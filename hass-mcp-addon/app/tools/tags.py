"""§22 Tags / NFC."""
from __future__ import annotations

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def list_tags() -> list:
        """§22 List all NFC/QR tags."""
        return await ws().call("tag/list")

    @tool(mcp)
    async def create_tag(tag_id: str, name: str | None = None) -> dict:
        """§22 Create a tag."""
        kwargs = {"tag_id": tag_id}
        if name: kwargs["name"] = name
        return await ws().call("tag/create", **kwargs)

    @tool(mcp)
    async def update_tag(tag_id: str, patch: dict) -> dict:
        """§22 Update tag."""
        return await ws().call("tag/update", tag_id=tag_id, **patch)

    @tool(mcp)
    async def delete_tag(tag_id: str) -> dict:
        """§22 Delete tag."""
        return await ws().call("tag/delete", tag_id=tag_id)

    @tool(mcp)
    async def scan_tag(tag_id: str, device_id: str | None = None) -> dict:
        """§22 Fire tag_scanned event."""
        data = {"tag_id": tag_id}
        if device_id: data["device_id"] = device_id
        return await ws().call("fire_event", event_type="tag_scanned",
                                event_data=data)

    return 5
