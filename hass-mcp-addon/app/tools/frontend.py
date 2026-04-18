"""§9 Frontend / themes / panels."""
from __future__ import annotations

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def list_themes() -> dict:
        """§9 List installed themes."""
        return await ws().call("frontend/get_themes")

    @tool(mcp)
    async def set_theme(name: str, mode: str = "light") -> dict:
        """§9 Set the global theme."""
        return await ws().call("call_service", domain="frontend", service="set_theme",
                                service_data={"name": name, "mode": mode})

    @tool(mcp)
    async def reload_themes() -> dict:
        """§9 Reload themes from disk."""
        return await ws().call("call_service", domain="frontend", service="reload_themes")

    @tool(mcp)
    async def set_user_theme(user_id: str, theme: str) -> dict:
        """§9 Set theme preference for a user (frontend storage)."""
        return await ws().call("frontend/set_user_data",
                                user_id=user_id, key="theme", value=theme)

    @tool(mcp)
    async def list_panels() -> dict:
        """§9 List sidebar panels."""
        return await ws().call("get_panels")

    @tool(mcp)
    async def remove_panel(frontend_url_path: str) -> dict:
        """§9 Remove a sidebar panel via service."""
        return await ws().call("call_service", domain="frontend", service="reload_themes",
                                service_data={"frontend_url_path": frontend_url_path})

    return 6
