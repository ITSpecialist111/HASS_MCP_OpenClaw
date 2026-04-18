"""§52 Cloud / SaaS backends — generic OAuth/REST relays.

These are deliberately schema-free pass-throughs because each vendor's
auth dance differs. Authentication tokens are held in /data/saas_creds.json.
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx

from ._helpers import tool

_CREDS = "/data/saas_creds.json"


def _load_creds() -> dict:
    if not os.path.exists(_CREDS): return {}
    try:
        with open(_CREDS) as f: return json.load(f)
    except Exception:
        return {}


def _save_creds(d: dict) -> None:
    os.makedirs(os.path.dirname(_CREDS), exist_ok=True)
    with open(_CREDS, "w") as f: json.dump(d, f)
    os.chmod(_CREDS, 0o600)


async def _hit(method: str, url: str, **kw) -> Any:
    async with httpx.AsyncClient(timeout=120.0) as c:
        r = await c.request(method.upper(), url, **kw)
        try: body = r.json()
        except Exception: body = r.text
        return {"status_code": r.status_code, "body": body}


def register(mcp) -> int:

    @tool(mcp)
    async def saas_set_credential(name: str, value: dict) -> dict:
        """§52 Stash a vendor credential blob (token, refresh, client_id, etc.)."""
        c = _load_creds(); c[name] = value; _save_creds(c)
        return {"name": name, "stored": True, "keys": list(value.keys())}

    @tool(mcp)
    async def saas_get_credential(name: str) -> dict:
        """§52 Read a stashed credential (full plaintext)."""
        return _load_creds().get(name, {"error": "not found"})

    @tool(mcp)
    async def saas_list_credentials() -> list:
        """§52 List credential names."""
        return list(_load_creds().keys())

    @tool(mcp)
    async def saas_delete_credential(name: str) -> dict:
        """§52 Remove a credential."""
        c = _load_creds(); v = c.pop(name, None); _save_creds(c)
        return {"removed": v is not None}

    @tool(mcp)
    async def octopus_account_request(method: str, path: str,
                                        api_key: str | None = None) -> Any:
        """§52 Octopus Energy REST (https://api.octopus.energy)."""
        creds = _load_creds().get("octopus", {})
        key = api_key or creds.get("api_key")
        return await _hit(method, f"https://api.octopus.energy{path}",
                           auth=(key, "") if key else None)

    @tool(mcp)
    async def google_workspace_request(method: str, url: str,
                                         access_token: str | None = None,
                                         json_body: dict | None = None,
                                         params: dict | None = None) -> Any:
        """§52 Google Workspace / Gmail / Calendar / Drive / Photos call.
        URL is fully qualified (e.g. https://www.googleapis.com/...)."""
        tok = access_token or _load_creds().get("google", {}).get("access_token")
        h = {"Authorization": f"Bearer {tok}"} if tok else {}
        return await _hit(method, url, headers=h, json=json_body, params=params)

    @tool(mcp)
    async def apple_icloud_request(method: str, url: str,
                                     cookies: dict | None = None,
                                     json_body: dict | None = None) -> Any:
        """§52 iCloud private endpoints — caller must supply session cookies."""
        c = cookies or _load_creds().get("icloud", {}).get("cookies")
        return await _hit(method, url, cookies=c, json=json_body)

    @tool(mcp)
    async def microsoft_graph_request(method: str, path: str,
                                        access_token: str | None = None,
                                        json_body: dict | None = None,
                                        params: dict | None = None) -> Any:
        """§52 Microsoft Graph (https://graph.microsoft.com/v1.0)."""
        tok = access_token or _load_creds().get("microsoft", {}).get("access_token")
        return await _hit(method, f"https://graph.microsoft.com/v1.0{path}",
                           headers={"Authorization": f"Bearer {tok}"} if tok else {},
                           json=json_body, params=params)

    @tool(mcp)
    async def amazon_alexa_request(method: str, url: str,
                                     cookies: dict | None = None,
                                     json_body: dict | None = None) -> Any:
        """§52 Alexa private REST (alexa.amazon.co.uk) — needs cookie jar."""
        c = cookies or _load_creds().get("alexa", {}).get("cookies")
        return await _hit(method, url, cookies=c, json=json_body)

    @tool(mcp)
    async def music_service_request(service: str, method: str, url: str,
                                      access_token: str | None = None,
                                      json_body: dict | None = None) -> Any:
        """§52 Spotify / YouTube Music / Tidal / Apple Music / Deezer pass-through."""
        tok = access_token or _load_creds().get(service, {}).get("access_token")
        return await _hit(method, url,
                           headers={"Authorization": f"Bearer {tok}"} if tok else {},
                           json=json_body)

    @tool(mcp)
    async def appliance_account_request(vendor: str, method: str, url: str,
                                          access_token: str | None = None,
                                          json_body: dict | None = None) -> Any:
        """§52 SmartThings / LG ThinQ / Bosch HomeConnect / Miele etc."""
        tok = access_token or _load_creds().get(vendor, {}).get("access_token")
        return await _hit(method, url,
                           headers={"Authorization": f"Bearer {tok}"} if tok else {},
                           json=json_body)

    @tool(mcp)
    async def vehicle_account_request(vendor: str, method: str, url: str,
                                        access_token: str | None = None,
                                        json_body: dict | None = None) -> Any:
        """§52 Tesla / Porsche / SAIC owner-account pass-through."""
        tok = access_token or _load_creds().get(vendor, {}).get("access_token")
        return await _hit(method, url,
                           headers={"Authorization": f"Bearer {tok}"} if tok else {},
                           json=json_body)

    @tool(mcp)
    async def camera_cloud_request(vendor: str, method: str, url: str,
                                     access_token: str | None = None,
                                     json_body: dict | None = None) -> Any:
        """§52 Ring / Arlo / Eufy account API pass-through."""
        tok = access_token or _load_creds().get(vendor, {}).get("access_token")
        return await _hit(method, url,
                           headers={"Authorization": f"Bearer {tok}"} if tok else {},
                           json=json_body)

    @tool(mcp)
    async def frigate_plus_request(method: str, path: str,
                                     api_key: str | None = None,
                                     json_body: dict | None = None) -> Any:
        """§52 Frigate+ (https://api.frigate.video)."""
        key = api_key or _load_creds().get("frigate_plus", {}).get("api_key")
        return await _hit(method, f"https://api.frigate.video{path}",
                           headers={"Authorization": f"Bearer {key}"} if key else {},
                           json=json_body)

    @tool(mcp)
    async def llm_provider_billing(provider: str, method: str, url: str,
                                     api_key: str | None = None,
                                     json_body: dict | None = None) -> Any:
        """§52 OpenAI / Anthropic / Google AI billing & key mgmt."""
        key = api_key or _load_creds().get(provider, {}).get("api_key")
        h = {}
        if provider == "openai" and key: h["Authorization"] = f"Bearer {key}"
        elif provider == "anthropic" and key: h["x-api-key"] = key
        elif key: h["Authorization"] = f"Bearer {key}"
        return await _hit(method, url, headers=h, json=json_body)

    return 15
