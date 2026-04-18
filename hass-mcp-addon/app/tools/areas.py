"""§5 Areas / Floors / Labels / Categories / Zones."""
from __future__ import annotations

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    # ---- Areas ----
    @tool(mcp)
    async def list_areas_full() -> list:
        """§5.1 List all areas with full registry data."""
        return await ws().call("config/area_registry/list")

    @tool(mcp)
    async def create_area(name: str, **fields) -> dict:
        """§5.1 Create an area. Optional: floor_id, picture, icon, aliases, labels."""
        return await ws().call("config/area_registry/create", name=name, **fields)

    @tool(mcp)
    async def update_area(area_id: str, patch: dict) -> dict:
        """§5.1 Update area. Keys: name, floor_id, icon, picture, aliases, labels."""
        return await ws().call("config/area_registry/update", area_id=area_id, **patch)

    @tool(mcp)
    async def delete_area(area_id: str) -> dict:
        """§5.1 Delete an area."""
        return await ws().call("config/area_registry/delete", area_id=area_id)

    @tool(mcp)
    async def merge_areas(src_area_id: str, dst_area_id: str) -> dict:
        """§5.1 Reassign all entities and devices from src to dst, then delete src."""
        ents = await ws().call("config/entity_registry/list")
        devs = await ws().call("config/device_registry/list")
        moved_e, moved_d = [], []
        for e in ents:
            if e.get("area_id") == src_area_id:
                await ws().call("config/entity_registry/update",
                                entity_id=e["entity_id"], area_id=dst_area_id)
                moved_e.append(e["entity_id"])
        for d in devs:
            if d.get("area_id") == src_area_id:
                await ws().call("config/device_registry/update",
                                device_id=d["id"], area_id=dst_area_id)
                moved_d.append(d["id"])
        await ws().call("config/area_registry/delete", area_id=src_area_id)
        return {"entities_moved": moved_e, "devices_moved": moved_d}

    # ---- Floors ----
    @tool(mcp)
    async def list_floors_full() -> list:
        """§5.2 List all floors."""
        return await ws().call("config/floor_registry/list")

    @tool(mcp)
    async def create_floor(name: str, **fields) -> dict:
        """§5.2 Create a floor."""
        return await ws().call("config/floor_registry/create", name=name, **fields)

    @tool(mcp)
    async def update_floor(floor_id: str, patch: dict) -> dict:
        """§5.2 Update floor."""
        return await ws().call("config/floor_registry/update", floor_id=floor_id, **patch)

    @tool(mcp)
    async def delete_floor(floor_id: str) -> dict:
        """§5.2 Delete a floor."""
        return await ws().call("config/floor_registry/delete", floor_id=floor_id)

    # ---- Labels ----
    @tool(mcp)
    async def list_labels_full() -> list:
        """§5.3 List all labels."""
        return await ws().call("config/label_registry/list")

    @tool(mcp)
    async def create_label(name: str, **fields) -> dict:
        """§5.3 Create a label. Optional: color, icon, description."""
        return await ws().call("config/label_registry/create", name=name, **fields)

    @tool(mcp)
    async def update_label(label_id: str, patch: dict) -> dict:
        """§5.3 Update label."""
        return await ws().call("config/label_registry/update", label_id=label_id, **patch)

    @tool(mcp)
    async def delete_label(label_id: str) -> dict:
        """§5.3 Delete a label."""
        return await ws().call("config/label_registry/delete", label_id=label_id)

    @tool(mcp)
    async def assign_label_to_entity(entity_id: str, label_id: str) -> dict:
        """§5.3 Add a label to an entity."""
        cur = await ws().call("config/entity_registry/get", entity_id=entity_id)
        labels = list(cur.get("entity_entry", cur).get("labels", []) or [])
        if label_id not in labels:
            labels.append(label_id)
        return await ws().call("config/entity_registry/update",
                               entity_id=entity_id, labels=labels)

    @tool(mcp)
    async def remove_label_from_entity(entity_id: str, label_id: str) -> dict:
        """§5.3 Remove a label from an entity."""
        cur = await ws().call("config/entity_registry/get", entity_id=entity_id)
        labels = [l for l in (cur.get("entity_entry", cur).get("labels", []) or [])
                  if l != label_id]
        return await ws().call("config/entity_registry/update",
                               entity_id=entity_id, labels=labels)

    # ---- Categories ----
    @tool(mcp)
    async def list_categories(scope: str = "automation") -> list:
        """§5.4 List categories for a scope."""
        return await ws().call("config/category_registry/list", scope=scope)

    @tool(mcp)
    async def create_category(scope: str, name: str, icon: str | None = None) -> dict:
        """§5.4 Create a category."""
        kwargs = {"scope": scope, "name": name}
        if icon: kwargs["icon"] = icon
        return await ws().call("config/category_registry/create", **kwargs)

    @tool(mcp)
    async def delete_category(scope: str, category_id: str) -> dict:
        """§5.4 Delete a category."""
        return await ws().call("config/category_registry/delete",
                               scope=scope, category_id=category_id)

    # ---- Zones ----
    @tool(mcp)
    async def create_zone(name: str, latitude: float, longitude: float,
                          radius: int = 100, icon: str | None = None) -> dict:
        """§5.5 Create a zone via zone.create service."""
        data = {"name": name, "latitude": latitude, "longitude": longitude, "radius": radius}
        if icon: data["icon"] = icon
        return await ws().call("call_service", domain="zone", service="reload",
                                service_data=data)

    return 19
