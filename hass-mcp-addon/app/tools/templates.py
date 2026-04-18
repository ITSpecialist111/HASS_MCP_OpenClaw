"""§12 Templates / validation / selectors."""
from __future__ import annotations

from .. import hass
from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def render_template_full(template: str, variables: dict | None = None) -> str:
        """§12 Render a Jinja template (full HA template engine)."""
        # Use REST for simple render
        return await hass.render_template(template)

    @tool(mcp)
    async def validate_config_full() -> dict:
        """§12 Validate the running HA configuration."""
        return await ws().call("validate_config")

    @tool(mcp)
    async def validate_template(template: str) -> dict:
        """§12 Validate a template renders without error."""
        try:
            res = await hass.render_template(template)
            return {"valid": True, "rendered": res}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    @tool(mcp)
    async def list_template_functions() -> list:
        """§12 Reference list of HA template functions / filters."""
        return [
            "states", "state_attr", "is_state", "is_state_attr",
            "states.<domain>", "expand", "device_id", "device_attr",
            "device_entities", "area_id", "area_name", "area_entities",
            "area_devices", "areas", "floors", "floor_name", "floor_areas",
            "floor_entities", "labels", "label_name", "label_entities",
            "label_areas", "label_devices", "label_description",
            "integration_entities", "config_entry_id", "config_entry_attr",
            "iif", "regex_match", "regex_search", "regex_replace",
            "now", "utcnow", "today_at", "as_datetime", "as_timestamp",
            "timedelta", "min", "max", "average", "median", "statistical_mode",
            "tojson", "from_json", "base64_encode", "base64_decode",
            "urlencode", "urldecode", "ord", "char", "wait_for_state",
        ]

    @tool(mcp)
    async def selector_render(selector: dict, value=None) -> dict:
        """§12 Render a selector definition (introspect via WS)."""
        return await ws().send({"type": "selector/get", "selector": selector,
                                 "value": value})

    return 5
