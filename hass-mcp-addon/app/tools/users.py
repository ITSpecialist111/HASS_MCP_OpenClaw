"""§14 Users / auth / persons / tokens."""
from __future__ import annotations

from typing import Any

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def list_users() -> list:
        """§14 List all HA users."""
        return await ws().call("config/auth/list")

    @tool(mcp)
    async def create_user(name: str, group_ids: list[str] | None = None,
                           local_only: bool = False) -> dict:
        """§14 Create a HA user."""
        kwargs: dict[str, Any] = {"name": name, "local_only": local_only}
        if group_ids: kwargs["group_ids"] = group_ids
        return await ws().call("config/auth/create", **kwargs)

    @tool(mcp)
    async def update_user(user_id: str, patch: dict) -> dict:
        """§14 Update a user (name, group_ids, is_active, local_only)."""
        return await ws().call("config/auth/update", user_id=user_id, **patch)

    @tool(mcp)
    async def delete_user(user_id: str) -> dict:
        """§14 Delete a user."""
        return await ws().call("config/auth/delete", user_id=user_id)

    @tool(mcp)
    async def change_user_password(user_id: str, password: str) -> dict:
        """§14 Change a user's password (homeassistant auth provider)."""
        return await ws().call("config/auth_provider/homeassistant/admin_change_password",
                                user_id=user_id, password=password)

    @tool(mcp)
    async def list_auth_providers() -> dict:
        """§14 List configured auth providers."""
        return await ws().call("auth/providers")

    @tool(mcp)
    async def list_refresh_tokens() -> list:
        """§14 List refresh tokens for the current user."""
        return await ws().call("auth/refresh_tokens")

    @tool(mcp)
    async def revoke_refresh_token(token_id: str) -> dict:
        """§14 Revoke a refresh token."""
        return await ws().call("auth/delete_refresh_token", refresh_token_id=token_id)

    @tool(mcp)
    async def create_long_lived_token(client_name: str = "MCP Server",
                                       lifespan_days: int = 3650) -> dict:
        """§14 Create a long-lived access token."""
        return await ws().call("auth/long_lived_access_token",
                                client_name=client_name, lifespan=lifespan_days)

    @tool(mcp)
    async def list_persons_full() -> list:
        """§14 List all persons."""
        return await ws().call("person/list")

    @tool(mcp)
    async def create_person(name: str, user_id: str | None = None,
                              device_trackers: list[str] | None = None) -> dict:
        """§14 Create a person."""
        kwargs: dict[str, Any] = {"name": name}
        if user_id: kwargs["user_id"] = user_id
        if device_trackers: kwargs["device_trackers"] = device_trackers
        return await ws().call("person/create", **kwargs)

    @tool(mcp)
    async def update_person(person_id: str, patch: dict) -> dict:
        """§14 Update a person."""
        return await ws().call("person/update", person_id=person_id, **patch)

    @tool(mcp)
    async def delete_person(person_id: str) -> dict:
        """§14 Delete a person."""
        return await ws().call("person/delete", person_id=person_id)

    return 13
