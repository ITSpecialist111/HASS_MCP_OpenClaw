"""§50 Self-preservation & persistence."""
from __future__ import annotations

import base64
import json
import os
import secrets
from typing import Any

import httpx

from .. import shell as _shell
from .. import supervisor_client as sup
from ..ws_client import get_ws
from ._helpers import tool

_PERSIST_DIR = "/data/persistence"
_TOKEN_STORE = f"{_PERSIST_DIR}/tokens.json"


def _ensure_dir() -> None:
    os.makedirs(_PERSIST_DIR, exist_ok=True)


def register(mcp) -> int:
    ws = get_ws

    @tool(mcp)
    async def watchdog_companion(image: str = "ghcr.io/local/hass-mcp-watchdog:latest",
                                   container_name: str = "hass_mcp_watchdog",
                                   check_url: str = "http://homeassistant:8099/health",
                                   interval: int = 30) -> dict:
        """§50 Run a sibling docker container that monitors this MCP add-on
        and reinstalls it from the supervisor store if it disappears.
        Idempotent."""
        from .. import docker_client as dc
        try:
            for c in dc.ps(all_=True):
                if c.get("name") == container_name:
                    dc.kill(container_name)
                    dc.client().containers.get(container_name).remove(force=True)
        except Exception:
            pass
        env = {"WATCH_URL": check_url, "INTERVAL": str(interval),
                "ADDON_SLUG": "local_hass_mcp_server",
                "SUPERVISOR_TOKEN": os.environ.get("SUPERVISOR_TOKEN", "")}
        return dc.docker_run(image=image, name=container_name, detach=True,
                              restart_policy={"Name": "unless-stopped"},
                              network_mode="host",
                              volumes={"/var/run/docker.sock":
                                        {"bind": "/var/run/docker.sock", "mode": "rw"}},
                              environment=env)

    @tool(mcp)
    async def dead_mans_switch(remote_url: str, remote_token: str,
                                 include_tokens: bool = True,
                                 include_storage: bool = True) -> dict:
        """§50 Encrypt and push critical state (tokens, .storage, options.json)
        to a remote endpoint (S3 / R2 / WebDAV / arbitrary HTTP PUT)."""
        from cryptography.fernet import Fernet
        _ensure_dir()
        key_path = f"{_PERSIST_DIR}/dms.key"
        if not os.path.exists(key_path):
            with open(key_path, "wb") as f: f.write(Fernet.generate_key())
        with open(key_path, "rb") as f: key = f.read()
        f = Fernet(key)
        bundle: dict[str, Any] = {}
        if include_tokens and os.path.exists(_TOKEN_STORE):
            with open(_TOKEN_STORE) as fh: bundle["tokens"] = fh.read()
        cfg = "/config" if os.path.isdir("/config") else "/homeassistant"
        if include_storage and os.path.isdir(f"{cfg}/.storage"):
            for fn in ("auth", "auth_provider.homeassistant",
                        "core.config_entries", "lovelace"):
                p = f"{cfg}/.storage/{fn}"
                if os.path.exists(p):
                    with open(p) as fh: bundle[f"storage:{fn}"] = fh.read()
        ciphertext = f.encrypt(json.dumps(bundle).encode())
        async with httpx.AsyncClient(timeout=120.0) as c:
            r = await c.put(remote_url, content=ciphertext,
                             headers={"Authorization": f"Bearer {remote_token}",
                                       "Content-Type": "application/octet-stream"})
            r.raise_for_status()
        return {"pushed": True, "bytes": len(ciphertext),
                 "key_b64": base64.b64encode(key).decode(),
                 "warning": "store key_b64 OFF-BOX or you cannot decrypt"}

    @tool(mcp)
    async def out_of_band_recovery(port: int = 8100,
                                     image: str = "ghcr.io/local/hass-mcp:latest") -> dict:
        """§50 Spawn a recovery MCP on a separate port via docker."""
        from .. import docker_client as dc
        try:
            dc.client().containers.get("hass_mcp_recovery").remove(force=True)
        except Exception: pass
        return dc.docker_run(image=image, name="hass_mcp_recovery", detach=True,
                              restart_policy={"Name": "unless-stopped"},
                              ports={f"{port}/tcp": port},
                              environment={"SUPERVISOR_TOKEN":
                                            os.environ.get("SUPERVISOR_TOKEN", ""),
                                            "RECOVERY": "1"})

    @tool(mcp)
    async def token_rotation(client_name: str = "hass_mcp_persistence") -> dict:
        """§50 Mint a new long-lived access token and stash it locally."""
        _ensure_dir()
        # WS auth/long_lived_access_token
        try:
            tok = await ws().call("auth/long_lived_access_token",
                                    client_name=f"{client_name}_{secrets.token_hex(4)}",
                                    lifespan=3650)
        except Exception as e:
            return {"error": f"ws mint failed: {e}"}
        store: dict = {}
        if os.path.exists(_TOKEN_STORE):
            try:
                with open(_TOKEN_STORE) as f: store = json.load(f)
            except Exception: pass
        store.setdefault("tokens", []).append({"created": secrets.token_hex(8),
                                                 "token": tok})
        with open(_TOKEN_STORE, "w") as f: json.dump(store, f)
        os.chmod(_TOKEN_STORE, 0o600)
        return {"minted": True, "stored_at": _TOKEN_STORE,
                 "count": len(store["tokens"])}

    @tool(mcp)
    async def list_persisted_tokens() -> dict:
        """§50 List stashed tokens (values redacted)."""
        if not os.path.exists(_TOKEN_STORE):
            return {"tokens": []}
        with open(_TOKEN_STORE) as f: store = json.load(f)
        return {"tokens": [{"created": t["created"],
                              "preview": t["token"][:12] + "..."}
                             for t in store.get("tokens", [])]}

    @tool(mcp)
    async def bios_uefi_access(host: str, user: str, password: str,
                                  vendor: str = "ipmi",
                                  command: str = "power status") -> dict:
        """§50 IPMI/iDRAC/AMT power & boot control via ipmitool."""
        if vendor not in ("ipmi", "idrac", "amt"):
            return {"error": "vendor must be ipmi|idrac|amt"}
        cmd = (f"ipmitool -I lanplus -H {host} -U {user!r} -P {password!r} "
                f"{command}")
        return await _shell.shell_exec(cmd, timeout=60.0)

    @tool(mcp)
    async def mcp_replicate_to_peer(peer_ha_url: str, peer_token: str,
                                      addon_slug: str = "local_hass_mcp_server") -> dict:
        """§50 Install this MCP add-on onto a peer HA instance via its Supervisor."""
        async with httpx.AsyncClient(timeout=120.0) as c:
            r = await c.post(f"{peer_ha_url}/api/hassio/addons/{addon_slug}/install",
                              headers={"Authorization": f"Bearer {peer_token}"})
            try: body = r.json()
            except Exception: body = r.text
        return {"status_code": r.status_code, "body": body}

    return 7
