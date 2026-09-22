"""sample-api — implements design/contracts/openapi/sample-api.yaml.

Writes go to the Postgres primary. `GET /items?source=replica` reads from a streaming replica, which
makes replication lag observable (write, then immediately list from the replica).
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sdl_common import ServiceSettings, create_app
from sdl_common.postgres import Database, PostgresSettings

from sample_api.repo import ItemsRepo, PostgresItemsRepo

settings = ServiceSettings(service_name="sample-api")


class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class Item(BaseModel):
    id: int
    name: str
    created_at: datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with Database(PostgresSettings()) as db:
        app.state.db = db
        app.state.repo = PostgresItemsRepo(db)
        yield


def readiness():
    db: Database | None = getattr(app.state, "db", None)
    return [("postgres", db.check)] if db else []


app = create_app(settings, title="sample-api", lifespan=lifespan, readiness=readiness)


def get_repo(request: Request) -> ItemsRepo:
    return request.app.state.repo


Repo = Annotated[ItemsRepo, Depends(get_repo)]


@app.post("/items", status_code=201, response_model=Item)
async def create_item(body: ItemIn, repo: Repo) -> dict:
    return await repo.create(body.name)


@app.get("/items", response_model=list[Item])
async def list_items(
    repo: Repo,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    source: Literal["primary", "replica"] = "primary",
) -> list[dict]:
    return await repo.list(limit, from_replica=source == "replica")


@app.get("/items/{item_id}", response_model=Item, responses={404: {"description": "Item not found"}})
async def get_item(item_id: int, repo: Repo) -> dict:
    item = await repo.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    return item
