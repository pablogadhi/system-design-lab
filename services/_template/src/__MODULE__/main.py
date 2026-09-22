"""__SERVICE__ — implements design/contracts/openapi/__SERVICE__.yaml.

Patterns (see services/sample-api for a complete example):
- dependencies come from connection contracts: add the component to `connections:` in
  deploy/values.yaml and read its env vars (e.g. POSTGRES_URL) via a pydantic-settings class
- open clients in `lifespan`, store them on app.state, register readiness checks
- keep I/O behind a small repo/client class so unit tests can swap in a fake via dependency_overrides
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sdl_common import ServiceSettings, create_app

settings = ServiceSettings(service_name="__SERVICE__")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # open connections/pools here, e.g. `async with Database(PostgresSettings()) as db: app.state.db = db`
    yield


def readiness():
    # return [("postgres", app.state.db.check)] once dependencies exist
    return []


app = create_app(settings, title="__SERVICE__", lifespan=lifespan, readiness=readiness)


@app.get("/hello")
async def hello() -> dict:
    return {"service": settings.service_name, "pod": settings.pod_name}
