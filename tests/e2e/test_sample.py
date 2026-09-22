"""Acceptance flows for the sample design (design/spec.md -> "Acceptance flows")."""

import uuid

from conftest import eventually


def test_create_and_read_item(http):
    name = f"e2e-{uuid.uuid4().hex[:8]}"
    created = http.post("/api/sample-api/items", json={"name": name})
    assert created.status_code == 201, created.text
    item = created.json()

    got = http.get(f"/api/sample-api/items/{item['id']}")
    assert got.status_code == 200
    assert got.json()["name"] == name


def test_write_is_eventually_visible_on_replica(http):
    name = f"e2e-replica-{uuid.uuid4().hex[:8]}"
    http.post("/api/sample-api/items", json={"name": name}).raise_for_status()

    def visible():
        names = [i["name"] for i in http.get("/api/sample-api/items?source=replica&limit=100").json()]
        assert name in names

    eventually(visible, timeout=15)


def test_requests_are_load_balanced(http):
    served_by = {http.get("/api/sample-api/items?limit=1").headers["x-served-by"] for _ in range(30)}
    assert len(served_by) >= 2, f"expected several replicas to answer, got {served_by}"


def test_unknown_item_is_404(http):
    assert http.get("/api/sample-api/items/999999999").status_code == 404


def test_client_is_served(http):
    res = http.get("/")
    assert res.status_code == 200
    assert "System Design Lab" in res.text
