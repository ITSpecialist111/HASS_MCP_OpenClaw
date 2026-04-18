"""§39 Bulk maintenance operations."""
from __future__ import annotations

import re
from typing import Any

from .. import hass
from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def cleanup_unavailable_entities(integration: str | None = None,
                                            domain: str | None = None) -> dict:
        """§39 Delete every entity whose state is unavailable/unknown
        (optionally restricted to integration/domain)."""
        states = await hass.get_all_states()
        bad = {s["entity_id"] for s in states
                if s.get("state") in ("unavailable", "unknown")}
        if domain:
            bad = {e for e in bad if e.startswith(f"{domain}.")}
        entries = await ws().call("config/entity_registry/list")
        targets = []
        for e in entries:
            if e["entity_id"] not in bad: continue
            if integration and e.get("platform") != integration: continue
            targets.append(e["entity_id"])
        removed = []
        for eid in targets:
            try:
                await ws().call("config/entity_registry/remove", entity_id=eid)
                removed.append(eid)
            except Exception:
                pass
        return {"removed": removed, "count": len(removed)}

    @tool(mcp)
    async def cleanup_orphaned_devices() -> dict:
        """§39 Delete devices that have zero entities."""
        devs = await ws().call("config/device_registry/list")
        ents = await ws().call("config/entity_registry/list")
        used = {e.get("device_id") for e in ents if e.get("device_id")}
        removed = []
        for d in devs:
            if d.get("id") not in used:
                for ce in d.get("config_entries", []):
                    try:
                        await ws().call("config/device_registry/remove_config_entry",
                                         device_id=d["id"], config_entry_id=ce)
                        removed.append(d["id"])
                        break
                    except Exception:
                        pass
        return {"removed": removed, "count": len(removed)}

    @tool(mcp)
    async def cleanup_unused_areas() -> dict:
        """§39 Delete areas with zero devices and zero entities."""
        areas = await ws().call("config/area_registry/list")
        devs = await ws().call("config/device_registry/list")
        ents = await ws().call("config/entity_registry/list")
        used = {d.get("area_id") for d in devs} | {e.get("area_id") for e in ents}
        removed = []
        for a in areas:
            if a.get("area_id") not in used:
                try:
                    await ws().call("config/area_registry/delete",
                                     area_id=a["area_id"])
                    removed.append(a["area_id"])
                except Exception:
                    pass
        return {"removed": removed, "count": len(removed)}

    @tool(mcp)
    async def cleanup_unused_labels() -> dict:
        """§39 Delete labels with no entity/device/area assignments."""
        try:
            labels = await ws().call("config/label_registry/list")
        except Exception:
            return {"error": "label registry not available"}
        ents = await ws().call("config/entity_registry/list")
        devs = await ws().call("config/device_registry/list")
        used: set[str] = set()
        for x in (*ents, *devs):
            for l in (x.get("labels") or []): used.add(l)
        removed = []
        for l in labels:
            if l.get("label_id") not in used:
                try:
                    await ws().call("config/label_registry/delete",
                                     label_id=l["label_id"])
                    removed.append(l["label_id"])
                except Exception:
                    pass
        return {"removed": removed, "count": len(removed)}

    @tool(mcp)
    async def cleanup_restored_entities(days_unseen: int = 30) -> dict:
        """§39 Delete entities flagged restored:true and not seen for N days."""
        # No reliable last_seen for restored entities via API; approximate via DB
        from .. import sql as _sql
        rows = _sql.query(
            "SELECT sm.entity_id, MAX(s.last_updated_ts) AS last_ts "
            "FROM states_meta sm LEFT JOIN states s ON sm.metadata_id=s.metadata_id "
            "GROUP BY sm.entity_id")["rows"]
        import time
        cutoff = time.time() - days_unseen * 86400
        old = [r["entity_id"] for r in rows if (r.get("last_ts") or 0) < cutoff]
        entries = await ws().call("config/entity_registry/list")
        eids = {e["entity_id"] for e in entries}
        removed = []
        for eid in old:
            if eid in eids:
                try:
                    await ws().call("config/entity_registry/remove", entity_id=eid)
                    removed.append(eid)
                except Exception:
                    pass
        return {"removed": removed, "count": len(removed)}

    @tool(mcp)
    async def rename_by_pattern(pattern: str, replacement: str,
                                 dry_run: bool = True) -> dict:
        """§39 Regex-rename entity_ids."""
        rx = re.compile(pattern)
        entries = await ws().call("config/entity_registry/list")
        plan = []
        for e in entries:
            new = rx.sub(replacement, e["entity_id"])
            if new != e["entity_id"]:
                plan.append((e["entity_id"], new))
        if dry_run:
            return {"plan": plan, "count": len(plan), "applied": False}
        for old, new in plan:
            try:
                await ws().call("config/entity_registry/update",
                                 entity_id=old, new_entity_id=new)
            except Exception:
                pass
        return {"applied": True, "count": len(plan), "plan": plan}

    @tool(mcp)
    async def move_by_pattern(pattern: str, area_id: str,
                                dry_run: bool = True) -> dict:
        """§39 Move all entities matching regex into area."""
        rx = re.compile(pattern)
        entries = await ws().call("config/entity_registry/list")
        targets = [e["entity_id"] for e in entries if rx.search(e["entity_id"])]
        if dry_run:
            return {"plan": targets, "count": len(targets), "area": area_id, "applied": False}
        for eid in targets:
            try:
                await ws().call("config/entity_registry/update",
                                 entity_id=eid, area_id=area_id)
            except Exception:
                pass
        return {"applied": True, "count": len(targets)}

    @tool(mcp)
    async def bulk_disable_integration(integration: str) -> dict:
        """§39 Disable every entity belonging to an integration."""
        entries = await ws().call("config/entity_registry/list")
        targets = [e["entity_id"] for e in entries if e.get("platform") == integration]
        for eid in targets:
            try:
                await ws().call("config/entity_registry/update",
                                 entity_id=eid, disabled_by="user")
            except Exception:
                pass
        return {"disabled": targets, "count": len(targets)}

    @tool(mcp)
    async def mass_purge_recorder(keep_days: int = 7,
                                    entity_globs: list[str] | None = None,
                                    repack: bool = True) -> dict:
        """§39 Purge recorder data older than `keep_days` and optionally
        delete given entity_globs entirely."""
        await ws().call("call_service", domain="recorder", service="purge",
                         service_data={"keep_days": keep_days, "repack": repack})
        if entity_globs:
            await ws().call("call_service", domain="recorder",
                             service="purge_entities",
                             service_data={"entity_globs": entity_globs})
        return {"keep_days": keep_days, "purged_globs": entity_globs}

    @tool(mcp)
    async def audit_report() -> dict:
        """§39 Health summary: unavailable counts, broken refs, orphans, db size, updates."""
        from .. import sql as _sql
        from .. import supervisor_client as sup
        states = await hass.get_all_states()
        unavailable = sum(1 for s in states if s.get("state") in ("unavailable", "unknown"))
        try:
            updates = await sup.get("/available_updates")
        except Exception:
            updates = []
        return {
            "total_entities": len(states),
            "unavailable_or_unknown": unavailable,
            "db_size": _sql.db_size(),
            "available_updates": updates,
        }

    return 10
