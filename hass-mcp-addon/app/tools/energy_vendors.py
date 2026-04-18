"""§35 Energy / solar vendor convenience wrappers."""
from __future__ import annotations

from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    # ---- FoxESS Modbus ----
    @tool(mcp)
    async def foxess_force_poll(entry_id: str | None = None) -> dict:
        """§35 Force a FoxESS modbus refresh."""
        data = {"entry_id": entry_id} if entry_id else {}
        return await ws().call("call_service", domain="modbus",
                                service="restart", service_data=data)

    @tool(mcp)
    async def foxess_set_charge_period(start: str, end: str,
                                        config_entry: str | None = None) -> dict:
        """§35 Set FoxESS charge period times."""
        data: dict = {"start_time": start, "end_time": end}
        if config_entry: data["config_entry"] = config_entry
        return await ws().call("call_service", domain="foxess_modbus",
                                service="set_charge_period", service_data=data)

    @tool(mcp)
    async def foxess_set_min_soc(value: int) -> dict:
        """§35 Set Min SoC (0-100)."""
        return await ws().call("call_service", domain="number",
                                service="set_value",
                                service_data={"entity_id": "number.foxess_min_soc",
                                              "value": value})

    @tool(mcp)
    async def foxess_set_work_mode(mode: str) -> dict:
        """§35 Set FoxESS work mode (Self Use, Feed In First, Backup Mode)."""
        return await ws().call("call_service", domain="select",
                                service="select_option",
                                service_data={"entity_id": "select.foxess_work_mode",
                                              "option": mode})

    # ---- Zappi ----
    @tool(mcp)
    async def zappi_set_mode(serial: str, mode: str) -> dict:
        """§35 Set Zappi charge mode (Fast/Eco/Eco+/Stop)."""
        return await ws().call("call_service", domain="myenergi",
                                service="set_zappi_mode",
                                service_data={"serial": serial, "mode": mode})

    @tool(mcp)
    async def zappi_boost(serial: str, amount: float | None = None,
                            time: str | None = None) -> dict:
        """§35 Boost Zappi by amount or to a time."""
        data: dict = {"serial": serial}
        if amount is not None: data["amount"] = amount
        if time: data["time"] = time
        return await ws().call("call_service", domain="myenergi",
                                service="set_zappi_boost", service_data=data)

    @tool(mcp)
    async def zappi_set_charge_target(serial: str, kwh: float) -> dict:
        """§35 Set a kWh charge target."""
        return await ws().call("call_service", domain="myenergi",
                                service="set_zappi_charge_target",
                                service_data={"serial": serial, "amount": kwh})

    # ---- SAIC (MG cars) ----
    @tool(mcp)
    async def saic_force_refresh(vin: str) -> dict:
        """§35 Refresh SAIC MG vehicle data."""
        return await ws().call("call_service", domain="saic_ismart",
                                service="force_update", service_data={"vin": vin})

    @tool(mcp)
    async def saic_lock(vin: str) -> dict:
        """§35 Lock SAIC vehicle."""
        return await ws().call("call_service", domain="lock", service="lock",
                                service_data={"entity_id": f"lock.saic_{vin}_door_lock"})

    @tool(mcp)
    async def saic_unlock(vin: str) -> dict:
        """§35 Unlock SAIC vehicle."""
        return await ws().call("call_service", domain="lock", service="unlock",
                                service_data={"entity_id": f"lock.saic_{vin}_door_lock"})

    @tool(mcp)
    async def saic_climate_on(vin: str, temperature: float = 21.0) -> dict:
        """§35 Start SAIC climate."""
        return await ws().call("call_service", domain="climate",
                                service="set_temperature",
                                service_data={"entity_id": f"climate.saic_{vin}",
                                              "temperature": temperature})

    @tool(mcp)
    async def saic_charge_now(vin: str) -> dict:
        """§35 Start charging."""
        return await ws().call("call_service", domain="saic_ismart",
                                service="start_charge", service_data={"vin": vin})

    @tool(mcp)
    async def saic_charge_stop(vin: str) -> dict:
        """§35 Stop charging."""
        return await ws().call("call_service", domain="saic_ismart",
                                service="stop_charge", service_data={"vin": vin})

    return 13
