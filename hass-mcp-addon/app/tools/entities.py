"""§2 Entity registry tools (WebSocket)."""
from __future__ import annotations

from typing import Any

from ..ws_client import get_ws
from ._helpers import tool

REGISTRY_FIELDS = ["name", "icon", "area_id", "device_class", "unit_of_measurement",
                   "disabled_by", "hidden_by", "entity_category", "aliases",
                   "labels", "options", "new_entity_id"]


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def list_entity_registry() -> list:
        """§2 All entity registry entries (incl. disabled/hidden)."""
        return await ws().call("config/entity_registry/list")

    @tool(mcp)
    async def get_entity_registry_entry(entity_id: str) -> dict:
        """§2 Full registry record for one entity."""
        return await ws().call("config/entity_registry/get", entity_id=entity_id)

    @tool(mcp)
    async def update_entity(entity_id: str, patch: dict) -> dict:
        """§2 Update entity registry entry. patch keys: name, icon, area_id,
        device_class, unit_of_measurement, disabled_by, hidden_by, entity_category,
        aliases, labels, options, new_entity_id (rename)."""
        return await ws().call("config/entity_registry/update",
                               entity_id=entity_id, **patch)

    @tool(mcp)
    async def delete_entity(entity_id: str) -> dict:
        """§2 Hard-delete an entity from the registry."""
        return await ws().call("config/entity_registry/remove", entity_id=entity_id)

    @tool(mcp)
    async def bulk_delete_entities(entity_ids: list[str]) -> list:
        """§2 Delete a list of entities."""
        out = []
        for eid in entity_ids:
            try:
                await ws().call("config/entity_registry/remove", entity_id=eid)
                out.append({"entity_id": eid, "ok": True})
            except Exception as e:
                out.append({"entity_id": eid, "error": str(e)})
        return out

    @tool(mcp)
    async def bulk_update_entities(updates: list[dict]) -> list:
        """§2 Bulk update; updates = [{entity_id, patch}, ...]."""
        out = []
        for u in updates:
            eid = u["entity_id"]; patch = u.get("patch", {})
            try:
                r = await ws().call("config/entity_registry/update",
                                    entity_id=eid, **patch)
                out.append({"entity_id": eid, "ok": True, "result": r})
            except Exception as e:
                out.append({"entity_id": eid, "error": str(e)})
        return out

    @tool(mcp)
    async def enable_entity(entity_id: str) -> dict:
        """§2 Enable a disabled entity."""
        return await ws().call("config/entity_registry/update",
                               entity_id=entity_id, disabled_by=None)

    @tool(mcp)
    async def disable_entity(entity_id: str, by: str = "user") -> dict:
        """§2 Disable an entity (disabled_by='user')."""
        return await ws().call("config/entity_registry/update",
                               entity_id=entity_id, disabled_by=by)

    @tool(mcp)
    async def hide_entity(entity_id: str) -> dict:
        """§2 Hide an entity from the dashboard."""
        return await ws().call("config/entity_registry/update",
                               entity_id=entity_id, hidden_by="user")

    @tool(mcp)
    async def unhide_entity(entity_id: str) -> dict:
        """§2 Unhide an entity."""
        return await ws().call("config/entity_registry/update",
                               entity_id=entity_id, hidden_by=None)

    @tool(mcp)
    async def rename_entity(entity_id: str, new_entity_id: str) -> dict:
        """§2 Rename an entity (changes entity_id)."""
        return await ws().call("config/entity_registry/update",
                               entity_id=entity_id, new_entity_id=new_entity_id)

    @tool(mcp)
    async def move_entity_to_area(entity_id: str, area_id: str | None) -> dict:
        """§2 Move entity to a different area (None to unassign)."""
        return await ws().call("config/entity_registry/update",
                               entity_id=entity_id, area_id=area_id)

    @tool(mcp)
    async def purge_orphaned_entities(integration: str | None = None,
                                       only_unavailable: bool = True) -> dict:
        """§2 Delete entities that are restored/unavailable, optionally filtered by integration."""
        entries = await ws().call("config/entity_registry/list")
        from .. import hass
        states = await hass.get_all_states()
        state_map = {s["entity_id"]: s.get("state") for s in states}
        to_remove = []
        for e in entries:
            if integration and e.get("platform") != integration:
                continue
            st = state_map.get(e["entity_id"])
            if only_unavailable and st not in (None, "unavailable", "unknown"):
                continue
            to_remove.append(e["entity_id"])
        results = []
        for eid in to_remove:
            try:
                await ws().call("config/entity_registry/remove", entity_id=eid)
                results.append(eid)
            except Exception:
                pass
        return {"removed": results, "count": len(results)}

    return 13
