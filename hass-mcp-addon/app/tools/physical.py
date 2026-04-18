"""§55 Physical world (PTZ, locks, intercom, vehicle, irrigation, banking)."""
from __future__ import annotations

from typing import Any

import httpx

from ..ws_client import get_ws
from ._helpers import tool


async def _hit(method: str, url: str, **kw) -> Any:
    async with httpx.AsyncClient(timeout=60.0, verify=kw.pop("verify", True)) as c:
        r = await c.request(method.upper(), url, **kw)
        try: body = r.json()
        except Exception: body = r.text
        return {"status_code": r.status_code, "body": body}


def register(mcp) -> int:
    ws = get_ws

    # ---- ONVIF PTZ ----
    @tool(mcp)
    async def onvif_ptz(host: str, user: str, password: str,
                          action: str = "AbsoluteMove",
                          x: float = 0.0, y: float = 0.0, zoom: float = 0.0,
                          preset: str | None = None) -> Any:
        """§55 Drive an ONVIF PTZ camera (action=AbsoluteMove|GotoPreset|Stop)."""
        try:
            from onvif import ONVIFCamera  # python-onvif-zeep
        except ImportError:
            return {"error": "python-onvif-zeep not installed"}
        cam = ONVIFCamera(host, 80, user, password)
        ptz = cam.create_ptz_service()
        media = cam.create_media_service()
        token = media.GetProfiles()[0].token
        if action == "GotoPreset" and preset:
            ptz.GotoPreset({"ProfileToken": token, "PresetToken": preset})
        elif action == "Stop":
            ptz.Stop({"ProfileToken": token})
        else:
            ptz.AbsoluteMove({"ProfileToken": token,
                                "Position": {"PanTilt": {"x": x, "y": y},
                                              "Zoom": {"x": zoom}}})
        return {"action": action, "ok": True}

    @tool(mcp)
    async def onvif_audio_talkback(host: str, user: str, password: str,
                                      audio_url: str) -> Any:
        """§55 Send audio talkback to ONVIF camera (best-effort RTSP backchannel)."""
        from .. import shell as _shell
        return await _shell.shell_exec(
            f"ffmpeg -y -i {audio_url!r} -c:a aac "
            f"rtsp://{user}:{password}@{host}/talk", timeout=120.0)

    # ---- Door locks ----
    @tool(mcp)
    async def door_lock_action(entity_id: str, action: str = "lock",
                                 code: str | None = None) -> Any:
        """§55 Direct lock.lock|unlock|open via HA service."""
        data = {"entity_id": entity_id}
        if code: data["code"] = code
        return await ws().call("call_service", domain="lock", service=action,
                                service_data=data)

    @tool(mcp)
    async def door_lock_set_user_code(entity_id: str, code_slot: int,
                                        usercode: str,
                                        domain: str = "zwave_js") -> Any:
        """§55 Set a user code on a Z-Wave lock."""
        return await ws().call("call_service", domain=domain,
                                service="set_lock_usercode",
                                service_data={"entity_id": entity_id,
                                              "code_slot": code_slot,
                                              "usercode": usercode})

    @tool(mcp)
    async def door_lock_clear_user_code(entity_id: str, code_slot: int,
                                          domain: str = "zwave_js") -> Any:
        """§55 Clear a user code on a Z-Wave lock."""
        return await ws().call("call_service", domain=domain,
                                service="clear_lock_usercode",
                                service_data={"entity_id": entity_id,
                                              "code_slot": code_slot})

    # ---- Intercoms ----
    @tool(mcp)
    async def intercom_request(vendor: str, base_url: str, method: str,
                                 path: str,
                                 auth_user: str | None = None,
                                 auth_pass: str | None = None,
                                 json_body: dict | None = None) -> Any:
        """§55 Doorbird / 2N / Aiphone / Akuvox REST."""
        auth = (auth_user, auth_pass) if auth_user and auth_pass else None
        return await _hit(method, f"{base_url.rstrip('/')}{path}",
                           auth=auth, json=json_body, verify=False)

    # ---- Vehicle remote (full) ----
    @tool(mcp)
    async def vehicle_command(domain: str, service: str,
                                entity_id: str | None = None,
                                extra: dict | None = None) -> Any:
        """§55 Generic vehicle command (tessie/teslemetry/saic_ismart/porsche etc.)."""
        data = dict(extra or {})
        if entity_id: data["entity_id"] = entity_id
        return await ws().call("call_service", domain=domain, service=service,
                                service_data=data)

    @tool(mcp)
    async def tesla_remote_command(vehicle_id: str, command: str,
                                     access_token: str,
                                     params: dict | None = None) -> Any:
        """§55 Tesla owner-API command (unlock_doors/honk_horn/etc.)."""
        return await _hit("POST",
            f"https://owner-api.teslamotors.com/api/1/vehicles/{vehicle_id}/command/{command}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=params or {})

    # ---- Irrigation / pool / spa ----
    @tool(mcp)
    async def irrigation_request(vendor: str, base_url: str, method: str,
                                   path: str, api_key: str | None = None,
                                   json_body: dict | None = None) -> Any:
        """§55 Hunter Hydrawise / Rachio / Pentair / Jandy REST."""
        h = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        return await _hit(method, f"{base_url.rstrip('/')}{path}",
                           headers=h, json=json_body)

    # ---- Solar export curtailment ----
    @tool(mcp)
    async def solar_set_export_limit(entity_id: str, watts: int) -> Any:
        """§55 Push an export limit via number.set_value (G98/G99 limiter)."""
        return await ws().call("call_service", domain="number",
                                service="set_value",
                                service_data={"entity_id": entity_id,
                                              "value": watts})

    # ---- Octopus account-side ----
    @tool(mcp)
    async def octopus_request(method: str, path: str, api_key: str) -> Any:
        """§55 Octopus REST (account, balance, top-up trigger if available)."""
        return await _hit(method, f"https://api.octopus.energy{path}",
                           auth=(api_key, ""))

    # ---- Banking (Open Banking AISP/PISP) ----
    @tool(mcp)
    async def open_banking_request(method: str, url: str,
                                     access_token: str,
                                     consent_id: str | None = None,
                                     json_body: dict | None = None) -> Any:
        """§55 PSD2 Open Banking call (read-only AIS unless PIS consent supplied)."""
        h = {"Authorization": f"Bearer {access_token}"}
        if consent_id: h["x-fapi-financial-id"] = consent_id
        return await _hit(method, url, headers=h, json=json_body)

    # ---- Battery arbitrage loop helper ----
    @tool(mcp)
    async def battery_arbitrage_step(soc_entity: str, price_entity: str,
                                       charge_below_p: float = 8.0,
                                       discharge_above_p: float = 25.0,
                                       charge_action: dict | None = None,
                                       discharge_action: dict | None = None,
                                       idle_action: dict | None = None) -> Any:
        """§55 Single decision step for a battery arbitrage loop."""
        from .. import hass
        soc_state = (await hass.get_entity_state(soc_entity)).get("state")
        price_state = (await hass.get_entity_state(price_entity)).get("state")
        try:
            price = float(price_state)
        except Exception:
            return {"error": f"price not numeric: {price_state}"}
        chosen = None
        if price <= charge_below_p and charge_action:
            chosen = "charge"
            await ws().call("call_service", **charge_action)
        elif price >= discharge_above_p and discharge_action:
            chosen = "discharge"
            await ws().call("call_service", **discharge_action)
        elif idle_action:
            chosen = "idle"
            await ws().call("call_service", **idle_action)
        return {"price": price, "soc": soc_state, "decision": chosen}

    return 11
