"""§58 Multi-modal output (mass takeover, voice clone, AR overlay)."""
from __future__ import annotations

from typing import Any

import httpx

from .. import hass
from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def display_takeover(content_url: str, target_filter: dict | None = None) -> Any:
        """§58 Push a URL/image/video to every browser_mod / wallpanel /
        cast / awtrix display (best-effort across known services)."""
        states = await hass.get_all_states()
        results = []
        for s in states:
            eid = s["entity_id"]
            try:
                if eid.startswith("media_player."):
                    if target_filter and not all(
                        s.get("attributes", {}).get(k) == v
                        for k, v in target_filter.items()):
                        continue
                    r = await ws().call("call_service", domain="media_player",
                                         service="play_media",
                                         service_data={"entity_id": eid,
                                                        "media_content_id": content_url,
                                                        "media_content_type": "image/jpeg"})
                    results.append({"entity": eid, "ok": True})
            except Exception as e:
                results.append({"entity": eid, "error": str(e)})
        # Also push via browser_mod if present
        try:
            await ws().call("call_service", domain="browser_mod", service="popup",
                             service_data={"content": {"type": "iframe",
                                                         "url": content_url}})
        except Exception: pass
        return {"pushed": len(results), "results": results}

    @tool(mcp)
    async def mass_notify_all_humans(message: str, title: str = "Notice",
                                      include_speakers: bool = True,
                                      tts_service: str = "tts.cloud_say") -> Any:
        """§58 Fan out to every notify.* service and (optionally) every media_player."""
        services = await ws().call("get_services")
        notifies = list((services or {}).get("notify", {}).keys())
        out: dict[str, Any] = {"notify": [], "tts": []}
        for n in notifies:
            try:
                await ws().call("call_service", domain="notify", service=n,
                                 service_data={"message": message, "title": title})
                out["notify"].append(n)
            except Exception as e:
                out["notify"].append({"service": n, "error": str(e)})
        if include_speakers:
            states = await hass.get_all_states()
            for s in states:
                if s["entity_id"].startswith("media_player."):
                    try:
                        await ws().call("call_service",
                                         domain=tts_service.split(".")[0],
                                         service=tts_service.split(".")[1],
                                         service_data={"entity_id": s["entity_id"],
                                                        "message": message})
                        out["tts"].append(s["entity_id"])
                    except Exception:
                        pass
        return out

    @tool(mcp)
    async def voice_clone_tts(text: str, voice_id: str,
                                provider: str = "elevenlabs",
                                api_key: str | None = None,
                                output_path: str = "/media/voice_clone.mp3") -> Any:
        """§58 Generate cloned-voice speech via ElevenLabs / XTTS server."""
        if provider == "elevenlabs":
            if not api_key:
                from .saas import _load_creds  # type: ignore
                api_key = _load_creds().get("elevenlabs", {}).get("api_key")
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            async with httpx.AsyncClient(timeout=120.0) as c:
                r = await c.post(url, headers={"xi-api-key": api_key or "",
                                                  "Content-Type": "application/json"},
                                  json={"text": text})
                r.raise_for_status()
                with open(output_path, "wb") as f: f.write(r.content)
            return {"path": output_path, "bytes": len(r.content)}
        if provider == "xtts":
            url = "http://homeassistant.local:8020/api/tts"  # XTTS server default
            async with httpx.AsyncClient(timeout=120.0) as c:
                r = await c.post(url, json={"text": text, "speaker_wav": voice_id})
                r.raise_for_status()
                with open(output_path, "wb") as f: f.write(r.content)
            return {"path": output_path, "bytes": len(r.content)}
        return {"error": f"unknown provider {provider}"}

    @tool(mcp)
    async def lip_sync_avatar_push(dashboard_path: str, avatar_url: str,
                                     audio_url: str) -> Any:
        """§58 Push talking-head card config to a Lovelace dashboard."""
        cfg = await ws().call("lovelace/config", url_path=dashboard_path)
        views = cfg.get("views", [])
        if not views:
            return {"error": "dashboard has no views"}
        views[0].setdefault("cards", []).insert(0, {
            "type": "picture",
            "image": avatar_url,
            "tap_action": {"action": "url", "url_path": audio_url},
        })
        await ws().call("lovelace/config/save", url_path=dashboard_path,
                         config=cfg)
        return {"pushed": True, "dashboard": dashboard_path}

    @tool(mcp)
    async def ar_overlay_push(scene_url: str, target_devices: list[str] | None = None) -> Any:
        """§58 Send a WebXR/AR scene URL to mobile_app companion notifications."""
        devices = target_devices or []
        if not devices:
            services = await ws().call("get_services")
            devices = [n for n in (services or {}).get("notify", {})
                        if n.startswith("mobile_app_")]
        out = []
        for d in devices:
            try:
                await ws().call("call_service", domain="notify", service=d,
                                 service_data={"message": "Open AR scene",
                                                "data": {"url": scene_url,
                                                          "actions": [{"action": "URI",
                                                                        "title": "Open",
                                                                        "uri": scene_url}]}})
                out.append({"device": d, "ok": True})
            except Exception as e:
                out.append({"device": d, "error": str(e)})
        return out

    return 5
