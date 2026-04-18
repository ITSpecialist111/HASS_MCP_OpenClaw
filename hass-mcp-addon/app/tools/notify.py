"""§20 Notifications."""
from __future__ import annotations

from typing import Any

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def list_notify_services() -> list:
        """§20 All notify.* services available."""
        services = await ws().call("get_services")
        return list((services or {}).get("notify", {}).keys())

    @tool(mcp)
    async def notify_send(service: str, message: str, title: str | None = None,
                           target: Any = None, data: dict | None = None) -> dict:
        """§20 Send via any notify.* service."""
        payload: dict[str, Any] = {"message": message}
        if title: payload["title"] = title
        if target is not None: payload["target"] = target
        if data: payload["data"] = data
        return await ws().call("call_service", domain="notify",
                                service=service, service_data=payload)

    @tool(mcp)
    async def persistent_notification_create(message: str, title: str | None = None,
                                               notification_id: str | None = None) -> dict:
        """§20 Create a persistent notification."""
        data: dict[str, Any] = {"message": message}
        if title: data["title"] = title
        if notification_id: data["notification_id"] = notification_id
        return await ws().call("call_service", domain="persistent_notification",
                                service="create", service_data=data)

    @tool(mcp)
    async def persistent_notification_dismiss(notification_id: str) -> dict:
        """§20 Dismiss a persistent notification."""
        return await ws().call("call_service", domain="persistent_notification",
                                service="dismiss",
                                service_data={"notification_id": notification_id})

    @tool(mcp)
    async def persistent_notification_dismiss_all() -> dict:
        """§20 Dismiss all persistent notifications."""
        return await ws().call("call_service", domain="persistent_notification",
                                service="dismiss_all")

    @tool(mcp)
    async def companion_app_notification(service: str, message: str,
                                          title: str | None = None,
                                          actions: list[dict] | None = None,
                                          image_url: str | None = None,
                                          critical: bool = False,
                                          channel: str | None = None,
                                          extra: dict | None = None) -> dict:
        """§20 Rich mobile_app push (actions, image, critical, channel)."""
        data: dict[str, Any] = {}
        if actions: data["actions"] = actions
        if image_url: data["image"] = image_url
        if critical:
            data["push"] = {"sound": {"name": "default", "critical": 1, "volume": 1.0}}
        if channel: data["channel"] = channel
        if extra: data.update(extra)
        payload: dict[str, Any] = {"message": message}
        if title: payload["title"] = title
        if data: payload["data"] = data
        return await ws().call("call_service", domain="notify",
                                service=service, service_data=payload)

    return 6
