"""§41 — Raw escape hatches: ws_raw, rest_raw, supervisor_raw, service_call_raw."""
from __future__ import annotations

from typing import Any

import httpx

from .. import config as cfg
from .. import supervisor_client as sup
from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    @tool(mcp)
    async def ws_raw(message: dict, timeout: float = 30.0) -> dict:
        """§41 Send a raw WebSocket message to HA Core. Returns the full response.
        Example: {"type": "config/area_registry/list"}.
        """
        return await get_ws().send(message, timeout=timeout)

    @tool(mcp)
    async def rest_raw(method: str, path: str,
                       json_body: dict | None = None,
                       params: dict | None = None) -> Any:
        """§41 Send an arbitrary REST request to HA Core /api/<path>."""
        url = f"{cfg.get_api_base()}{path if path.startswith('/') else '/' + path}"
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.request(method.upper(), url, headers=cfg.get_headers(),
                                json=json_body, params=params)
            r.raise_for_status()
            try:
                return r.json()
            except Exception:
                return {"text": r.text, "status_code": r.status_code}

    @tool(mcp)
    async def supervisor_raw(method: str, path: str,
                             json_body: dict | None = None,
                             params: dict | None = None) -> Any:
        """§41 Send an arbitrary REST request to Supervisor (path begins with /)."""
        return await sup.request(method, path, json=json_body, params=params)

    @tool(mcp)
    async def service_call_raw(domain: str, service: str,
                               service_data: dict | None = None,
                               target: dict | None = None,
                               return_response: bool = True) -> dict:
        """§41 Call any HA service via WebSocket with full target + return_response."""
        payload: dict[str, Any] = {
            "domain": domain, "service": service,
            "service_data": service_data or {},
            "return_response": return_response,
        }
        if target:
            payload["target"] = target
        return await get_ws().call("call_service", **payload)

    return 4
