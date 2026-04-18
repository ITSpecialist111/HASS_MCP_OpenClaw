"""§4 Config entry / integration tools."""
from __future__ import annotations

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def list_config_entries(domain: str | None = None,
                                   type_filter: str | None = None) -> list:
        """§4 List all config entries (optionally filter by domain or type)."""
        kwargs = {}
        if domain: kwargs["domain"] = domain
        if type_filter: kwargs["type_filter"] = type_filter
        return await ws().call("config_entries/get", **kwargs)

    @tool(mcp)
    async def get_config_entry(entry_id: str) -> dict:
        """§4 Get a single config entry."""
        try:
            return await ws().call("config_entries/get_single", entry_id=entry_id)
        except Exception:
            entries = await ws().call("config_entries/get")
            for e in entries:
                if e.get("entry_id") == entry_id:
                    return e
            return {"error": "not_found"}

    @tool(mcp)
    async def delete_config_entry(entry_id: str) -> dict:
        """§4 Remove (uninstall) a config entry / integration."""
        return await ws().call("config_entries/remove", entry_id=entry_id)

    @tool(mcp)
    async def reload_config_entry(entry_id: str) -> dict:
        """§4 Reload a config entry."""
        return await ws().call("config_entries/reload", entry_id=entry_id)

    @tool(mcp)
    async def disable_config_entry(entry_id: str) -> dict:
        """§4 Disable a config entry."""
        return await ws().call("config_entries/disable",
                               entry_id=entry_id, disabled_by="user")

    @tool(mcp)
    async def enable_config_entry(entry_id: str) -> dict:
        """§4 Re-enable a config entry."""
        return await ws().call("config_entries/disable",
                               entry_id=entry_id, disabled_by=None)

    @tool(mcp)
    async def update_config_entry(entry_id: str, patch: dict) -> dict:
        """§4 Update a config entry (title, data, options, pref_disable_*)."""
        return await ws().call("config_entries/update", entry_id=entry_id, **patch)

    @tool(mcp)
    async def start_config_flow(handler: str, show_advanced_options: bool = True) -> dict:
        """§4 Start a config flow for an integration handler (domain)."""
        return await ws().call("config_entries/flow/init", handler=handler,
                               show_advanced_options=show_advanced_options)

    @tool(mcp)
    async def progress_config_flow(flow_id: str, user_input: dict) -> dict:
        """§4 Progress a config flow with user input."""
        return await ws().call("config_entries/flow/configure",
                               flow_id=flow_id, user_input=user_input)

    @tool(mcp)
    async def list_config_flows_in_progress() -> list:
        """§4 List config flows currently in progress."""
        return await ws().call("config_entries/flow/progress")

    @tool(mcp)
    async def abort_config_flow(flow_id: str) -> dict:
        """§4 Abort a config flow."""
        return await ws().call("config_entries/flow/abort", flow_id=flow_id)

    @tool(mcp)
    async def start_options_flow(handler: str) -> dict:
        """§4 Start an options flow for a config entry id (handler)."""
        return await ws().call("config_entries/options/flow/init", handler=handler)

    @tool(mcp)
    async def progress_options_flow(flow_id: str, user_input: dict) -> dict:
        """§4 Progress an options flow."""
        return await ws().call("config_entries/options/flow/configure",
                               flow_id=flow_id, user_input=user_input)

    @tool(mcp)
    async def list_subentries(entry_id: str) -> list:
        """§4 List subentries of a config entry."""
        return await ws().call("config_entries/subentries/list", entry_id=entry_id)

    @tool(mcp)
    async def delete_subentry(entry_id: str, subentry_id: str) -> dict:
        """§4 Delete a subentry."""
        return await ws().call("config_entries/subentries/delete",
                               entry_id=entry_id, subentry_id=subentry_id)

    return 15
