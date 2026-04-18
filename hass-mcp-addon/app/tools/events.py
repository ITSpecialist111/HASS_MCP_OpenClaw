"""§13 Events / bus."""
from __future__ import annotations

import asyncio

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def fire_event_full(event_type: str, event_data: dict | None = None) -> dict:
        """§13 Fire any event on the HA event bus."""
        return await ws().call("fire_event", event_type=event_type,
                                event_data=event_data or {})

    @tool(mcp)
    async def subscribe_events(event_type: str | None = None,
                                duration: float = 10.0,
                                max_events: int = 200) -> dict:
        """§13 Subscribe to events for `duration` seconds, return captured list."""
        captured: list = []
        loop = asyncio.get_running_loop()
        done = loop.create_future()

        def on_event(msg):
            captured.append(msg.get("event"))
            if len(captured) >= max_events and not done.done():
                done.set_result(True)

        kwargs = {"event_type": event_type} if event_type else {}
        sub_id = await ws().subscribe("subscribe_events", on_event, **kwargs)
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
        return {"event_type": event_type, "captured": captured, "count": len(captured)}

    @tool(mcp)
    async def subscribe_trigger(trigger: dict, duration: float = 30.0,
                                 max_events: int = 100) -> dict:
        """§13 Subscribe to a trigger definition for `duration` seconds."""
        captured: list = []
        done = asyncio.get_running_loop().create_future()

        def on_event(msg):
            captured.append(msg.get("event"))
            if len(captured) >= max_events and not done.done():
                done.set_result(True)

        sub_id = await ws().subscribe("subscribe_trigger", on_event, trigger=trigger)
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
        return {"trigger": trigger, "captured": captured, "count": len(captured)}

    @tool(mcp)
    async def list_event_types() -> list:
        """§13 Common HA event types reference list."""
        return [
            "state_changed", "call_service", "service_registered",
            "service_removed", "component_loaded", "homeassistant_start",
            "homeassistant_started", "homeassistant_stop", "homeassistant_final_write",
            "automation_triggered", "automation_reloaded",
            "script_started", "scene_reloaded",
            "logbook_entry", "panel_custom",
            "user_added", "user_removed", "user_updated",
            "tag_scanned", "zha_event", "deconz_event", "esphome.button_pressed",
            "mobile_app_notification_action", "mobile_app_notification_received",
            "ios.notification_action_fired", "alexa_smart_home", "google_assistant_command",
            "config_entry_discovered", "device_registry_updated",
            "entity_registry_updated", "area_registry_updated",
        ]

    return 4
