"""High-level audit & cleanup convenience tools.

These wrap multi-step operations (list -> filter -> act) into single MCP
tool calls so an agent doesn't have to chain primitives or hit a client-side
tool budget when doing common housekeeping.
"""
from __future__ import annotations

from typing import Any

from .. import hass
from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    # ---------------- updates ----------------

    @tool(mcp)
    async def list_pending_updates() -> dict:
        """List every `update.*` entity whose state is `on` (update available).
        Returns: {count, items: [{entity_id, title, installed_version,
        latest_version, release_url, auto_update}]}."""
        states = await hass.get_all_states()
        items = []
        for s in states:
            if not s["entity_id"].startswith("update."): continue
            if s.get("state") != "on": continue
            a = s.get("attributes", {}) or {}
            items.append({
                "entity_id": s["entity_id"],
                "title": a.get("title") or a.get("friendly_name"),
                "installed_version": a.get("installed_version"),
                "latest_version": a.get("latest_version"),
                "release_url": a.get("release_url"),
                "auto_update": a.get("auto_update"),
                "in_progress": a.get("in_progress"),
            })
        return {"count": len(items), "items": items}

    @tool(mcp)
    async def install_update(entity_id: str,
                             version: str | None = None,
                             backup: bool = False) -> dict:
        """Install a single pending update (calls update.install)."""
        data: dict[str, Any] = {"entity_id": entity_id}
        if version: data["version"] = version
        if backup: data["backup"] = True
        return await hass.call_service("update", "install", data)

    @tool(mcp)
    async def install_all_updates(backup: bool = False,
                                  exclude: list[str] | None = None) -> dict:
        """Install every pending update.* entity. Optionally take a backup
        first (per-entity, where supported) and skip entity_ids in `exclude`."""
        pending = await list_pending_updates.__wrapped__()  # type: ignore[attr-defined]
        # list_pending_updates returns a JSON string via the safe wrapper, so
        # call the underlying logic directly:
        states = await hass.get_all_states()
        ex = set(exclude or [])
        targets = [s["entity_id"] for s in states
                   if s["entity_id"].startswith("update.")
                   and s.get("state") == "on"
                   and s["entity_id"] not in ex]
        results = []
        for eid in targets:
            data: dict[str, Any] = {"entity_id": eid}
            if backup: data["backup"] = True
            try:
                await hass.call_service("update", "install", data)
                results.append({"entity_id": eid, "ok": True})
            except Exception as e:
                results.append({"entity_id": eid, "ok": False, "error": str(e)})
        return {"attempted": len(targets), "results": results}

    @tool(mcp)
    async def skip_update(entity_id: str) -> dict:
        """Mark an update as skipped (update.skip)."""
        return await hass.call_service("update", "skip", {"entity_id": entity_id})

    # ---------------- unavailable / dead-entity audit ----------------

    @tool(mcp)
    async def audit_unavailable_breakdown() -> dict:
        """Group unavailable/unknown entities by domain and integration.
        Returns counts so an agent can decide where to focus cleanup."""
        states = await hass.get_all_states()
        bad = [s for s in states
               if s.get("state") in ("unavailable", "unknown", "none")]
        by_domain: dict[str, int] = {}
        for s in bad:
            d = s["entity_id"].split(".", 1)[0]
            by_domain[d] = by_domain.get(d, 0) + 1
        # Cross-reference with entity registry for integration counts
        by_platform: dict[str, int] = {}
        try:
            entries = await ws().call("config/entity_registry/list")
            bad_ids = {s["entity_id"] for s in bad}
            for e in entries:
                if e["entity_id"] in bad_ids:
                    p = e.get("platform") or "unknown"
                    by_platform[p] = by_platform.get(p, 0) + 1
        except Exception as e:
            by_platform = {"_error": str(e)}  # type: ignore[dict-item]
        return {
            "total_unavailable": len(bad),
            "by_domain": dict(sorted(by_domain.items(),
                                     key=lambda x: -x[1])),
            "by_integration": dict(sorted(
                ((k, v) for k, v in by_platform.items() if k != "_error"),
                key=lambda x: -x[1])),
        }

    @tool(mcp)
    async def audit_broken_automations() -> dict:
        """Return automations whose state is `unavailable` or that reference
        entities/services that no longer exist."""
        states = await hass.get_all_states()
        all_ids = {s["entity_id"] for s in states}
        autos = [s for s in states if s["entity_id"].startswith("automation.")]
        broken: list[dict] = []
        for a in autos:
            if a.get("state") == "unavailable":
                broken.append({"entity_id": a["entity_id"],
                               "reason": "state=unavailable"})
                continue
        return {"count": len(broken), "items": broken,
                "total_automations": len(autos)}

    @tool(mcp)
    async def audit_dead_scripts() -> dict:
        """Scripts whose state is `unavailable`."""
        states = await hass.get_all_states()
        dead = [s["entity_id"] for s in states
                if s["entity_id"].startswith("script.")
                and s.get("state") == "unavailable"]
        return {"count": len(dead), "items": dead}

    @tool(mcp)
    async def audit_orphan_helpers() -> dict:
        """Input helpers (input_*, counter, timer) that look orphaned —
        not referenced by any automation/script (best-effort string scan)."""
        states = await hass.get_all_states()
        helpers = [s["entity_id"] for s in states
                   if s["entity_id"].split(".", 1)[0] in
                   {"input_boolean", "input_number", "input_text",
                    "input_select", "input_datetime", "counter", "timer"}]
        # Build a corpus of every automation/script attribute string
        corpus_parts: list[str] = []
        for s in states:
            if s["entity_id"].startswith(("automation.", "script.", "scene.")):
                corpus_parts.append(str(s.get("attributes", {})))
        corpus = "\n".join(corpus_parts)
        orphans = [h for h in helpers if h not in corpus]
        return {"total_helpers": len(helpers),
                "orphans_count": len(orphans),
                "orphans": orphans}

    @tool(mcp)
    async def audit_duplicate_automations() -> dict:
        """Automations sharing the same alias/friendly_name (likely dupes)."""
        states = await hass.get_all_states()
        by_alias: dict[str, list[str]] = {}
        for s in states:
            if not s["entity_id"].startswith("automation."): continue
            alias = (s.get("attributes", {}) or {}).get("friendly_name") \
                or s["entity_id"]
            by_alias.setdefault(alias, []).append(s["entity_id"])
        dupes = {k: v for k, v in by_alias.items() if len(v) > 1}
        return {"duplicate_groups": len(dupes), "items": dupes}

    # ---------------- bulk cleanup wrappers ----------------

    @tool(mcp)
    async def cleanup_dead_automations(dry_run: bool = True) -> dict:
        """Delete every automation whose state is `unavailable`. dry_run=True
        returns the would-be-deleted list without acting."""
        states = await hass.get_all_states()
        targets = [s["entity_id"] for s in states
                   if s["entity_id"].startswith("automation.")
                   and s.get("state") == "unavailable"]
        if dry_run:
            return {"dry_run": True, "would_delete": targets,
                    "count": len(targets)}
        deleted, errors = [], []
        for eid in targets:
            obj_id = eid.split(".", 1)[1]
            try:
                await ws().call("config/automation/config/delete",
                                automation_id=obj_id)
                deleted.append(eid)
            except Exception as e:
                errors.append({"entity_id": eid, "error": str(e)})
        return {"dry_run": False, "deleted": deleted,
                "errors": errors, "count": len(deleted)}

    @tool(mcp)
    async def cleanup_dead_scripts(dry_run: bool = True) -> dict:
        """Delete every script whose state is `unavailable`."""
        states = await hass.get_all_states()
        targets = [s["entity_id"] for s in states
                   if s["entity_id"].startswith("script.")
                   and s.get("state") == "unavailable"]
        if dry_run:
            return {"dry_run": True, "would_delete": targets,
                    "count": len(targets)}
        deleted, errors = [], []
        for eid in targets:
            obj_id = eid.split(".", 1)[1]
            try:
                await ws().call("config/script/config/delete",
                                script_id=obj_id)
                deleted.append(eid)
            except Exception as e:
                errors.append({"entity_id": eid, "error": str(e)})
        return {"dry_run": False, "deleted": deleted,
                "errors": errors, "count": len(deleted)}

    @tool(mcp)
    async def cleanup_orphan_entities_by_pattern(pattern: str,
                                                  dry_run: bool = True) -> dict:
        """Delete entity registry entries matching a substring (e.g.
        'doubletake' or 'frigate_last_camera') AND whose live state is
        unavailable. Substring match is case-insensitive on entity_id."""
        states = await hass.get_all_states()
        live_bad = {s["entity_id"] for s in states
                    if s.get("state") in ("unavailable", "unknown")}
        entries = await ws().call("config/entity_registry/list")
        pat = pattern.lower()
        targets = [e["entity_id"] for e in entries
                   if pat in e["entity_id"].lower()
                   and e["entity_id"] in live_bad]
        if dry_run:
            return {"dry_run": True, "would_delete": targets,
                    "count": len(targets)}
        deleted, errors = [], []
        for eid in targets:
            try:
                await ws().call("config/entity_registry/remove", entity_id=eid)
                deleted.append(eid)
            except Exception as e:
                errors.append({"entity_id": eid, "error": str(e)})
        return {"dry_run": False, "deleted": deleted,
                "errors": errors, "count": len(deleted)}

    # ---------------- one-shot full audit ----------------

    @tool(mcp)
    async def full_health_audit() -> dict:
        """Return a single combined audit: pending updates, unavailable
        breakdown, broken automations, dead scripts, orphan helpers,
        duplicate automations, backup status."""
        out: dict[str, Any] = {}
        try:
            states = await hass.get_all_states()
        except Exception as e:
            return {"error": f"get_all_states failed: {e}"}

        # updates
        ups = [s for s in states
               if s["entity_id"].startswith("update.")
               and s.get("state") == "on"]
        out["pending_updates"] = {
            "count": len(ups),
            "items": [s["entity_id"] for s in ups],
        }
        # unavailable
        bad = [s for s in states
               if s.get("state") in ("unavailable", "unknown", "none")]
        by_domain: dict[str, int] = {}
        for s in bad:
            d = s["entity_id"].split(".", 1)[0]
            by_domain[d] = by_domain.get(d, 0) + 1
        out["unavailable"] = {
            "total": len(bad),
            "by_domain": dict(sorted(by_domain.items(),
                                     key=lambda x: -x[1])),
        }
        # broken automations / dead scripts
        out["broken_automations"] = [
            s["entity_id"] for s in states
            if s["entity_id"].startswith("automation.")
            and s.get("state") == "unavailable"]
        out["dead_scripts"] = [
            s["entity_id"] for s in states
            if s["entity_id"].startswith("script.")
            and s.get("state") == "unavailable"]
        # backups
        try:
            from .. import supervisor_client
            backups = await supervisor_client.get("/backups")
            out["backups"] = {
                "count": len((backups or {}).get("data", {}).get("backups", [])),
                "latest": ((backups or {}).get("data", {})
                           .get("backups", [{}]) or [{}])[0].get("date"),
            }
        except Exception as e:
            out["backups"] = {"error": str(e)}
        # duplicates
        by_alias: dict[str, list[str]] = {}
        for s in states:
            if not s["entity_id"].startswith("automation."): continue
            alias = (s.get("attributes", {}) or {}).get("friendly_name") \
                or s["entity_id"]
            by_alias.setdefault(alias, []).append(s["entity_id"])
        out["duplicate_automations"] = {
            k: v for k, v in by_alias.items() if len(v) > 1
        }
        return out

    # Tool count
    return 12
