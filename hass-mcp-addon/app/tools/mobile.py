"""§21 Companion app / mobile."""
from __future__ import annotations

from .. import hass
from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def list_mobile_apps() -> list:
        """§21 List installed mobile_app device trackers."""
        states = await hass.get_all_states()
        return [s["entity_id"] for s in states
                if s["entity_id"].startswith("device_tracker.")
                and (s.get("attributes", {}).get("source_type") == "gps"
                     or "mobile_app" in s["entity_id"])]

    @tool(mcp)
    async def send_actionable_notification(service: str, message: str,
                                             actions: list[dict],
                                             title: str | None = None) -> dict:
        """§21 Mobile actionable notification helper."""
        data = {"actions": actions}
        payload = {"message": message, "data": data}
        if title: payload["title"] = title
        return await ws().call("call_service", domain="notify",
                                service=service, service_data=payload)

    @tool(mcp)
    async def geocode_user(person_entity_id: str) -> dict:
        """§21 Reverse geocode a person via template."""
        tpl = (
            f"{{% set lat = state_attr('{person_entity_id}', 'latitude') %}}"
            f"{{% set lon = state_attr('{person_entity_id}', 'longitude') %}}"
            "{\"latitude\": {{ lat }}, \"longitude\": {{ lon }}}"
        )
        import json
        try:
            return json.loads(await hass.render_template(tpl))
        except Exception as e:
            return {"error": str(e)}

    @tool(mcp)
    async def get_user_location(entity_id: str) -> dict:
        """§21 Current location of a person/device_tracker entity."""
        s = await hass.get_entity_state(entity_id)
        a = s.get("attributes", {})
        return {"entity_id": entity_id, "state": s.get("state"),
                "latitude": a.get("latitude"),
                "longitude": a.get("longitude"),
                "gps_accuracy": a.get("gps_accuracy")}

    @tool(mcp)
    async def update_mobile_app_sensor(webhook_id: str, sensor_id: str,
                                         state, attributes: dict | None = None) -> dict:
        """§21 mobile_app/update_sensor_states via webhook."""
        return await ws().call("call_service", domain="mobile_app",
                                service="update_sensor_state",
                                service_data={"webhook_id": webhook_id,
                                              "sensor_id": sensor_id,
                                              "state": state,
                                              "attributes": attributes or {}})

    return 5
