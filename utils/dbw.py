import aiosqlite
from typing import Any, Optional, Union

class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        if not self.conn:
            self.conn = await aiosqlite.connect(self.path)
            await self.conn.execute("PRAGMA foreign_keys = ON;")
            self.conn.row_factory = aiosqlite.Row

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None

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
        keys = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        await self.conn.execute(sql, tuple(data.values()))
        await self.conn.commit()

    async def get(self, table: str, where: dict[str, Any] = {}) -> Optional[dict[str, Any]]:
        where_clause, values = self._dict_to_where_clause(where)
        sql = f"SELECT * FROM {table} {where_clause} LIMIT 1"
        cursor = await self.conn.execute(sql, values)
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_all(self, table: str, where: dict[str, Any] = {}) -> list[dict[str, Any]]:
        where_clause, values = self._dict_to_where_clause(where)
        sql = f"SELECT * FROM {table} {where_clause}"
        cursor = await self.conn.execute(sql, values)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update(self, table: str, data: dict[str, Any], where: dict[str, Any]):
        set_clause = ", ".join([f"{k} = ?" for k in data])
        where_clause, where_values = self._dict_to_where_clause(where)
        sql = f"UPDATE {table} SET {set_clause} {where_clause}"
        await self.conn.execute(sql, list(data.values()) + where_values)
        await self.conn.commit()

    async def delete(self, table: str, where: dict[str, Any]):
        where_clause, values = self._dict_to_where_clause(where)
        sql = f"DELETE FROM {table} {where_clause}"
        await self.conn.execute(sql, values)
        await self.conn.commit()
