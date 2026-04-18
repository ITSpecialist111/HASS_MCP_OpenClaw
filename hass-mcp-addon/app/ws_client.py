"""Persistent Home Assistant WebSocket client.

Auto-reconnect, monotonic message-ID counter, future-keyed pending-response
map for concurrent calls, and a subscription manager.
"""
from __future__ import annotations

import asyncio
import itertools
import json
import logging
import os
from typing import Any, Awaitable, Callable

import websockets

logger = logging.getLogger(__name__)

WS_URL = os.environ.get("HA_WS_URL", "ws://supervisor/core/websocket")
TOKEN = os.environ.get("SUPERVISOR_TOKEN", "") or os.environ.get("HA_TOKEN", "")


class HAWebSocket:
    def __init__(self, url: str = WS_URL, token: str = TOKEN):
        self.url = url
        self.token = token
        self._ws: Any = None
        self._ids = itertools.count(1)
        self._pending: dict[int, asyncio.Future] = {}
        self._subscriptions: dict[int, Callable[[dict], Awaitable[None] | None]] = {}
        self._lock = asyncio.Lock()
        self._reader_task: asyncio.Task | None = None
        self._connected = asyncio.Event()

    async def connect(self) -> None:
        async with self._lock:
            if self._ws is not None and not getattr(self._ws, "closed", True):
                return
            backoff = 1.0
            while True:
                try:
                    self._ws = await websockets.connect(
                        self.url, max_size=64 * 1024 * 1024, ping_interval=30
                    )
                    auth_required = json.loads(await self._ws.recv())
                    if auth_required.get("type") == "auth_required":
                        await self._ws.send(json.dumps({"type": "auth", "access_token": self.token}))
                        auth_resp = json.loads(await self._ws.recv())
                        if auth_resp.get("type") != "auth_ok":
                            raise RuntimeError(f"WS auth failed: {auth_resp}")
                    logger.info("WS connected to %s", self.url)
                    self._connected.set()
                    self._reader_task = asyncio.create_task(self._reader())
                    return
                except Exception as e:
                    logger.warning("WS connect failed: %s; retrying in %.1fs", e, backoff)
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 30.0)

    async def _reader(self) -> None:
        try:
            async for raw in self._ws:
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                mid = msg.get("id")
                mtype = msg.get("type")
                if mtype == "event" and mid in self._subscriptions:
                    cb = self._subscriptions[mid]
                    try:
                        res = cb(msg)
                        if asyncio.iscoroutine(res):
                            asyncio.create_task(res)
                    except Exception:
                        logger.exception("subscription callback error")
                    continue
                if mid in self._pending:
                    fut = self._pending.pop(mid)
                    if not fut.done():
                        fut.set_result(msg)
        except Exception as e:
            logger.warning("WS reader exited: %s", e)
        finally:
            self._connected.clear()
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(ConnectionError("WS closed"))
            self._pending.clear()
            self._ws = None
            # Auto-reconnect
            asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        await asyncio.sleep(2)
        try:
            await self.connect()
        except Exception:
            logger.exception("reconnect failed")

    async def send(self, message: dict, timeout: float = 30.0) -> dict:
        await self.connect()
        mid = next(self._ids)
        message = {**message, "id": mid}
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[mid] = fut
        await self._ws.send(json.dumps(message))
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(mid, None)
            raise

    async def call(self, type_: str, **kwargs) -> Any:
        """Send a typed command and return the `result` field (or raise)."""
        resp = await self.send({"type": type_, **kwargs})
        if not resp.get("success", True):
            err = resp.get("error", {})
            raise RuntimeError(f"{err.get('code', 'err')}: {err.get('message', resp)}")
        return resp.get("result")

    async def subscribe(self, type_: str, callback: Callable, **kwargs) -> int:
        await self.connect()
        mid = next(self._ids)
        self._subscriptions[mid] = callback
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[mid] = fut
        await self._ws.send(json.dumps({"id": mid, "type": type_, **kwargs}))
        resp = await asyncio.wait_for(fut, timeout=15.0)
        if not resp.get("success", True):
            self._subscriptions.pop(mid, None)
            raise RuntimeError(resp.get("error", resp))
        return mid

    async def unsubscribe(self, sub_id: int) -> None:
        self._subscriptions.pop(sub_id, None)
        try:
            await self.call("unsubscribe_events", subscription=sub_id)
        except Exception:
            pass


_singleton: HAWebSocket | None = None


def get_ws() -> HAWebSocket:
    global _singleton
    if _singleton is None:
        _singleton = HAWebSocket()
    return _singleton
