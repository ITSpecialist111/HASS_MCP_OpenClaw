"""§16 Radios: Zigbee2MQTT, Z-Wave JS, Matter, Thread."""
from __future__ import annotations

from typing import Any

from ..ws_client import get_ws
from ._helpers import tool


Z2M_PREFIX = "zigbee2mqtt"


async def _mqtt_pub(topic: str, payload: str = "", retain: bool = False):
    return await get_ws().call("call_service", domain="mqtt", service="publish",
                                service_data={"topic": topic, "payload": payload,
                                              "retain": retain})


def register(mcp) -> int:
    ws = get_ws

    # ---- Zigbee2MQTT (via MQTT requests) ----
    @tool(mcp)
    async def z2m_list_devices() -> dict:
        """§16.1 Request Z2M device list (publish to zigbee2mqtt/bridge/request/devices)."""
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/devices", "")

    @tool(mcp)
    async def z2m_rename_device(friendly_name: str, new_name: str) -> dict:
        """§16.1 Rename a Z2M device."""
        import json
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/device/rename",
                                json.dumps({"from": friendly_name, "to": new_name}))

    @tool(mcp)
    async def z2m_remove_device(friendly_name: str, force: bool = False) -> dict:
        """§16.1 Remove a Z2M device."""
        import json
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/device/remove",
                                json.dumps({"id": friendly_name, "force": force}))

    @tool(mcp)
    async def z2m_permit_join(value: bool = True, time: int = 254) -> dict:
        """§16.1 Permit join (pairing mode)."""
        import json
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/permit_join",
                                json.dumps({"value": value, "time": time}))

    @tool(mcp)
    async def z2m_set_value(friendly_name: str, payload: dict) -> dict:
        """§16.1 Publish to zigbee2mqtt/<friendly>/set."""
        import json
        return await _mqtt_pub(f"{Z2M_PREFIX}/{friendly_name}/set", json.dumps(payload))

    @tool(mcp)
    async def z2m_get_groups() -> dict:
        """§16.1 Request Z2M group list."""
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/groups", "")

    @tool(mcp)
    async def z2m_create_group(friendly_name: str, group_id: int | None = None) -> dict:
        """§16.1 Create a Z2M group."""
        import json
        body = {"friendly_name": friendly_name}
        if group_id is not None: body["id"] = group_id
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/group/add", json.dumps(body))

    @tool(mcp)
    async def z2m_delete_group(group: str) -> dict:
        """§16.1 Delete a group."""
        import json
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/group/remove",
                                json.dumps({"id": group}))

    @tool(mcp)
    async def z2m_add_to_group(group: str, device: str) -> dict:
        """§16.1 Add device to group."""
        import json
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/group/members/add",
                                json.dumps({"group": group, "device": device}))

    @tool(mcp)
    async def z2m_ota_check(friendly_name: str) -> dict:
        """§16.1 Check OTA update for a device."""
        import json
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/device/ota_update/check",
                                json.dumps({"id": friendly_name}))

    @tool(mcp)
    async def z2m_ota_update(friendly_name: str) -> dict:
        """§16.1 Trigger OTA update."""
        import json
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/device/ota_update/update",
                                json.dumps({"id": friendly_name}))

    @tool(mcp)
    async def z2m_bind(source: str, target: str, clusters: list[str] | None = None) -> dict:
        """§16.1 Bind two devices."""
        import json
        body: dict = {"from": source, "to": target}
        if clusters: body["clusters"] = clusters
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/device/bind", json.dumps(body))

    @tool(mcp)
    async def z2m_unbind(source: str, target: str) -> dict:
        """§16.1 Unbind two devices."""
        import json
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/device/unbind",
                                json.dumps({"from": source, "to": target}))

    @tool(mcp)
    async def z2m_network_map() -> dict:
        """§16.1 Request network map (graphviz/raw)."""
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/networkmap", "raw")

    @tool(mcp)
    async def z2m_health_check() -> dict:
        """§16.1 Health check."""
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/health_check", "")

    @tool(mcp)
    async def z2m_restart() -> dict:
        """§16.1 Restart Z2M bridge."""
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/restart", "")

    @tool(mcp)
    async def z2m_change_channel(channel: int) -> dict:
        """§16.1 Change Zigbee channel."""
        import json
        return await _mqtt_pub(f"{Z2M_PREFIX}/bridge/request/options",
                                json.dumps({"options": {"advanced": {"channel": channel}}}))

    # ---- Z-Wave JS ----
    @tool(mcp)
    async def zwave_network_status(entry_id: str) -> Any:
        """§16.2 Z-Wave network status."""
        return await ws().call("zwave_js/network_status", entry_id=entry_id)

    @tool(mcp)
    async def zwave_add_node(entry_id: str, secure: bool = True) -> Any:
        """§16.2 Begin inclusion."""
        return await ws().call("zwave_js/add_node", entry_id=entry_id,
                                inclusion_strategy=0 if secure else 3)

    @tool(mcp)
    async def zwave_stop_inclusion(entry_id: str) -> Any:
        """§16.2 Stop inclusion."""
        return await ws().call("zwave_js/stop_inclusion", entry_id=entry_id)

    @tool(mcp)
    async def zwave_remove_node(entry_id: str) -> Any:
        """§16.2 Begin exclusion."""
        return await ws().call("zwave_js/remove_node", entry_id=entry_id)

    @tool(mcp)
    async def zwave_node_status(device_id: str) -> Any:
        """§16.2 Node status."""
        return await ws().call("zwave_js/node_status", device_id=device_id)

    @tool(mcp)
    async def zwave_heal_network(entry_id: str) -> Any:
        """§16.2 Begin network heal."""
        return await ws().call("zwave_js/begin_healing_network", entry_id=entry_id)

    @tool(mcp)
    async def zwave_set_config_param(device_id: str, property_: int,
                                       value: int, endpoint: int = 0) -> Any:
        """§16.2 Set Z-Wave config parameter."""
        return await ws().call("zwave_js/set_config_parameter",
                                device_id=device_id, property=property_,
                                value=value, endpoint=endpoint)

    # ---- Matter ----
    @tool(mcp)
    async def matter_commission(code: str) -> Any:
        """§16.3 Commission a Matter device with setup code."""
        return await ws().call("matter/commission", code=code)

    @tool(mcp)
    async def matter_decommission(node_id: int) -> Any:
        """§16.3 Decommission Matter node."""
        return await ws().call("matter/remove_matter_fabric", node_id=node_id)

    @tool(mcp)
    async def matter_ping(node_id: int) -> Any:
        """§16.3 Ping Matter node."""
        return await ws().call("matter/ping_node", node_id=node_id)

    @tool(mcp)
    async def matter_set_attribute(node_id: int, endpoint_id: int,
                                    cluster_id: int, attribute: int, value) -> Any:
        """§16.3 Write attribute on Matter device."""
        return await ws().call("matter/set_attribute", node_id=node_id,
                                endpoint_id=endpoint_id, cluster_id=cluster_id,
                                attribute=attribute, value=value)

    # ---- Thread ----
    @tool(mcp)
    async def thread_list_datasets() -> Any:
        """§16.4 List Thread datasets."""
        return await ws().call("thread/list_datasets")

    @tool(mcp)
    async def thread_set_preferred(dataset_id: str) -> Any:
        """§16.4 Set preferred Thread dataset."""
        return await ws().call("thread/set_preferred_dataset", dataset_id=dataset_id)

    @tool(mcp)
    async def thread_add_dataset(source: str, tlv: str) -> Any:
        """§16.4 Add a Thread dataset."""
        return await ws().call("thread/add_dataset_tlv", source=source, tlv=tlv)

    @tool(mcp)
    async def thread_delete_dataset(dataset_id: str) -> Any:
        """§16.4 Delete a Thread dataset."""
        return await ws().call("thread/delete_dataset", dataset_id=dataset_id)

    return 27
