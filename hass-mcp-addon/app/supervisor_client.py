"""Persistent Supervisor REST client."""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SUPERVISOR_URL = os.environ.get("SUPERVISOR_URL", "http://supervisor")
TOKEN = os.environ.get("SUPERVISOR_TOKEN", "") or os.environ.get("HA_TOKEN", "")
TIMEOUT = 60.0


def _h(extra: dict | None = None) -> dict[str, str]:
    h = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    return h


def _unwrap(data: Any) -> Any:
    if isinstance(data, dict) and "data" in data and "result" in data:
        return data["data"]
    return data


async def get(path: str, *, raw: bool = False, headers: dict | None = None) -> Any:
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.get(f"{SUPERVISOR_URL}{path}", headers=_h(headers))
        r.raise_for_status()
        if raw:
            return r.text
        try:
            return _unwrap(r.json())
        except Exception:
            return r.text


async def post(path: str, json: dict | None = None, *, raw: bool = False) -> Any:
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.post(f"{SUPERVISOR_URL}{path}", headers=_h(), json=json or {})
        r.raise_for_status()
        if raw:
            return r.text
        try:
            return _unwrap(r.json())
        except Exception:
            return r.text


async def delete(path: str) -> Any:
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.delete(f"{SUPERVISOR_URL}{path}", headers=_h())
        r.raise_for_status()
        try:
            return _unwrap(r.json())
        except Exception:
            return r.text


async def request(method: str, path: str, *, json: dict | None = None,
                  params: dict | None = None, raw: bool = False) -> Any:
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.request(method.upper(), f"{SUPERVISOR_URL}{path}",
                            headers=_h(), json=json, params=params)
        r.raise_for_status()
        if raw:
            return r.text
        try:
            return _unwrap(r.json())
        except Exception:
            return r.text


async def logs(path: str, lines: int = 200) -> str:
    text = await get(path, raw=True, headers={"Accept": "text/plain"})
    if isinstance(text, str):
        rows = text.strip().splitlines()
        return "\n".join(rows[-lines:])
    return str(text)
