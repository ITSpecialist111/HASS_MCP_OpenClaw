"""§51 Network & infrastructure (router, DNS, DHCP, VPN, Cloudflare, NAS, hypervisors)."""
from __future__ import annotations

from typing import Any

import httpx

from .. import shell as _shell
from ._helpers import tool


async def _http(method: str, url: str, **kw) -> Any:
    async with httpx.AsyncClient(timeout=60.0, verify=kw.pop("verify", True)) as c:
        r = await c.request(method.upper(), url, **kw)
        try: body = r.json()
        except Exception: body = r.text
        return {"status_code": r.status_code, "body": body}


def register(mcp) -> int:

    # ---- Router (UniFi / OPNsense / pfSense / Mikrotik) ----
    @tool(mcp)
    async def router_request(base_url: str, method: str, path: str,
                              token: str | None = None,
                              auth_user: str | None = None,
                              auth_pass: str | None = None,
                              verify_tls: bool = False,
                              json_body: dict | None = None) -> Any:
        """§51 Generic router REST request (UniFi/OPNsense/pfSense/Mikrotik)."""
        headers = {}
        auth = None
        if token: headers["Authorization"] = f"Bearer {token}"
        if auth_user and auth_pass: auth = (auth_user, auth_pass)
        return await _http(method, f"{base_url.rstrip('/')}{path}",
                            headers=headers, auth=auth, json=json_body,
                            verify=verify_tls)

    @tool(mcp)
    async def router_ssh_exec(host: str, user: str, command: str,
                                password: str | None = None,
                                key_path: str | None = None,
                                port: int = 22) -> Any:
        """§51 SSH into router (Mikrotik/EdgeOS/OpenWRT) and run a command."""
        import paramiko, io
        cli = paramiko.SSHClient()
        cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        kw: dict = {"username": user, "port": port, "timeout": 15}
        if password: kw["password"] = password
        if key_path: kw["pkey"] = paramiko.RSAKey.from_private_key_file(key_path)
        cli.connect(host, **kw)
        try:
            _, stdout, stderr = cli.exec_command(command, timeout=120)
            return {"stdout": stdout.read().decode(errors="replace"),
                    "stderr": stderr.read().decode(errors="replace"),
                    "rc": stdout.channel.recv_exit_status()}
        finally:
            cli.close()

    # ---- DNS (AdGuard / Pi-hole / Technitium) ----
    @tool(mcp)
    async def dns_authority_request(base_url: str, method: str, path: str,
                                      auth_user: str | None = None,
                                      auth_pass: str | None = None,
                                      json_body: dict | None = None) -> Any:
        """§51 Generic AdGuard/Pi-hole/Technitium API call."""
        auth = (auth_user, auth_pass) if auth_user and auth_pass else None
        return await _http(method, f"{base_url.rstrip('/')}{path}",
                            auth=auth, json=json_body, verify=False)

    # ---- DHCP (typically through router_request) ----
    @tool(mcp)
    async def dhcp_lease_table() -> Any:
        """§51 Read /var/lib/misc/dnsmasq.leases or arp -a as a fallback."""
        for p in ("/var/lib/misc/dnsmasq.leases",
                   "/tmp/dhcp.leases",
                   "/etc/dhcp/dhcpd.leases"):
            r = await _shell.shell_exec(f"cat {p}", timeout=10.0)
            if r.get("rc") == 0 and r.get("stdout"):
                return {"path": p, "content": r["stdout"]}
        return await _shell.shell_exec("arp -a", timeout=10.0)

    # ---- VPN (WireGuard / Tailscale) ----
    @tool(mcp)
    async def wireguard_show() -> Any:
        """§51 wg show — current peers & traffic."""
        return await _shell.shell_exec("wg show", timeout=10.0)

    @tool(mcp)
    async def wireguard_add_peer(interface: str, public_key: str,
                                   allowed_ips: str,
                                   endpoint: str | None = None,
                                   persistent_keepalive: int | None = None) -> Any:
        """§51 wg set <if> peer <pub> allowed-ips <ips> [endpoint <e>] [persistent-keepalive N]."""
        parts = [f"wg set {interface} peer {public_key}",
                  f"allowed-ips {allowed_ips}"]
        if endpoint: parts.append(f"endpoint {endpoint}")
        if persistent_keepalive: parts.append(f"persistent-keepalive {persistent_keepalive}")
        return await _shell.shell_exec(" ".join(parts), timeout=15.0)

    @tool(mcp)
    async def wireguard_remove_peer(interface: str, public_key: str) -> Any:
        """§51 wg set <if> peer <pub> remove."""
        return await _shell.shell_exec(
            f"wg set {interface} peer {public_key} remove", timeout=10.0)

    @tool(mcp)
    async def tailscale_request(method: str, path: str,
                                  api_key: str,
                                  json_body: dict | None = None) -> Any:
        """§51 Tailscale Central API."""
        return await _http(method, f"https://api.tailscale.com{path}",
                            headers={"Authorization": f"Bearer {api_key}"},
                            json=json_body)

    # ---- Cloudflare ----
    @tool(mcp)
    async def cloudflare_request(method: str, path: str, api_token: str,
                                   json_body: dict | None = None,
                                   params: dict | None = None) -> Any:
        """§51 Cloudflare API v4 (DNS, tunnels, Access, R2, Workers, WAF)."""
        return await _http(method, f"https://api.cloudflare.com/client/v4{path}",
                            headers={"Authorization": f"Bearer {api_token}",
                                      "Content-Type": "application/json"},
                            json=json_body, params=params)

    # ---- NAS ----
    @tool(mcp)
    async def nas_request(base_url: str, method: str, path: str,
                            api_key: str | None = None,
                            cookies: dict | None = None,
                            json_body: dict | None = None,
                            verify_tls: bool = False) -> Any:
        """§51 Generic Synology/TrueNAS/Unraid REST call."""
        headers = {}
        if api_key: headers["Authorization"] = f"Bearer {api_key}"
        return await _http(method, f"{base_url.rstrip('/')}{path}",
                            headers=headers, cookies=cookies,
                            json=json_body, verify=verify_tls)

    # ---- Proxmox ----
    @tool(mcp)
    async def proxmox_request(base_url: str, method: str, path: str,
                                token_id: str, token_secret: str,
                                json_body: dict | None = None,
                                verify_tls: bool = False) -> Any:
        """§51 Proxmox VE API (PVEAPIToken)."""
        return await _http(method, f"{base_url.rstrip('/')}/api2/json{path}",
                            headers={"Authorization":
                                      f"PVEAPIToken={token_id}={token_secret}"},
                            json=json_body, verify=verify_tls)

    # ---- ESXi / vSphere ----
    @tool(mcp)
    async def vsphere_request(base_url: str, method: str, path: str,
                                session_id: str | None = None,
                                json_body: dict | None = None,
                                verify_tls: bool = False) -> Any:
        """§51 vSphere REST (call /rest/com/vmware/cis/session first to get id)."""
        headers = {}
        if session_id: headers["vmware-api-session-id"] = session_id
        return await _http(method, f"{base_url.rstrip('/')}{path}",
                            headers=headers, json=json_body, verify=verify_tls)

    # ---- Continuous LAN discovery ----
    @tool(mcp)
    async def lan_discover(subnet: str = "192.168.1.0/24") -> Any:
        """§51 nmap -sn ARP scan."""
        return await _shell.shell_exec(f"nmap -sn {subnet} -oG -",
                                        timeout=120.0)

    # ---- 802.1X via radclient ----
    @tool(mcp)
    async def radius_test_auth(server: str, secret: str, user: str,
                                  password: str, port: int = 1812) -> Any:
        """§51 freeradius radclient probe (must be installed)."""
        cmd = (f"echo 'User-Name={user},User-Password={password}' | "
                f"radclient -x {server}:{port} auth {secret!r}")
        return await _shell.shell_exec(cmd, timeout=15.0)

    # ---- Routing daemon (FRR / Bird) ----
    @tool(mcp)
    async def routing_daemon_command(daemon: str, command: str) -> Any:
        """§51 Send a vtysh / birdc command to the routing daemon container."""
        if daemon == "frr":
            return await _shell.shell_exec(f"vtysh -c {command!r}", timeout=15.0)
        if daemon == "bird":
            return await _shell.shell_exec(f"birdc -c {command!r}", timeout=15.0)
        return {"error": "daemon must be frr|bird"}

    return 13
