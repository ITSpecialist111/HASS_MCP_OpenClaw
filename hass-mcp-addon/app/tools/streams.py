"""§40 Streaming subscriptions."""
from __future__ import annotations

import asyncio
import itertools
from typing import Any

from ..ws_client import get_ws
from ._helpers import tool


_STREAMS: dict[str, dict[str, Any]] = {}
_ids = itertools.count(1)


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def start_stream(event_type: str | None = None,
                            trigger: dict | None = None,
                            buffer_size: int = 500) -> dict:
        """§40 Start a buffered subscription. Returns stream_id; use read_stream/stop_stream."""
        stream_id = f"s{next(_ids)}"
        buf: list = []

        def on_evt(msg):
            buf.append(msg.get("event") or msg)
            if len(buf) > buffer_size:
                del buf[0:len(buf) - buffer_size]

        if trigger:
            sub_id = await ws().subscribe("subscribe_trigger", on_evt, trigger=trigger)
        else:
            kwargs = {"event_type": event_type} if event_type else {}
            sub_id = await ws().subscribe("subscribe_events", on_evt, **kwargs)

        _STREAMS[stream_id] = {"sub_id": sub_id, "buffer": buf,
                                "kind": "trigger" if trigger else "event",
                                "filter": trigger or event_type}
        return {"stream_id": stream_id}

    @tool(mcp)
    async def read_stream(stream_id: str, drain: bool = True) -> dict:
        """§40 Read buffered events for a stream."""
        s = _STREAMS.get(stream_id)
        if not s:
            return {"error": "unknown stream_id"}
        events = list(s["buffer"])
        if drain:
            s["buffer"].clear()
        return {"stream_id": stream_id, "count": len(events), "events": events}

    @tool(mcp)
    async def stop_stream(stream_id: str) -> dict:
        """§40 Stop and remove a stream."""
        s = _STREAMS.pop(stream_id, None)
        if not s: return {"error": "unknown stream_id"}
        try:
            await ws().unsubscribe(s["sub_id"])
        except Exception:
            pass
        return {"stopped": stream_id}

    @tool(mcp)
    async def list_streams() -> list:
        """§40 List active streams."""
        return [{"stream_id": k, "kind": v["kind"], "filter": v["filter"],
                  "buffered": len(v["buffer"])} for k, v in _STREAMS.items()]

    return 4
