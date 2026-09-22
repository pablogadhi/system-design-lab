"""Postgres via the `postgres-conn` connection contract (env: POSTGRES_URL, POSTGRES_READ_URL, ...).

from sdl_common.postgres import PostgresSettings, Database

db = Database(PostgresSettings())
async with db:                       # opens both pools (primary + replicas)
    async with db.primary.connection() as conn: ...
    async with db.replica.connection() as conn: ...   # may lag behind the primary
"""

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_", extra="ignore")

    url: str
    read_url: str | None = None  # replicas (ha profile); falls back to url
    pool_min: int = 1
    pool_max: int = 10


class Database:
    def __init__(self, settings: PostgresSettings):
        self.settings = settings
        kwargs = {"row_factory": dict_row}
        self.primary = AsyncConnectionPool(
            settings.url, min_size=settings.pool_min, max_size=settings.pool_max, kwargs=kwargs, open=False
        )
        self.replica = (
            AsyncConnectionPool(
                settings.read_url,
                min_size=settings.pool_min,
                max_size=settings.pool_max,
                kwargs=kwargs,
                open=False,
            )
            if settings.read_url
            else self.primary
        )

    async def __aenter__(self) -> "Database":
        # wait=False: the app starts even if the DB is down; /readyz reports it until it recovers
        await self.primary.open(wait=False)
        if self.replica is not self.primary:
            await self.replica.open(wait=False)
        return self

    async def __aexit__(self, *exc) -> None:
        if self.replica is not self.primary:
            await self.replica.close()
        await self.primary.close()

    async def check(self) -> None:
        """Readiness check: the primary answers a trivial query."""
        async with self.primary.connection(timeout=2) as conn:
            await conn.execute("SELECT 1")
