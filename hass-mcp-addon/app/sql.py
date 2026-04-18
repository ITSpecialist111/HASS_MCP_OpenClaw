"""Recorder DB direct access (SQLite by default; configurable URL)."""
from __future__ import annotations

import os
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DB_URL = os.environ.get("RECORDER_URL", "")
DB_PATH = os.environ.get("RECORDER_DB", "/config/home-assistant_v2.db")


def _engine() -> Engine:
    url = DB_URL or f"sqlite:///{DB_PATH}"
    return create_engine(url, future=True)


def query(sql: str, params: dict | None = None, limit: int = 1000) -> dict[str, Any]:
    eng = _engine()
    with eng.connect() as conn:
        rs = conn.execute(text(sql), params or {})
        rows = []
        for i, row in enumerate(rs):
            if i >= limit:
                break
            rows.append(dict(row._mapping))
        return {"rows": rows, "count": len(rows)}


def execute(sql: str, params: dict | None = None) -> dict[str, Any]:
    eng = _engine()
    with eng.begin() as conn:
        rs = conn.execute(text(sql), params or {})
        return {"rowcount": rs.rowcount}


def schema() -> dict[str, Any]:
    eng = _engine()
    out: dict[str, list] = {}
    with eng.connect() as conn:
        if eng.url.get_backend_name() == "sqlite":
            tbls = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            for (name,) in tbls:
                cols = conn.execute(text(f"PRAGMA table_info({name})")).fetchall()
                out[name] = [{"name": c[1], "type": c[2]} for c in cols]
        else:
            tbls = conn.execute(text("SELECT table_name FROM information_schema.tables")).fetchall()
            for (name,) in tbls:
                out[name] = []
    return out


def vacuum() -> dict[str, Any]:
    eng = _engine()
    with eng.connect() as conn:
        if eng.url.get_backend_name() == "sqlite":
            conn.exec_driver_sql("VACUUM")
            return {"ok": True}
        return {"ok": False, "error": "VACUUM only supported on sqlite"}


def db_size() -> dict[str, Any]:
    if os.path.exists(DB_PATH):
        return {"path": DB_PATH, "bytes": os.path.getsize(DB_PATH)}
    return {"path": DB_PATH, "bytes": 0, "missing": True}
