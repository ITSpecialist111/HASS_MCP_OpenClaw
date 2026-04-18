"""§17 ESPHome (delegates to esphome service domain + dashboard add-on API)."""
from __future__ import annotations

from .. import shell as _shell
from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def esphome_list_devices() -> list:
        """§17 List devices known to ESPHome integration."""
        states = await ws().call("config/entity_registry/list")
        return [e for e in states if (e.get("platform") or "") == "esphome"]

    @tool(mcp)
    async def esphome_get_device_yaml(device: str) -> dict:
        """§17 Read /config/esphome/<device>.yaml."""
        path = f"/config/esphome/{device}.yaml"
        with open(path) as f:
            return {"path": path, "content": f.read()}

    @tool(mcp)
    async def esphome_set_device_yaml(device: str, yaml_content: str) -> dict:
        """§17 Write /config/esphome/<device>.yaml."""
        path = f"/config/esphome/{device}.yaml"
        with open(path, "w") as f:
            f.write(yaml_content)
        return {"path": path, "bytes": len(yaml_content)}

    @tool(mcp)
    async def esphome_compile(device: str) -> dict:
        """§17 esphome compile <device>.yaml (via shell, requires esphome CLI)."""
        return await _shell.shell_exec(f"esphome compile /config/esphome/{device}.yaml",
                                        timeout=600.0)

    @tool(mcp)
    async def esphome_upload(device: str) -> dict:
        """§17 esphome upload <device>.yaml (OTA)."""
        return await _shell.shell_exec(f"esphome upload /config/esphome/{device}.yaml",
                                        timeout=600.0)

    @tool(mcp)
    async def esphome_logs(device: str, timeout: float = 30.0) -> dict:
        """§17 Tail logs from esphome device (timeout-bounded)."""
        return await _shell.shell_exec(f"timeout {timeout} esphome logs /config/esphome/{device}.yaml",
                                        timeout=timeout + 10)

    @tool(mcp)
    async def esphome_validate(device: str) -> dict:
        """§17 esphome config (validate)."""
        return await _shell.shell_exec(f"esphome config /config/esphome/{device}.yaml")

    @tool(mcp)
    async def esphome_run(device: str) -> dict:
        """§17 esphome run = compile + upload + logs."""
        return await _shell.shell_exec(f"esphome run /config/esphome/{device}.yaml",
                                        timeout=900.0)

    return 8
