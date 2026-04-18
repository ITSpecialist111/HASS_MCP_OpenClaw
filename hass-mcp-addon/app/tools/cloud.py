"""§31 Cloud / Nabu Casa / Cloudflared."""
from __future__ import annotations

from typing import Any

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def cloud_status() -> Any:
        """§31 Nabu Casa cloud status."""
        return await ws().call("cloud/status")

    @tool(mcp)
    async def cloud_login(email: str, password: str) -> Any:
        """§31 Login to Nabu Casa."""
        return await ws().call("cloud/login", email=email, password=password)

    @tool(mcp)
    async def cloud_logout() -> Any:
        """§31 Logout."""
        return await ws().call("cloud/logout")

    @tool(mcp)
    async def cloud_register(email: str, password: str) -> Any:
        """§31 Register a new Nabu Casa account."""
        return await ws().call("cloud/register", email=email, password=password)

    @tool(mcp)
    async def cloud_subscription_info() -> Any:
        """§31 Subscription info."""
        return await ws().call("cloud/subscription")

    @tool(mcp)
    async def cloud_remote_connect() -> Any:
        """§31 Connect remote UI."""
        return await ws().call("cloud/remote/connect")

    @tool(mcp)
    async def cloud_remote_disconnect() -> Any:
        """§31 Disconnect remote UI."""
        return await ws().call("cloud/remote/disconnect")

    @tool(mcp)
    async def cloud_alexa_sync() -> Any:
        """§31 Sync Alexa."""
        return await ws().call("cloud/alexa/sync")

    @tool(mcp)
    async def cloud_google_sync() -> Any:
        """§31 Sync Google Assistant."""
        return await ws().call("cloud/google_assistant/sync")

    @tool(mcp)
    async def cloud_tts_voices() -> Any:
        """§31 List Nabu Casa TTS voices."""
        return await ws().call("cloud/tts/info")

    @tool(mcp)
    async def cloudflared_tunnel_list() -> Any:
        """§31 List cloudflared tunnels via the addon (requires cloudflared add-on)."""
        from .. import supervisor_client as sup
        try:
            return await sup.get("/addons/8099_cloudflared/info")
        except Exception as e:
            return {"error": str(e)}

    @tool(mcp)
    async def cloudflared_tunnel_create(name: str, hostname: str, service: str) -> Any:
        """§31 Create a cloudflared tunnel (delegates to the add-on; placeholder)."""
        return {"note": "configure cloudflared add-on via set_addon_options",
                "name": name, "hostname": hostname, "service": service}

    return 12
