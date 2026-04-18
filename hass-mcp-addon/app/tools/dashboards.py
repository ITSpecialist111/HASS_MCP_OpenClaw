"""§8 Lovelace dashboards."""
from __future__ import annotations

from typing import Any

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def list_dashboards_full() -> list:
        """§8 List all Lovelace dashboards."""
        return await ws().call("lovelace/dashboards/list")

    @tool(mcp)
    async def create_dashboard(url_path: str, title: str, icon: str | None = None,
                                show_in_sidebar: bool = True,
                                require_admin: bool = False) -> dict:
        """§8 Create a new dashboard."""
        kwargs = {"url_path": url_path, "title": title,
                  "show_in_sidebar": show_in_sidebar, "require_admin": require_admin}
        if icon: kwargs["icon"] = icon
        return await ws().call("lovelace/dashboards/create", **kwargs)

    @tool(mcp)
    async def update_dashboard(dashboard_id: str, patch: dict) -> dict:
        """§8 Update dashboard config."""
        return await ws().call("lovelace/dashboards/update",
                                dashboard_id=dashboard_id, **patch)

    @tool(mcp)
    async def delete_dashboard(dashboard_id: str) -> dict:
        """§8 Delete a dashboard."""
        return await ws().call("lovelace/dashboards/delete", dashboard_id=dashboard_id)

    @tool(mcp)
    async def get_dashboard_config_full(url_path: str | None = None) -> dict:
        """§8 Get dashboard config (None = default)."""
        kwargs = {"url_path": url_path} if url_path else {}
        return await ws().call("lovelace/config", **kwargs)

    @tool(mcp)
    async def set_dashboard_config(config: dict, url_path: str | None = None) -> dict:
        """§8 Replace dashboard config."""
        kwargs: dict[str, Any] = {"config": config}
        if url_path: kwargs["url_path"] = url_path
        return await ws().call("lovelace/config/save", **kwargs)

    @tool(mcp)
    async def list_resources() -> list:
        """§8 List Lovelace resources (JS modules/CSS)."""
        return await ws().call("lovelace/resources")

    @tool(mcp)
    async def create_resource(url: str, res_type: str = "module") -> dict:
        """§8 Add a Lovelace resource."""
        return await ws().call("lovelace/resources/create", url=url, res_type=res_type)

    @tool(mcp)
    async def update_resource(resource_id: str, url: str, res_type: str = "module") -> dict:
        """§8 Update a Lovelace resource."""
        return await ws().call("lovelace/resources/update",
                                resource_id=resource_id, url=url, res_type=res_type)

    @tool(mcp)
    async def delete_resource(resource_id: str) -> dict:
        """§8 Delete a Lovelace resource."""
        return await ws().call("lovelace/resources/delete", resource_id=resource_id)

    @tool(mcp)
    async def add_card_to_view(card: dict, view_index: int = 0,
                                url_path: str | None = None) -> dict:
        """§8 Append a card to a view of a dashboard."""
        cfg = await ws().call("lovelace/config",
                               **({"url_path": url_path} if url_path else {}))
        views = cfg.setdefault("views", [{}])
        view = views[view_index]
        view.setdefault("cards", []).append(card)
        kwargs: dict[str, Any] = {"config": cfg}
        if url_path: kwargs["url_path"] = url_path
        return await ws().call("lovelace/config/save", **kwargs)

    return 11
