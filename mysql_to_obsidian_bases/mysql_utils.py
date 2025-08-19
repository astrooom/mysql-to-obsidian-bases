from __future__ import annotations

import mysql.connector
from mysql.connector import connection
from typing import Any, Dict, List, Tuple


class MySQLClient:
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        port: int = 3306,
    ) -> None:
        self._host = host
        self._user = user
        self._password = password
        self._database = database
        self._port = port
        self._conn: connection.MySQLConnection | None = None

    def connect(self) -> None:
        self._conn = mysql.connector.connect(
            host=self._host,
            user=self._user,
            password=self._password,
            database=self._database,
            port=self._port,
            autocommit=False,
        )

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None

    def _ensure_conn(self) -> connection.MySQLConnection:
        if not self._conn:
            raise RuntimeError("Not connected")
        return self._conn

    def list_tables(self) -> List[str]:
        conn = self._ensure_conn()
        sql = (
            "SELECT TABLE_NAME FROM information_schema.tables "
            "WHERE table_schema = %s AND table_type = 'BASE TABLE' ORDER BY TABLE_NAME"
        )
        with conn.cursor() as cur:
            cur.execute(sql, (self._database,))
            rows = cur.fetchall()
        return [r[0] for r in rows]

    def fetch_all_rows(self, table: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        conn = self._ensure_conn()
        # Fetch column metadata from information_schema for robust type info
        col_meta_query = (
            "SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s ORDER BY ORDINAL_POSITION"
        )
        with conn.cursor(dictionary=True) as cur:
            cur.execute(col_meta_query, (self._database, table))
            cols_meta = cur.fetchall()

        if not cols_meta:
            raise ValueError(f"Table not found or has no columns: {self._database}.{table}")

        select_sql = f"SELECT * FROM `{table}`"
        with conn.cursor(dictionary=True) as cur:
            cur.execute(select_sql)
            rows = cur.fetchall()

        # Normalize metadata shape
        columns = [
            {
                "name": m["COLUMN_NAME"],
                "data_type": (m["DATA_TYPE"] or "").lower(),
                "column_type": (m["COLUMN_TYPE"] or "").lower(),
            }
            for m in cols_meta
        ]
        return rows, columns
