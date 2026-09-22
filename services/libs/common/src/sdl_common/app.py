import asyncio
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from sdl_common.logging import configure_logging
from sdl_common.settings import ServiceSettings

log = logging.getLogger("sdl.app")

# A readiness check is an async callable that raises (or times out) when a dependency is unhealthy.
ReadinessCheck = Callable[[], Awaitable[object]]
Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


def create_app(
    settings: ServiceSettings,
    *,
    title: str | None = None,
    lifespan: Lifespan | None = None,
    readiness: Sequence[tuple[str, ReadinessCheck]] | Callable[[], Sequence[tuple[str, ReadinessCheck]]] = (),
    readiness_timeout: float = 2.0,
) -> FastAPI:
    """Build a FastAPI app with the lab's standard plumbing.

    - GET /healthz  liveness: the process is up (never checks dependencies — a DB outage
                    must not restart pods)
    - GET /readyz   readiness: runs every check; 503 takes the pod out of the gateway's rotation
    - GET /metrics  Prometheus metrics (scraped via the chart's ServiceMonitor)
    - every response carries `X-Served-By: <pod>@<node>` so load balancing and failover are visible
    """
    configure_logging(settings.service_name, settings.pod_name, settings.log_level)

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
        log.info("starting", extra={"extra_fields": {"node": settings.node_name}})
        if lifespan is None:
            yield
        else:
            async with lifespan(app):
                yield
        log.info("stopped")

    app = FastAPI(title=title or settings.service_name, root_path=settings.root_path, lifespan=_lifespan)
    served_by = f"{settings.pod_name}@{settings.node_name}"

    @app.middleware("http")
    async def _served_by(request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        response.headers["X-Served-By"] = served_by
        if request.url.path not in ("/healthz", "/readyz", "/metrics"):
            log.info(
                "request",
                extra={
                    "extra_fields": {
                        "method": request.method,
                        "path": request.url.path,
                        "status": response.status_code,
                        "ms": round((time.perf_counter() - start) * 1000, 1),
                    }
                },
            )
        return response

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/readyz", include_in_schema=False)
    async def readyz() -> JSONResponse:
        checks = readiness() if callable(readiness) else readiness
        results: dict[str, str] = {}
        ok = True
        for name, check in checks:
            try:
                await asyncio.wait_for(check(), timeout=readiness_timeout)
                results[name] = "ok"
            except Exception as exc:  # noqa: BLE001 — any failure means not ready
                ok = False
                results[name] = f"fail: {type(exc).__name__}: {exc}"[:200]
        return JSONResponse(
            {"status": "ok" if ok else "fail", "checks": results}, status_code=200 if ok else 503
        )

    Instrumentator(excluded_handlers=["/healthz", "/readyz", "/metrics"]).instrument(app).expose(
        app, include_in_schema=False
    )
    return app


def run(app_path: str, settings: ServiceSettings) -> None:
    """Entry point for `python -m <module>`: uvicorn with graceful shutdown."""
    uvicorn.run(
        app_path,
        host="0.0.0.0",
        port=settings.port,
        proxy_headers=True,
        forwarded_allow_ips="*",
        timeout_graceful_shutdown=20,
        log_config=None,
    )
