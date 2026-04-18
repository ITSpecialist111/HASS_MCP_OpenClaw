"""§23-24 Calendar / ToDo (full CRUD)."""
from __future__ import annotations

from typing import Any

from .. import hass
from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    # Calendar
    @tool(mcp)
    async def list_calendars() -> list:
        """§23 List calendar entities."""
        return await hass.get_calendars()

    @tool(mcp)
    async def create_event(entity_id: str, summary: str, start: str, end: str,
                            description: str | None = None,
                            location: str | None = None,
                            rrule: str | None = None) -> dict:
        """§23 Create a calendar event (with optional rrule)."""
        data: dict[str, Any] = {"entity_id": entity_id, "summary": summary,
                                 "start_date_time": start, "end_date_time": end}
        if description: data["description"] = description
        if location: data["location"] = location
        if rrule: data["rrule"] = rrule
        return await ws().call("call_service", domain="calendar",
                                service="create_event", service_data=data)

    @tool(mcp)
    async def update_event(entity_id: str, uid: str, **fields) -> dict:
        """§23 Update calendar event by uid."""
        data = {"entity_id": entity_id, "uid": uid, **fields}
        return await ws().call("call_service", domain="calendar",
                                service="update_event", service_data=data)

    @tool(mcp)
    async def delete_event(entity_id: str, uid: str,
                            recurrence_id: str | None = None,
                            recurrence_range: str | None = None) -> dict:
        """§23 Delete calendar event."""
        data: dict[str, Any] = {"entity_id": entity_id, "uid": uid}
        if recurrence_id: data["recurrence_id"] = recurrence_id
        if recurrence_range: data["recurrence_range"] = recurrence_range
        return await ws().call("call_service", domain="calendar",
                                service="delete_event", service_data=data)

    @tool(mcp)
    async def list_events_range(entity_id: str, start: str, end: str) -> Any:
        """§23 List calendar events in a time range."""
        return await ws().call("calendar/list_events", entity_id=entity_id,
                                start=start, end=end)

    # ToDo
    @tool(mcp)
    async def todo_clear_completed(entity_id: str) -> dict:
        """§24 Remove all completed todo items."""
        return await ws().call("call_service", domain="todo",
                                service="remove_completed_items",
                                service_data={"entity_id": entity_id})

    @tool(mcp)
    async def todo_move_item(entity_id: str, uid: str, previous_uid: str | None = None) -> dict:
        """§24 Reorder a todo item."""
        data: dict[str, Any] = {"entity_id": entity_id, "uid": uid}
        if previous_uid: data["previous_uid"] = previous_uid
        return await ws().call("call_service", domain="todo",
                                service="reorder_items", service_data=data)

    return 7
