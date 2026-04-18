"""§60 Legal-edge tools.

Flagged as RIPA / Wireless Telegraphy Act / Computer Misuse Act / PSD2
sensitive in the spec. Implemented as raw pass-throughs; the caller is
responsible for the legality of how they're used.
"""
from __future__ import annotations

from typing import Any

import httpx

from .. import shell as _shell
from ._helpers import tool


async def _hit(method: str, url: str, **kw) -> Any:
    async with httpx.AsyncClient(timeout=120.0) as c:
        r = await c.request(method.upper(), url, **kw)
        try: body = r.json()
        except Exception: body = r.text
        return {"status_code": r.status_code, "body": body}


def register(mcp) -> int:

    @tool(mcp)
    async def neighbour_signal_scan(seconds: float = 30.0,
                                      interface: str = "wlan0",
                                      output_path: str = "/share/wifi_scan.csv") -> Any:
        """§60 airodump-ng style passive Wi-Fi probe scan (legality varies by jurisdiction)."""
        return await _shell.shell_exec(
            f"timeout {seconds} airodump-ng --output-format csv "
            f"-w {output_path} {interface}", timeout=seconds + 30)

    @tool(mcp)
    async def neighbour_rf_scan(frequency_hz: int, seconds: float = 30.0) -> Any:
        """§60 RTL-SDR passive RF capture in a frequency band."""
        return await _shell.shell_exec(
            f"timeout {seconds} rtl_433 -f {frequency_hz} -F json",
            timeout=seconds + 10)

    @tool(mcp)
    async def open_banking_payment(method: str, url: str,
                                     access_token: str,
                                     consent_id: str,
                                     payload: dict) -> Any:
        """§60 PSD2 PIS payment initiation. Caller MUST hold valid SCA-completed consent."""
        return await _hit(method, url,
                           headers={"Authorization": f"Bearer {access_token}",
                                     "x-idempotency-key": consent_id,
                                     "x-fapi-financial-id": consent_id},
                           json=payload)

    @tool(mcp)
    async def social_media_post(provider: str, method: str, url: str,
                                  access_token: str,
                                  json_body: dict | None = None,
                                  data: dict | None = None) -> Any:
        """§60 Post to Twitter/X / Facebook / Instagram / LinkedIn / Threads / Mastodon."""
        return await _hit(method, url,
                           headers={"Authorization": f"Bearer {access_token}"},
                           json=json_body, data=data)

    @tool(mcp)
    async def autonomous_purchase_request(vendor: str, method: str, url: str,
                                            access_token: str | None = None,
                                            json_body: dict | None = None,
                                            cookies: dict | None = None) -> Any:
        """§60 Submit a purchase request to a vendor checkout API."""
        h = {"Authorization": f"Bearer {access_token}"} if access_token else {}
        return await _hit(method, url, headers=h, json=json_body, cookies=cookies)

    @tool(mcp)
    async def legal_form_submit(method: str, url: str,
                                  cookies: dict | None = None,
                                  data: dict | None = None,
                                  json_body: dict | None = None) -> Any:
        """§60 Submit forms to HMRC / DVLA / Companies House / GOV.UK endpoints."""
        return await _hit(method, url, cookies=cookies, data=data, json=json_body)

    return 6
