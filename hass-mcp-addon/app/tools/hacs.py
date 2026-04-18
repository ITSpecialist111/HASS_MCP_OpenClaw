"""§30 HACS (via service domain hacs.*)."""
from __future__ import annotations

from .. import hass
from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    async def _hacs_loaded() -> bool:
        try:
            comps = await hass.get_components()
            return "hacs" in comps
        except Exception:
            return False

    @tool(mcp)
    async def hacs_list_repositories() -> dict:
        """§30 List HACS repositories (via WS hacs/repositories if available)."""
        if not await _hacs_loaded():
            return {"error": "HACS not installed"}
        try:
            return await ws().call("hacs/repositories")
        except Exception as e:
            return {"error": str(e)}

    @tool(mcp)
    async def hacs_install_repository(repository: str, version: str | None = None) -> dict:
        """§30 Install a HACS repository."""
        data = {"repository": repository}
        if version: data["version"] = version
        return await ws().call("call_service", domain="hacs",
                                service="install", service_data=data)

    @tool(mcp)
    async def hacs_remove_repository(repository: str) -> dict:
        """§30 Remove a HACS repository."""
        return await ws().call("call_service", domain="hacs", service="uninstall",
                                service_data={"repository": repository})

    @tool(mcp)
    async def hacs_update_repository(repository: str) -> dict:
        """§30 Update a HACS repository."""
        return await ws().call("call_service", domain="hacs", service="update",
                                service_data={"repository": repository})

    @tool(mcp)
    async def hacs_update_all() -> dict:
        """§30 Update all HACS repositories."""
        return await ws().call("call_service", domain="hacs", service="update_all")

    @tool(mcp)
    async def hacs_search(query: str, category: str | None = None) -> dict:
        """§30 Search HACS (best-effort via WS)."""
        kwargs = {"query": query}
        if category: kwargs["category"] = category
        try:
            return await ws().call("hacs/search", **kwargs)
        except Exception:
            return {"error": "hacs/search WS endpoint unavailable"}

    @tool(mcp)
    async def hacs_set_branch(repository: str, branch: str) -> dict:
        """§30 Pin a repo to a branch."""
        return await ws().call("call_service", domain="hacs", service="set_branch",
                                service_data={"repository": repository, "branch": branch})

    return 7
