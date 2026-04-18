"""§3 Device registry tools."""
from __future__ import annotations

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def list_device_registry() -> list:
        """§3 All devices in the registry."""
        return await ws().call("config/device_registry/list")

    @tool(mcp)
    async def get_device(device_id: str) -> dict:
        """§3 Get a device by id."""
        devs = await ws().call("config/device_registry/list")
        for d in devs:
            if d.get("id") == device_id:
                return d
        return {"error": "not_found"}

    @tool(mcp)
    async def update_device(device_id: str, patch: dict) -> dict:
        """§3 Update device. patch keys: name_by_user, area_id, disabled_by, labels."""
        return await ws().call("config/device_registry/update",
                               device_id=device_id, **patch)

    @tool(mcp)
    async def delete_device(device_id: str, config_entry_id: str) -> dict:
        """§3 Remove device from a config entry (effectively deletes if last entry)."""
        return await ws().call("config/device_registry/remove_config_entry",
                               device_id=device_id, config_entry_id=config_entry_id)

    @tool(mcp)
    async def merge_devices(src_device_id: str, dst_device_id: str) -> dict:
        """§3 Move all entities from src device to dst device, then delete src."""
        entries = await ws().call("config/entity_registry/list")
        moved = []
        for e in entries:
            if e.get("device_id") == src_device_id:
                await ws().call("config/entity_registry/update",
                                entity_id=e["entity_id"], device_id=dst_device_id)
                moved.append(e["entity_id"])
        # Try to nuke src device
        devs = await ws().call("config/device_registry/list")
        for d in devs:
            if d.get("id") == src_device_id:
                for ce in d.get("config_entries", []):
                    try:
                        await ws().call("config/device_registry/remove_config_entry",
                                        device_id=src_device_id, config_entry_id=ce)
                    except Exception:
                        pass
        return {"moved_entities": moved, "src": src_device_id, "dst": dst_device_id}

    return 5
