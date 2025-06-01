import asyncpg


class Database:
    def __init__(self, dsn: str):
        self.pool: asyncpg.Pool | None = None
        self.dsn = dsn

    async def connect(self):
        self.pool = await asyncpg.create_pool(dsn=self.dsn, min_size=5, max_size=10)

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
