"""§38 Cross-surface search."""
from __future__ import annotations

import re
from typing import Any

from .. import hass
from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def global_search(query: str) -> dict:
        """§38 Search entities + areas + devices + automations + scripts +
        scenes + dashboards + helpers + persons in one shot."""
        q = query.lower()
        results: dict[str, Any] = {"query": query}

        states = await hass.get_all_states()
        results["entities"] = [s["entity_id"] for s in states
                                if q in s["entity_id"].lower()
                                or q in str(s.get("attributes", {})
                                            .get("friendly_name", "")).lower()]
        try:
            areas = await ws().call("config/area_registry/list")
            results["areas"] = [a for a in areas if q in (a.get("name") or "").lower()]
        except Exception: pass
        try:
            devs = await ws().call("config/device_registry/list")
            results["devices"] = [d for d in devs
                                   if q in (d.get("name") or d.get("name_by_user") or "").lower()]
        except Exception: pass
        try:
            ents = await ws().call("config/entity_registry/list")
            results["registry_matches"] = [e for e in ents
                                            if q in e["entity_id"].lower()
                                            or q in (e.get("name") or "").lower()]
        except Exception: pass
        return results

    @tool(mcp)
    async def find_unused(domain: str | None = None) -> dict:
        """§38 Find entities not referenced by any automation/script/scene/dashboard."""
        # Read .storage files and search
        import os, json
        config_dir = "/config" if os.path.isdir("/config") else "/homeassistant"
        scan_files = [
            ".storage/core.config_entries", ".storage/lovelace",
            ".storage/lovelace.dashboards",
            "automations.yaml", "scripts.yaml", "scenes.yaml",
        ]
        haystack = ""
        for f in scan_files:
            p = os.path.join(config_dir, f)
            if os.path.exists(p):
                try:
                    with open(p) as fh: haystack += "\n" + fh.read()
                except Exception:
                    pass
        # Also scan .storage/lovelace_*
        ls = os.path.join(config_dir, ".storage")
        if os.path.isdir(ls):
            for fn in os.listdir(ls):
                if fn.startswith("lovelace"):
                    try:
                        with open(os.path.join(ls, fn)) as fh: haystack += "\n" + fh.read()
                    except Exception: pass
        states = await hass.get_all_states()
        unused = []
        for s in states:
            eid = s["entity_id"]
            if domain and not eid.startswith(f"{domain}."):
                continue
            if eid not in haystack:
                unused.append(eid)
        return {"count": len(unused), "entities": unused}

    @tool(mcp)
    async def find_dependencies(entity_id: str) -> dict:
        """§38 Find automations/scripts/scenes/dashboards referencing an entity."""
        import os
        config_dir = "/config" if os.path.isdir("/config") else "/homeassistant"
        from .. import shell as _shell
        res = await _shell.shell_exec(
            f"rg -l --no-messages -F {entity_id!r} {config_dir!r}",
            timeout=60.0)
        files = [l for l in (res.get("stdout") or "").splitlines() if l]
        return {"entity_id": entity_id, "files": files}

    @tool(mcp)
    async def find_broken_references() -> dict:
        """§38 Find references in YAML to entity_ids that no longer exist."""
        import os, re
        config_dir = "/config" if os.path.isdir("/config") else "/homeassistant"
        states = await hass.get_all_states()
        existing = {s["entity_id"] for s in states}
        eid_re = re.compile(r"\b([a-z_]+\.[a-z0-9_]+)\b")
        broken: dict[str, list[str]] = {}
        for fname in ("automations.yaml", "scripts.yaml", "scenes.yaml",
                       "configuration.yaml"):
            p = os.path.join(config_dir, fname)
            if not os.path.exists(p): continue
            try:
                with open(p) as f: text = f.read()
            except Exception: continue
            for m in set(eid_re.findall(text)):
                if "." in m and m.split(".")[0] in {
                    "light","switch","sensor","binary_sensor","climate","cover",
                    "fan","media_player","camera","alarm_control_panel","lock",
                    "vacuum","automation","script","scene","input_boolean",
                    "input_number","input_text","input_select","timer","counter"
                } and m not in existing:
                    broken.setdefault(fname, []).append(m)
        return broken

    return 4
