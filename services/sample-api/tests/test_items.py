"""Unit tests: no cluster, no database. The repo is swapped for an in-memory fake."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sample_api.main import app, get_repo
from sdl_common.contract import assert_implements_contract


class FakeRepo:
    def __init__(self):
        self.items: dict[int, dict] = {}

    async def create(self, name: str) -> dict:
        item = {"id": len(self.items) + 1, "name": name, "created_at": datetime.now(UTC)}
        self.items[item["id"]] = item
        return item

    async def get(self, item_id: int) -> dict | None:
        return self.items.get(item_id)

    async def list(self, limit: int, from_replica: bool) -> list[dict]:
        return sorted(self.items.values(), key=lambda i: -i["id"])[:limit]


@pytest.fixture
def client():
    repo = FakeRepo()
    app.dependency_overrides[get_repo] = lambda: repo
    yield TestClient(app)  # not used as a context manager -> lifespan (real DB) never runs
    app.dependency_overrides.clear()


def test_create_then_get(client):
    created = client.post("/items", json={"name": "hello"})
    assert created.status_code == 201
    item_id = created.json()["id"]
    got = client.get(f"/items/{item_id}")
    assert got.status_code == 200
    assert got.json()["name"] == "hello"
    assert "X-Served-By" in got.headers


def test_list_newest_first(client):
    for name in ("a", "b", "c"):
        client.post("/items", json={"name": name})
    assert [i["name"] for i in client.get("/items?limit=2").json()] == ["c", "b"]


def test_missing_item_is_404(client):
    assert client.get("/items/99999").status_code == 404


def test_validation(client):
    assert client.post("/items", json={"name": ""}).status_code == 422


def test_health_endpoints(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").status_code == 200  # no db opened -> no checks registered


def test_matches_contract():
    assert_implements_contract(app, "sample-api")
