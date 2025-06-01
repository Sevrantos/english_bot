import json
from typing import Optional, Union

import asyncpg
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey


class PGStorage(BaseStorage):
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def init_tables(self):
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS aiogram_states (
                    key TEXT PRIMARY KEY,
                    state TEXT
                );
            """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS aiogram_data (
                    key TEXT PRIMARY KEY,
                    data JSONB
                );
            """
            )

    async def set_state(
        self, key: StorageKey, state: Optional[Union[str, State]] = None
    ) -> None:
        state_value = state if isinstance(state, (str, type(None))) else state.state
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO aiogram_states(key, state)
                VALUES($1, $2)
                ON CONFLICT (key)
                DO UPDATE SET state = EXCLUDED.state;
            """,
                str(key),
                state_value,
            )

    async def get_state(self, key: StorageKey) -> Optional[str]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT state FROM aiogram_states WHERE key = $1;", str(key)
            )
            return row["state"] if row else None

    async def set_data(self, key: StorageKey, data: dict) -> None:
        data_json = json.dumps(data)
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO aiogram_data(key, data)
                VALUES($1, $2::jsonb)
                ON CONFLICT (key)
                DO UPDATE SET data = EXCLUDED.data;
            """,
                str(key),
                data_json,
            )

    async def get_data(self, key: StorageKey) -> dict:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT data FROM aiogram_data WHERE key = $1;", str(key)
            )
            return json.loads(row["data"]) if row else {}

    async def update_data(self, key: StorageKey, data: dict) -> dict:
        current = await self.get_data(key)
        current.update(data)
        await self.set_data(key, current)
        return current

    async def close(self) -> None:
        # If you want PGStorage to handle closing, you can call pool.close()
        # Otherwise, manage your pool lifecycle externally.
        await self._pool.close()
