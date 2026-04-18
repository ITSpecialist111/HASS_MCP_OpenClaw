"""§27 Network / diagnostics."""
from __future__ import annotations

from typing import Any

import httpx

from .. import shell as _shell
from ._helpers import tool


def register(mcp) -> int:

    @tool(mcp)
    async def ping_host(host: str, count: int = 4) -> dict:
        """§27 Ping a host."""
        return await _shell.shell_exec(f"ping -c {count} {host}")

    @tool(mcp)
    async def traceroute(host: str) -> dict:
        """§27 Traceroute."""
        return await _shell.shell_exec(f"traceroute {host}", timeout=60.0)

    @tool(mcp)
    async def dns_resolve(host: str, type_: str = "A") -> dict:
        """§27 DNS lookup."""
        return await _shell.shell_exec(f"dig +short {host} {type_}")

    @tool(mcp)
    async def port_scan(host: str, ports: str = "1-1024") -> dict:
        """§27 Quick TCP port scan via nmap if available, else nc loop."""
        return await _shell.shell_exec(
            f"command -v nmap >/dev/null && nmap -p {ports} {host} || "
            f"for p in $(seq {ports.split('-')[0]} {ports.split('-')[-1]}); do "
            f"  (echo > /dev/tcp/{host}/$p) >/dev/null 2>&1 && echo \"$p open\"; "
            f"done", timeout=120.0)

    @tool(mcp)
    async def http_request(method: str, url: str,
                            headers: dict | None = None,
                            json_body: dict | None = None,
                            data: str | None = None) -> dict:
        """§27 Issue arbitrary HTTP from inside HA's network."""
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True, verify=False) as c:
            r = await c.request(method.upper(), url, headers=headers,
                                json=json_body, content=data)
            try:
                body: Any = r.json()
            except Exception:
                body = r.text[:10_000]
            return {"status_code": r.status_code, "headers": dict(r.headers),
                    "body": body}

    @tool(mcp)
    async def wake_on_lan(mac: str, broadcast: str = "255.255.255.255") -> dict:
        """§27 Send WOL magic packet (calls wake_on_lan service)."""
        from ..ws_client import get_ws
        return await get_ws().call("call_service", domain="wake_on_lan",
                                    service="send_magic_packet",
                                    service_data={"mac": mac, "broadcast_address": broadcast})

    @tool(mcp)
    async def ssh_exec(host: str, command: str,
                        username: str = "root", port: int = 22,
                        password: str | None = None,
                        key_filename: str | None = None) -> dict:
        """§27 Run a command on a remote host via SSH (paramiko)."""
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=username,
                        password=password, key_filename=key_filename, timeout=30)
        try:
            _stdin, stdout, stderr = client.exec_command(command, timeout=120)
            return {"stdout": stdout.read().decode(),
                    "stderr": stderr.read().decode(),
                    "rc": stdout.channel.recv_exit_status()}
        finally:
            client.close()

    @tool(mcp)
    async def arp_table() -> dict:
        """§27 Read ARP table."""
        return await _shell.shell_exec("ip neigh show || arp -a")

    @tool(mcp)
    async def network_speedtest() -> dict:
        """§27 Run speedtest-cli if installed, else iperf3 hint."""
        return await _shell.shell_exec(
            "command -v speedtest-cli >/dev/null && speedtest-cli --simple || "
            "echo 'speedtest-cli not installed; try: pip install speedtest-cli'",
            timeout=120.0)

    return 9
