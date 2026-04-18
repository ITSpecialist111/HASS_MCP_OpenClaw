"""§11 Energy dashboard."""
from __future__ import annotations

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def get_energy_prefs() -> dict:
        """§11 Get energy dashboard preferences."""
        return await ws().call("energy/get_prefs")

    @tool(mcp)
    async def save_energy_prefs(prefs: dict) -> dict:
        """§11 Save energy dashboard preferences."""
        return await ws().call("energy/save_prefs", **prefs)

    @tool(mcp)
    async def validate_energy_prefs() -> dict:
        """§11 Validate energy preferences."""
        return await ws().call("energy/validate")

    @tool(mcp)
    async def get_energy_solar_forecast() -> dict:
        """§11 Solar forecast (sum across configured forecasts)."""
        return await ws().call("energy/solar_forecast")

    @tool(mcp)
    async def get_energy_fossil_consumption(start_time: str, end_time: str | None = None,
                                             period: str = "hour") -> dict:
        """§11 Fossil energy consumption summary."""
        kwargs = {"start_time": start_time, "period": period}
        if end_time: kwargs["end_time"] = end_time
        return await ws().call("energy/fossil_energy_consumption", **kwargs)

    return 5
