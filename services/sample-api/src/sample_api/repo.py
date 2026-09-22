from typing import Protocol

from sdl_common.postgres import Database


class ItemsRepo(Protocol):
    async def create(self, name: str) -> dict: ...
    async def get(self, item_id: int) -> dict | None: ...
    async def list(self, limit: int, from_replica: bool) -> list[dict]: ...


class PostgresItemsRepo:
    def __init__(self, db: Database):
        self.db = db

    async def create(self, name: str) -> dict:
        async with self.db.primary.connection() as conn:
            cur = await conn.execute(
                "INSERT INTO items(name) VALUES (%s) RETURNING id, name, created_at", (name,)
            )
            return await cur.fetchone()

    async def get(self, item_id: int) -> dict | None:
        async with self.db.primary.connection() as conn:
            cur = await conn.execute("SELECT id, name, created_at FROM items WHERE id = %s", (item_id,))
            return await cur.fetchone()

    async def list(self, limit: int, from_replica: bool) -> list[dict]:
        pool = self.db.replica if from_replica else self.db.primary
        async with pool.connection() as conn:
            cur = await conn.execute(
                "SELECT id, name, created_at FROM items ORDER BY id DESC LIMIT %s", (limit,)
            )
            return await cur.fetchall()
