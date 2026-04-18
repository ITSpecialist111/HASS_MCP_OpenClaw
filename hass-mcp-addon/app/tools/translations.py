"""§37 Translation / i18n."""
from __future__ import annotations

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def list_translations(language: str = "en", category: str = "state") -> dict:
        """§37 Get HA frontend translations for a language."""
        return await ws().call("frontend/get_translations",
                                language=language, category=category)

    @tool(mcp)
    async def set_language(user_id: str, language: str) -> dict:
        """§37 Set a user's frontend language preference."""
        return await ws().call("frontend/set_user_data", user_id=user_id,
                                key="language", value=language)

    @tool(mcp)
    async def get_user_language(user_id: str) -> dict:
        """§37 Get a user's stored frontend language."""
        return await ws().call("frontend/get_user_data", user_id=user_id, key="language")

    return 3
