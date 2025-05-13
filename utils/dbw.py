import aiosqlite
import asyncio
from typing import Any, Optional, Union
from datetime import datetime

class Database:
    def __init__(self, path: str, debug: bool = False):
        self.path = path
        self.conn: Optional[aiosqlite.Connection] = None
        self.lock = asyncio.Lock()
        self.debug = debug

    def _log(self, level: str, message: str):
        if not self.debug:
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = {
            "INFO": "\033[94m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "DEBUG": "\033[37m",
        }.get(level.upper(), "\033[0m")
        reset = "\033[0m"
        print(f"\033[90m{now} {color}{level.upper():<8}{reset} \033[96mdatabase\033[0m {message}")

    async def connect(self):
        if not self.conn:
            self.conn = await aiosqlite.connect(self.path)
            await self.conn.execute("PRAGMA foreign_keys = ON;")
            self.conn.row_factory = aiosqlite.Row
            self._log("INFO", f"Connected to database '{self.path}'")

    async def close(self):
        if self.conn:
            await self.conn.close()
            self._log("INFO", f"Closed connection to database '{self.path}'")
            self.conn = None

    async def rollback(self) -> None:
        if self.conn:
            await self.conn.rollback()
            self._log("WARNING", f"Transaction rollback issued")

    @property
    def in_transaction(self) -> bool:
        return self.conn.in_transaction if self.conn else False

    @property
    def _running(self) -> bool:
        return self.conn._running if self.conn else False

    @property
    def name(self) -> Optional[str]:
        return self.conn.name if self.conn else None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _dict_to_where_clause(self, where: dict[str, Any]) -> tuple[str, list[Any]]:
        if not where:
            return "", []
        clause = " AND ".join([f"{k} = ?" for k in where])
        return f"WHERE {clause}", list(where.values())

    async def insert(self, table: str, data: dict[str, Any]):
        async with self.lock:
            keys = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
            await self.conn.execute(sql, tuple(data.values()))
            await self.conn.commit()
            self._log("INFO", f"Inserted data into '{table}'")

    async def get(self, table: str, where: dict[str, Any] = {}) -> Optional[dict[str, Any]]:
        where_clause, values = self._dict_to_where_clause(where)
        sql = f"SELECT * FROM {table} {where_clause} LIMIT 1"
        self._log("DEBUG", f"Fetching single row from '{table}'")
        cursor = await self.conn.execute(sql, values)
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_all(self, table: str, where: dict[str, Any] = {}) -> list[dict[str, Any]]:
        where_clause, values = self._dict_to_where_clause(where)
        sql = f"SELECT * FROM {table} {where_clause}"
        self._log("DEBUG", f"Fetching all rows from '{table}'")
        cursor = await self.conn.execute(sql, values)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update(self, table: str, data: dict[str, Any], where: dict[str, Any]):
        async with self.lock:
            set_clause = ", ".join([f"{k} = ?" for k in data])
            where_clause, where_values = self._dict_to_where_clause(where)
            sql = f"UPDATE {table} SET {set_clause} {where_clause}"
            await self.conn.execute(sql, list(data.values()) + where_values)
            await self.conn.commit()
            self._log("INFO", f"Updated rows in '{table}'")

    async def delete(self, table: str, where: dict[str, Any]):
        async with self.lock:
            where_clause, values = self._dict_to_where_clause(where)
            sql = f"DELETE FROM {table} {where_clause}"
            await self.conn.execute(sql, values)
            await self.conn.commit()
            self._log("INFO", f"Deleted rows from '{table}'")
