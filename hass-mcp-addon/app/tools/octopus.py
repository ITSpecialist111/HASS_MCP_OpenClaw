"""§34 Octopus Energy (HACS integration services)."""
from __future__ import annotations

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def octopus_force_refresh() -> dict:
        """§34 Refresh Octopus data."""
        return await ws().call("call_service", domain="octopus_energy",
                                service="refresh_data")

    @tool(mcp)
    async def octopus_get_intelligent_dispatches(account_id: str) -> dict:
        """§34 Get planned smart-charge dispatches."""
        return await ws().call("call_service", domain="octopus_energy",
                                service="get_intelligent_dispatches",
                                service_data={"account_id": account_id},
                                return_response=True)

    @tool(mcp)
    async def octopus_register_rates(mpan: str) -> dict:
        """§34 Register rates for an MPAN/MPRN."""
        return await ws().call("call_service", domain="octopus_energy",
                                service="register_rate_weightings",
                                service_data={"mpan": mpan})

    @tool(mcp)
    async def octopus_purge_invalid_external_statistic_ids() -> dict:
        """§34 Purge invalid external statistic IDs."""
        return await ws().call("call_service", domain="octopus_energy",
                                service="purge_invalid_external_statistic_ids")

    return 4
