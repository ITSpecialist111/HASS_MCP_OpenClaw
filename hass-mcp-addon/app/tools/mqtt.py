"""§15 MQTT (publish, subscribe, dump, discovery wipe)."""
from __future__ import annotations

import asyncio
from typing import Any

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def mqtt_publish(topic: str, payload: str = "", qos: int = 0,
                            retain: bool = False) -> dict:
        """§15 Publish to MQTT (full options)."""
        return await ws().call("call_service", domain="mqtt", service="publish",
                                service_data={"topic": topic, "payload": payload,
                                              "qos": qos, "retain": retain})

    @tool(mcp)
    async def mqtt_subscribe(topic: str, duration: float = 10.0,
                              max_msgs: int = 200) -> dict:
        """§15 Subscribe to a topic for `duration` seconds, return messages."""
        captured: list = []
        done = asyncio.get_running_loop().create_future()

        def on_msg(m):
            evt = m.get("event") or m
            captured.append(evt)
            if len(captured) >= max_msgs and not done.done():
                done.set_result(True)

        sub_id = await ws().subscribe("mqtt/subscribe", on_msg, topic=topic)
        try:
            try:
                await asyncio.wait_for(done, timeout=duration)
            except asyncio.TimeoutError:
                pass
        finally:
            try:
                await ws().unsubscribe(sub_id)
            except Exception:
                pass
        return {"topic": topic, "messages": captured, "count": len(captured)}

    @tool(mcp)
    async def mqtt_dump(topic_root: str = "homeassistant/#",
                         duration: float = 5.0) -> dict:
        """§15 Snapshot retained messages from a topic root."""
        return await mqtt_subscribe(topic_root, duration=duration, max_msgs=5000)

    @tool(mcp)
    async def mqtt_remove_discovery(topic: str) -> dict:
        """§15 Clear a retained MQTT discovery topic by publishing empty retained payload."""
        return await ws().call("call_service", domain="mqtt", service="publish",
                                service_data={"topic": topic, "payload": "", "retain": True})

    @tool(mcp)
    async def mqtt_info() -> Any:
        """§15 MQTT broker info (handler)."""
        return await ws().call("mqtt/device/debug_info")

    return 5
