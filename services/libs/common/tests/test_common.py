import asyncio

from fastapi.testclient import TestClient
from sdl_common import ServiceSettings, create_app
from sdl_common.contract import operations


def make_app(checks):
    settings = ServiceSettings(service_name="t", pod_name="p1", node_name="n1")
    return create_app(settings, readiness=checks, readiness_timeout=0.2)


def test_healthz_and_served_by():
    res = TestClient(make_app([])).get("/healthz")
    assert res.json() == {"status": "ok"}
    assert res.headers["X-Served-By"] == "p1@n1"


def test_readyz_reports_failing_and_slow_checks():
    async def ok():
        return None

    async def broken():
        raise ConnectionError("db down")

    async def slow():
        await asyncio.sleep(1)

    res = TestClient(make_app([("a", ok), ("b", broken), ("c", slow)])).get("/readyz")
    assert res.status_code == 503
    checks = res.json()["checks"]
    assert checks["a"] == "ok"
    assert "db down" in checks["b"]
    assert checks["c"].startswith("fail: TimeoutError")


def test_readyz_accepts_lazy_check_factory():
    res = TestClient(make_app(lambda: [])).get("/readyz")
    assert res.status_code == 200


def test_metrics_exposed():
    client = TestClient(make_app([]))
    client.get("/healthz")
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "http_request" in res.text


def test_contract_operations_parsing():
    spec = {"paths": {"/x": {"get": {"responses": {"200": {}}}, "parameters": []}}}
    assert operations(spec) == {("GET", "/x"): {"200"}}
