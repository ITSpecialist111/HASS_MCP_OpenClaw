"""§10 Recorder / history / statistics."""
from __future__ import annotations

from typing import Any

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def recorder_info() -> dict:
        """§10 Recorder integration info."""
        return await ws().call("recorder/info")

    @tool(mcp)
    async def recorder_purge(keep_days: int = 10, repack: bool = False,
                              apply_filter: bool = False) -> dict:
        """§10 Purge recorder data older than keep_days."""
        return await ws().call("call_service", domain="recorder", service="purge",
                                service_data={"keep_days": keep_days, "repack": repack,
                                              "apply_filter": apply_filter})

    @tool(mcp)
    async def recorder_purge_entities(entity_id: list[str] | None = None,
                                       domains: list[str] | None = None,
                                       entity_globs: list[str] | None = None) -> dict:
        """§10 Purge specific entities from recorder."""
        data: dict[str, Any] = {}
        if entity_id: data["entity_id"] = entity_id
        if domains: data["domains"] = domains
        if entity_globs: data["entity_globs"] = entity_globs
        return await ws().call("call_service", domain="recorder",
                                service="purge_entities", service_data=data)

    @tool(mcp)
    async def disable_recording() -> dict:
        """§10 Pause recorder."""
        return await ws().call("call_service", domain="recorder", service="disable")

    @tool(mcp)
    async def enable_recording() -> dict:
        """§10 Resume recorder."""
        return await ws().call("call_service", domain="recorder", service="enable")

    @tool(mcp)
    async def list_statistics(statistic_type: str | None = None) -> list:
        """§10 List statistic_ids."""
        kwargs = {"statistic_type": statistic_type} if statistic_type else {}
        return await ws().call("recorder/list_statistic_ids", **kwargs)

    @tool(mcp)
    async def get_statistics(start_time: str, statistic_ids: list[str],
                              period: str = "hour", end_time: str | None = None) -> dict:
        """§10 Statistics during a period (period: 5minute|hour|day|week|month)."""
        kwargs: dict[str, Any] = {"start_time": start_time, "statistic_ids": statistic_ids,
                                   "period": period}
        if end_time: kwargs["end_time"] = end_time
        return await ws().call("recorder/statistics_during_period", **kwargs)

    @tool(mcp)
    async def clear_statistics(statistic_ids: list[str]) -> dict:
        """§10 Clear stats for given statistic_ids."""
        return await ws().call("recorder/clear_statistics", statistic_ids=statistic_ids)

    @tool(mcp)
    async def update_statistics_metadata(statistic_id: str, unit_of_measurement: str | None = None,
                                          new_statistic_id: str | None = None) -> dict:
        """§10 Update statistic metadata."""
        kwargs: dict[str, Any] = {"statistic_id": statistic_id}
        if unit_of_measurement is not None: kwargs["unit_of_measurement"] = unit_of_measurement
        if new_statistic_id is not None: kwargs["new_statistic_id"] = new_statistic_id
        return await ws().call("recorder/update_statistics_metadata", **kwargs)

    @tool(mcp)
    async def import_statistics(metadata: dict, stats: list) -> dict:
        """§10 Import statistics."""
        return await ws().call("recorder/import_statistics",
                                metadata=metadata, stats=stats)

    @tool(mcp)
    async def adjust_sum_statistics(statistic_id: str, start_time: str,
                                     adjustment: float, adjustment_unit_of_measurement: str) -> dict:
        """§10 Adjust a sum statistic."""
        return await ws().call("recorder/adjust_sum_statistics",
                                statistic_id=statistic_id, start_time=start_time,
                                adjustment=adjustment,
                                adjustment_unit_of_measurement=adjustment_unit_of_measurement)

    return 11
