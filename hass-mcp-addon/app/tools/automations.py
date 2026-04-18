"""§7 Automations / scripts / scenes / helpers / blueprints."""
from __future__ import annotations

import httpx

from .. import config as cfg
from ..ws_client import get_ws
from ._helpers import tool


HELPER_DOMAINS = ["input_boolean", "input_text", "input_number", "input_select",
                  "input_datetime", "input_button", "counter", "timer", "schedule"]


async def _rest(method: str, path: str, json_body=None):
    url = f"{cfg.get_api_base()}{path}"
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.request(method, url, headers=cfg.get_headers(), json=json_body)
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {"status": "ok"}


def register(mcp) -> int:
    ws = get_ws

    # ---- Automations ----
    @tool(mcp)
    async def list_automations_full() -> list:
        """§7 List all automations (full YAML config)."""
        return await _rest("GET", "/config/automation/config")

    @tool(mcp)
    async def get_automation_yaml(automation_id: str) -> dict:
        """§7 Get automation YAML by id."""
        return await _rest("GET", f"/config/automation/config/{automation_id}")

    @tool(mcp)
    async def create_automation(automation_id: str, config: dict) -> dict:
        """§7 Create or replace an automation."""
        return await _rest("POST", f"/config/automation/config/{automation_id}", config)

    @tool(mcp)
    async def update_automation(automation_id: str, config: dict) -> dict:
        """§7 Update an automation (same as create)."""
        return await _rest("POST", f"/config/automation/config/{automation_id}", config)

    @tool(mcp)
    async def delete_automation(automation_id: str) -> dict:
        """§7 Delete an automation by id."""
        return await _rest("DELETE", f"/config/automation/config/{automation_id}")

    @tool(mcp)
    async def enable_automation(entity_id: str) -> dict:
        """§7 Enable an automation."""
        return await ws().call("call_service", domain="automation",
                                service="turn_on", service_data={"entity_id": entity_id})

    @tool(mcp)
    async def disable_automation(entity_id: str) -> dict:
        """§7 Disable an automation."""
        return await ws().call("call_service", domain="automation",
                                service="turn_off", service_data={"entity_id": entity_id})

    @tool(mcp)
    async def reload_automations() -> dict:
        """§7 Reload all automations."""
        return await ws().call("call_service", domain="automation", service="reload")

    # ---- Scripts ----
    @tool(mcp)
    async def list_scripts_full() -> list:
        """§7 List all scripts."""
        return await _rest("GET", "/config/script/config")

    @tool(mcp)
    async def get_script_yaml(script_id: str) -> dict:
        """§7 Get script YAML."""
        return await _rest("GET", f"/config/script/config/{script_id}")

    @tool(mcp)
    async def create_script(script_id: str, config: dict) -> dict:
        """§7 Create or replace a script."""
        return await _rest("POST", f"/config/script/config/{script_id}", config)

    @tool(mcp)
    async def delete_script(script_id: str) -> dict:
        """§7 Delete a script."""
        return await _rest("DELETE", f"/config/script/config/{script_id}")

    @tool(mcp)
    async def reload_scripts() -> dict:
        """§7 Reload all scripts."""
        return await ws().call("call_service", domain="script", service="reload")

    # ---- Scenes ----
    @tool(mcp)
    async def list_scenes_full() -> list:
        """§7 List all scenes."""
        return await _rest("GET", "/config/scene/config")

    @tool(mcp)
    async def get_scene_yaml(scene_id: str) -> dict:
        """§7 Get scene YAML."""
        return await _rest("GET", f"/config/scene/config/{scene_id}")

    @tool(mcp)
    async def create_scene(scene_id: str, config: dict) -> dict:
        """§7 Create or replace a scene."""
        return await _rest("POST", f"/config/scene/config/{scene_id}", config)

    @tool(mcp)
    async def delete_scene(scene_id: str) -> dict:
        """§7 Delete a scene."""
        return await _rest("DELETE", f"/config/scene/config/{scene_id}")

    @tool(mcp)
    async def reload_scenes() -> dict:
        """§7 Reload all scenes."""
        return await ws().call("call_service", domain="scene", service="reload")

    # ---- Helpers (input_*, counter, timer, schedule) ----
    @tool(mcp)
    async def list_helpers(domain: str) -> list:
        """§7 List helpers in a domain (input_boolean, counter, timer, schedule, etc.)."""
        if domain not in HELPER_DOMAINS:
            return [{"error": f"unknown helper domain {domain}"}]
        return await ws().call(f"{domain}/list")

    @tool(mcp)
    async def create_helper(domain: str, config: dict) -> dict:
        """§7 Create a helper. config must include 'name' (and others per domain)."""
        return await ws().call(f"{domain}/create", **config)

    @tool(mcp)
    async def update_helper(domain: str, helper_id: str, patch: dict) -> dict:
        """§7 Update a helper by id."""
        return await ws().call(f"{domain}/update", **{f"{domain}_id": helper_id, **patch})

    @tool(mcp)
    async def delete_helper(domain: str, helper_id: str) -> dict:
        """§7 Delete a helper."""
        return await ws().call(f"{domain}/delete", **{f"{domain}_id": helper_id})

    # ---- Blueprints ----
    @tool(mcp)
    async def list_blueprints(domain: str = "automation") -> dict:
        """§7 List blueprints (domain: automation|script)."""
        return await ws().call("blueprint/list", domain=domain)

    @tool(mcp)
    async def import_blueprint(url: str, domain: str = "automation") -> dict:
        """§7 Import a blueprint from a URL."""
        return await ws().call("blueprint/import", url=url, domain=domain)

    @tool(mcp)
    async def delete_blueprint(domain: str, path: str) -> dict:
        """§7 Delete a blueprint."""
        return await ws().call("blueprint/delete", domain=domain, path=path)

    @tool(mcp)
    async def substitute_blueprint(domain: str, path: str, substitutions: dict) -> dict:
        """§7 Substitute placeholders in a blueprint."""
        return await ws().call("blueprint/substitute", domain=domain,
                                path=path, input=substitutions)

    return 25
