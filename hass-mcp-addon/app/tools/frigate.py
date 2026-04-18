"""§18 Frigate (HTTP API + config file)."""
from __future__ import annotations

import os
from typing import Any

import httpx

from .. import shell as _shell
from ._helpers import tool

FRIGATE_URL = os.environ.get("FRIGATE_URL", "http://homeassistant.local:5000")
FRIGATE_CONFIG = "/config/frigate/config.yaml"


async def _fg(method: str, path: str, **kwargs) -> Any:
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.request(method.upper(), f"{FRIGATE_URL}{path}", **kwargs)
        r.raise_for_status()
        try: return r.json()
        except Exception: return r.text


def register(mcp) -> int:

    @tool(mcp)
    async def frigate_list_cameras() -> Any:
        """§18 List Frigate cameras."""
        cfg = await _fg("GET", "/api/config")
        return list(cfg.get("cameras", {}).keys())

    @tool(mcp)
    async def frigate_get_camera_config(camera: str) -> Any:
        """§18 Camera config."""
        cfg = await _fg("GET", "/api/config")
        return cfg.get("cameras", {}).get(camera)

    @tool(mcp)
    async def frigate_get_events(limit: int = 50, camera: str | None = None) -> Any:
        """§18 List events."""
        params: dict[str, Any] = {"limit": limit}
        if camera: params["camera"] = camera
        return await _fg("GET", "/api/events", params=params)

    @tool(mcp)
    async def frigate_delete_event(event_id: str) -> Any:
        """§18 Delete event."""
        return await _fg("DELETE", f"/api/events/{event_id}")

    @tool(mcp)
    async def frigate_get_recordings(camera: str, after: float | None = None,
                                       before: float | None = None) -> Any:
        """§18 List recordings."""
        params = {k: v for k, v in {"after": after, "before": before}.items() if v}
        return await _fg("GET", f"/api/{camera}/recordings", params=params)

    @tool(mcp)
    async def frigate_export_clip(camera: str, start: float, end: float,
                                    playback: str = "realtime") -> Any:
        """§18 Export a clip from a time range."""
        return await _fg("POST", f"/api/export/{camera}/start/{start}/end/{end}",
                         json={"playback": playback})

    @tool(mcp)
    async def frigate_snapshot(camera: str) -> Any:
        """§18 Get a snapshot URL."""
        return {"url": f"{FRIGATE_URL}/api/{camera}/latest.jpg"}

    @tool(mcp)
    async def frigate_clip_url(event_id: str) -> Any:
        """§18 Clip URL for an event."""
        return {"url": f"{FRIGATE_URL}/api/events/{event_id}/clip.mp4"}

    @tool(mcp)
    async def frigate_update_config(yaml_content: str, restart: bool = True) -> Any:
        """§18 Overwrite Frigate config and optionally restart the addon."""
        with open(FRIGATE_CONFIG, "w") as f:
            f.write(yaml_content)
        out = {"path": FRIGATE_CONFIG, "bytes": len(yaml_content)}
        if restart:
            from .. import supervisor_client as sup
            try:
                await sup.post("/addons/ccab4aaf_frigate/restart")
                out["restarted"] = True
            except Exception as e:
                out["restart_error"] = str(e)
        return out

    @tool(mcp)
    async def frigate_restart() -> Any:
        """§18 Restart the Frigate add-on."""
        from .. import supervisor_client as sup
        return await sup.post("/addons/ccab4aaf_frigate/restart")

    return 10
