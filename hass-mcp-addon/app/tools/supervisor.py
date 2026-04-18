"""§6 Full Supervisor / OS / Host / Network / Backup / Docker surface."""
from __future__ import annotations

from typing import Any

from .. import supervisor_client as sup
from ._helpers import tool


def register(mcp) -> int:
    n = 0
    def t(name: str, fn):
        nonlocal n
        fn.__name__ = name
        tool(mcp)(fn)
        n += 1

    # ---------- 6.1 Add-ons ----------
    @tool(mcp)
    async def list_addons_full() -> Any:
        """§6.1 List all add-ons (full info)."""
        return await sup.get("/addons")

    @tool(mcp)
    async def get_addon_info_full(slug: str) -> Any:
        """§6.1 Full info for a specific add-on."""
        return await sup.get(f"/addons/{slug}/info")

    @tool(mcp)
    async def install_addon(slug: str) -> Any:
        """§6.1 Install an add-on from the store."""
        return await sup.post(f"/store/addons/{slug}/install")

    @tool(mcp)
    async def uninstall_addon(slug: str) -> Any:
        """§6.1 Uninstall an add-on."""
        return await sup.post(f"/addons/{slug}/uninstall")

    @tool(mcp)
    async def update_addon(slug: str) -> Any:
        """§6.1 Update an add-on."""
        return await sup.post(f"/addons/{slug}/update")

    @tool(mcp)
    async def start_addon(slug: str) -> Any:
        """§6.1 Start an add-on."""
        return await sup.post(f"/addons/{slug}/start")

    @tool(mcp)
    async def stop_addon(slug: str) -> Any:
        """§6.1 Stop an add-on."""
        return await sup.post(f"/addons/{slug}/stop")

    @tool(mcp)
    async def restart_addon(slug: str) -> Any:
        """§6.1 Restart an add-on."""
        return await sup.post(f"/addons/{slug}/restart")

    @tool(mcp)
    async def rebuild_addon(slug: str) -> Any:
        """§6.1 Rebuild an add-on (local builds)."""
        return await sup.post(f"/addons/{slug}/rebuild")

    @tool(mcp)
    async def get_addon_logs_full(slug: str, lines: int = 200) -> str:
        """§6.1 Tail an add-on's logs."""
        return await sup.logs(f"/addons/{slug}/logs", lines=lines)

    @tool(mcp)
    async def get_addon_stats(slug: str) -> Any:
        """§6.1 CPU/mem/network stats for an add-on."""
        return await sup.get(f"/addons/{slug}/stats")

    @tool(mcp)
    async def set_addon_options(slug: str, options: dict) -> Any:
        """§6.1 Set an add-on's options."""
        return await sup.post(f"/addons/{slug}/options", {"options": options})

    @tool(mcp)
    async def set_addon_security(slug: str, protected: bool) -> Any:
        """§6.1 Toggle protection mode."""
        return await sup.post(f"/addons/{slug}/security", {"protected": protected})

    @tool(mcp)
    async def addon_stdin(slug: str, data: str) -> Any:
        """§6.1 Write to an add-on's stdin."""
        return await sup.request("POST", f"/addons/{slug}/stdin", json={"data": data})

    @tool(mcp)
    async def addon_changelog(slug: str) -> str:
        """§6.1 Add-on changelog."""
        return await sup.get(f"/addons/{slug}/changelog", raw=True)

    @tool(mcp)
    async def addon_documentation(slug: str) -> str:
        """§6.1 Add-on documentation."""
        return await sup.get(f"/addons/{slug}/documentation", raw=True)

    # ---------- 6.2 Add-on stores ----------
    @tool(mcp)
    async def list_repositories() -> Any:
        """§6.2 List add-on repositories."""
        return await sup.get("/store/repositories")

    @tool(mcp)
    async def add_repository(repository: str) -> Any:
        """§6.2 Add an add-on repository (URL)."""
        return await sup.post("/store/repositories", {"repository": repository})

    @tool(mcp)
    async def remove_repository(repo_slug: str) -> Any:
        """§6.2 Remove a repository."""
        return await sup.delete(f"/store/repositories/{repo_slug}")

    @tool(mcp)
    async def reload_store() -> Any:
        """§6.2 Reload the add-on store."""
        return await sup.post("/store/reload")

    @tool(mcp)
    async def list_store_addons() -> Any:
        """§6.2 List all add-ons available in the store."""
        return await sup.get("/store")

    # ---------- 6.3 Supervisor ----------
    @tool(mcp)
    async def supervisor_info() -> Any:
        """§6.3 Supervisor info."""
        return await sup.get("/supervisor/info")

    @tool(mcp)
    async def supervisor_logs(lines: int = 200) -> str:
        """§6.3 Supervisor logs."""
        return await sup.logs("/supervisor/logs", lines=lines)

    @tool(mcp)
    async def supervisor_update(version: str | None = None) -> Any:
        """§6.3 Update Supervisor."""
        body = {"version": version} if version else None
        return await sup.post("/supervisor/update", body)

    @tool(mcp)
    async def supervisor_restart() -> Any:
        """§6.3 Restart Supervisor."""
        return await sup.post("/supervisor/restart")

    @tool(mcp)
    async def supervisor_repair() -> Any:
        """§6.3 Trigger Supervisor repair."""
        return await sup.post("/supervisor/repair")

    @tool(mcp)
    async def supervisor_options(options: dict) -> Any:
        """§6.3 Set Supervisor options."""
        return await sup.post("/supervisor/options", options)

    @tool(mcp)
    async def supervisor_diagnostics(enable: bool) -> Any:
        """§6.3 Enable/disable diagnostics."""
        return await sup.post("/supervisor/options", {"diagnostics": enable})

    # ---------- 6.4 Core ----------
    @tool(mcp)
    async def core_info() -> Any:
        """§6.4 Core info."""
        return await sup.get("/core/info")

    @tool(mcp)
    async def core_logs(lines: int = 200) -> str:
        """§6.4 Core logs."""
        return await sup.logs("/core/logs", lines=lines)

    @tool(mcp)
    async def core_update(version: str | None = None) -> Any:
        """§6.4 Update Core."""
        body = {"version": version} if version else None
        return await sup.post("/core/update", body)

    @tool(mcp)
    async def core_restart() -> Any:
        """§6.4 Restart Core."""
        return await sup.post("/core/restart")

    @tool(mcp)
    async def core_stop() -> Any:
        """§6.4 Stop Core."""
        return await sup.post("/core/stop")

    @tool(mcp)
    async def core_start() -> Any:
        """§6.4 Start Core."""
        return await sup.post("/core/start")

    @tool(mcp)
    async def core_check_config() -> Any:
        """§6.4 Validate Core config."""
        return await sup.post("/core/check")

    @tool(mcp)
    async def core_rebuild() -> Any:
        """§6.4 Rebuild Core container."""
        return await sup.post("/core/rebuild")

    @tool(mcp)
    async def core_options(options: dict) -> Any:
        """§6.4 Set Core options."""
        return await sup.post("/core/options", options)

    @tool(mcp)
    async def core_stats() -> Any:
        """§6.4 Core resource stats."""
        return await sup.get("/core/stats")

    @tool(mcp)
    async def core_diagnostics(enable: bool) -> Any:
        """§6.4 Toggle Core diagnostics."""
        return await sup.post("/core/options", {"diagnostics": enable})

    # ---------- 6.5 OS ----------
    @tool(mcp)
    async def os_info() -> Any:
        """§6.5 HAOS info."""
        return await sup.get("/os/info")

    @tool(mcp)
    async def os_update(version: str | None = None) -> Any:
        """§6.5 Update HAOS."""
        body = {"version": version} if version else None
        return await sup.post("/os/update", body)

    @tool(mcp)
    async def os_config_sync() -> Any:
        """§6.5 Sync OS config."""
        return await sup.post("/os/config/sync")

    @tool(mcp)
    async def os_data_disk_list() -> Any:
        """§6.5 List candidate data disks."""
        return await sup.get("/os/datadisk/list")

    @tool(mcp)
    async def os_data_disk_change(device: str) -> Any:
        """§6.5 Move data disk to another device."""
        return await sup.post("/os/datadisk/move", {"device": device})

    @tool(mcp)
    async def os_boot_slot(boot_slot: str) -> Any:
        """§6.5 Set boot slot (HAOS Green/Yellow)."""
        return await sup.post("/os/boot-slot", {"boot_slot": boot_slot})

    # ---------- 6.6 Host ----------
    @tool(mcp)
    async def host_info_full() -> Any:
        """§6.6 Host info."""
        return await sup.get("/host/info")

    @tool(mcp)
    async def host_reboot() -> Any:
        """§6.6 Reboot host (HAOS)."""
        return await sup.post("/host/reboot")

    @tool(mcp)
    async def host_shutdown() -> Any:
        """§6.6 Shutdown host."""
        return await sup.post("/host/shutdown")

    @tool(mcp)
    async def host_logs(lines: int = 200) -> str:
        """§6.6 Host journal."""
        return await sup.logs("/host/logs", lines=lines)

    @tool(mcp)
    async def host_services() -> Any:
        """§6.6 List host services."""
        return await sup.get("/host/services")

    @tool(mcp)
    async def host_service_action(service: str, action: str) -> Any:
        """§6.6 start/stop/restart/reload a host service."""
        return await sup.post(f"/host/services/{service}/{action}")

    @tool(mcp)
    async def host_options(hostname: str | None = None) -> Any:
        """§6.6 Update host options (hostname)."""
        body = {}
        if hostname: body["hostname"] = hostname
        return await sup.post("/host/options", body)

    @tool(mcp)
    async def hardware_info() -> Any:
        """§6.6 Full hardware inventory."""
        return await sup.get("/hardware/info")

    @tool(mcp)
    async def hardware_audio() -> Any:
        """§6.6 Audio device list."""
        return await sup.get("/hardware/audio")

    # ---------- 6.7 Network ----------
    @tool(mcp)
    async def network_info_full() -> Any:
        """§6.7 Network info."""
        return await sup.get("/network/info")

    @tool(mcp)
    async def network_interface_update(interface: str, config: dict) -> Any:
        """§6.7 Update interface config (ipv4, ipv6, wifi)."""
        return await sup.post(f"/network/interface/{interface}/update", config)

    @tool(mcp)
    async def network_reload() -> Any:
        """§6.7 Reload networking."""
        return await sup.post("/network/reload")

    @tool(mcp)
    async def network_wireless_scan(interface: str) -> Any:
        """§6.7 Scan for wireless networks."""
        return await sup.get(f"/network/interface/{interface}/accesspoints")

    @tool(mcp)
    async def network_vlan(interface: str, vlan: int, config: dict) -> Any:
        """§6.7 Configure a VLAN on interface."""
        return await sup.post(f"/network/interface/{interface}/vlan/{vlan}", config)

    @tool(mcp)
    async def dns_info() -> Any:
        """§6.7 DNS info."""
        return await sup.get("/dns/info")

    @tool(mcp)
    async def dns_update(servers: list[str]) -> Any:
        """§6.7 Update DNS servers list."""
        return await sup.post("/dns/options", {"servers": servers})

    @tool(mcp)
    async def dns_restart() -> Any:
        """§6.7 Restart DNS."""
        return await sup.post("/dns/restart")

    @tool(mcp)
    async def dns_logs(lines: int = 200) -> str:
        """§6.7 DNS logs."""
        return await sup.logs("/dns/logs", lines=lines)

    # ---------- 6.8 Auth & security ----------
    @tool(mcp)
    async def audit_logs(lines: int = 200) -> str:
        """§6.8 Audit logs."""
        return await sup.logs("/audit/logs", lines=lines)

    @tool(mcp)
    async def auth_passwd_reset(username: str, password: str) -> Any:
        """§6.8 Reset a HA user's password (Supervisor auth)."""
        return await sup.post("/auth/reset", {"username": username, "password": password})

    # ---------- 6.9 Backups ----------
    @tool(mcp)
    async def list_backups_full() -> Any:
        """§6.9 List backups."""
        return await sup.get("/backups")

    @tool(mcp)
    async def get_backup(slug: str) -> Any:
        """§6.9 Get backup info."""
        return await sup.get(f"/backups/{slug}/info")

    @tool(mcp)
    async def create_full_backup(name: str | None = None, password: str | None = None) -> Any:
        """§6.9 Create a full backup."""
        body: dict = {}
        if name: body["name"] = name
        if password: body["password"] = password
        return await sup.post("/backups/new/full", body)

    @tool(mcp)
    async def create_partial_backup(name: str | None = None,
                                    addons: list[str] | None = None,
                                    folders: list[str] | None = None,
                                    homeassistant: bool = True,
                                    password: str | None = None) -> Any:
        """§6.9 Create a partial backup."""
        body: dict = {"homeassistant": homeassistant}
        if name: body["name"] = name
        if addons: body["addons"] = addons
        if folders: body["folders"] = folders
        if password: body["password"] = password
        return await sup.post("/backups/new/partial", body)

    @tool(mcp)
    async def restore_full_backup(slug: str, password: str | None = None) -> Any:
        """§6.9 Restore a full backup."""
        body = {"password": password} if password else {}
        return await sup.post(f"/backups/{slug}/restore/full", body)

    @tool(mcp)
    async def restore_partial_backup(slug: str, addons: list[str] | None = None,
                                     folders: list[str] | None = None,
                                     homeassistant: bool = True,
                                     password: str | None = None) -> Any:
        """§6.9 Partially restore a backup."""
        body: dict = {"homeassistant": homeassistant}
        if addons: body["addons"] = addons
        if folders: body["folders"] = folders
        if password: body["password"] = password
        return await sup.post(f"/backups/{slug}/restore/partial", body)

    @tool(mcp)
    async def delete_backup(slug: str) -> Any:
        """§6.9 Delete a backup."""
        return await sup.delete(f"/backups/{slug}")

    @tool(mcp)
    async def freeze_backup() -> Any:
        """§6.9 Freeze backups (pause)."""
        return await sup.post("/backups/freeze")

    @tool(mcp)
    async def thaw_backup() -> Any:
        """§6.9 Thaw backups (resume)."""
        return await sup.post("/backups/thaw")

    @tool(mcp)
    async def backup_options(options: dict) -> Any:
        """§6.9 Set default backup options."""
        return await sup.post("/backups/options", options)

    # ---------- 6.10 Mounts ----------
    @tool(mcp)
    async def list_mounts() -> Any:
        """§6.10 List network mounts."""
        return await sup.get("/mounts")

    @tool(mcp)
    async def create_mount(name: str, type_: str, server: str, share: str, **fields) -> Any:
        """§6.10 Create a mount (cifs/nfs)."""
        body = {"name": name, "type": type_, "server": server, "share": share, **fields}
        return await sup.post("/mounts", body)

    @tool(mcp)
    async def delete_mount(name: str) -> Any:
        """§6.10 Delete a mount."""
        return await sup.delete(f"/mounts/{name}")

    @tool(mcp)
    async def update_mount(name: str, patch: dict) -> Any:
        """§6.10 Update a mount."""
        return await sup.post(f"/mounts/{name}", patch)

    @tool(mcp)
    async def reload_mounts() -> Any:
        """§6.10 Reload all mounts."""
        return await sup.post("/mounts/reload")

    # ---------- 6.11 Resolution Center ----------
    @tool(mcp)
    async def list_issues() -> Any:
        """§6.11 List Resolution Center issues."""
        info = await sup.get("/resolution/info")
        return info.get("issues", info)

    @tool(mcp)
    async def dismiss_issue(issue_id: str) -> Any:
        """§6.11 Dismiss an issue."""
        return await sup.delete(f"/resolution/issue/{issue_id}")

    @tool(mcp)
    async def apply_suggestion(suggestion_id: str) -> Any:
        """§6.11 Apply a suggestion."""
        return await sup.post(f"/resolution/suggestion/{suggestion_id}")

    @tool(mcp)
    async def dismiss_suggestion(suggestion_id: str) -> Any:
        """§6.11 Dismiss a suggestion."""
        return await sup.delete(f"/resolution/suggestion/{suggestion_id}")

    @tool(mcp)
    async def run_check(check: str) -> Any:
        """§6.11 Run a resolution check by slug."""
        return await sup.post(f"/resolution/check/{check}/run")

    @tool(mcp)
    async def enable_check(check: str) -> Any:
        """§6.11 Enable a check."""
        return await sup.post(f"/resolution/check/{check}/options", {"enabled": True})

    @tool(mcp)
    async def disable_check(check: str) -> Any:
        """§6.11 Disable a check."""
        return await sup.post(f"/resolution/check/{check}/options", {"enabled": False})

    # ---------- 6.12 Docker (Supervisor) ----------
    @tool(mcp)
    async def supervisor_docker_info() -> Any:
        """§6.12 Supervisor's view of docker."""
        return await sup.get("/docker/info")

    @tool(mcp)
    async def supervisor_docker_registries() -> Any:
        """§6.12 List docker registries."""
        return await sup.get("/docker/registries")

    @tool(mcp)
    async def supervisor_docker_registry_add(hostname: str, username: str, password: str) -> Any:
        """§6.12 Add a docker registry."""
        return await sup.post("/docker/registries", {"hostname": hostname,
                                                       "username": username,
                                                       "password": password})

    @tool(mcp)
    async def supervisor_docker_registry_remove(hostname: str) -> Any:
        """§6.12 Remove a docker registry."""
        return await sup.delete(f"/docker/registries/{hostname}")

    # ---------- 6.13 Audio ----------
    @tool(mcp)
    async def audio_info() -> Any:
        """§6.13 Audio plugin info."""
        return await sup.get("/audio/info")

    @tool(mcp)
    async def audio_set_default(name: str, application: str = "output") -> Any:
        """§6.13 Set default audio device."""
        return await sup.post(f"/audio/default/{application}", {"name": name})

    @tool(mcp)
    async def audio_set_volume(name: str, volume: float, application: str = "output") -> Any:
        """§6.13 Set audio volume (0..1)."""
        return await sup.post(f"/audio/volume/{application}", {"name": name, "volume": volume})

    @tool(mcp)
    async def audio_mute(name: str, mute: bool, application: str = "output") -> Any:
        """§6.13 Mute audio device."""
        return await sup.post(f"/audio/mute/{application}", {"name": name, "active": mute})

    @tool(mcp)
    async def audio_logs(lines: int = 200) -> str:
        """§6.13 Audio logs."""
        return await sup.logs("/audio/logs", lines=lines)

    @tool(mcp)
    async def audio_restart() -> Any:
        """§6.13 Restart audio plugin."""
        return await sup.post("/audio/restart")

    @tool(mcp)
    async def audio_reload() -> Any:
        """§6.13 Reload audio plugin."""
        return await sup.post("/audio/reload")

    # ---------- 6.14 CLI ----------
    @tool(mcp)
    async def cli_info() -> Any:
        """§6.14 CLI plugin info."""
        return await sup.get("/cli/info")

    @tool(mcp)
    async def cli_update(version: str | None = None) -> Any:
        """§6.14 Update CLI plugin."""
        return await sup.post("/cli/update", {"version": version} if version else None)

    # ---------- 6.15 Multicast ----------
    @tool(mcp)
    async def multicast_info() -> Any:
        """§6.15 Multicast plugin info."""
        return await sup.get("/multicast/info")

    @tool(mcp)
    async def multicast_update(version: str | None = None) -> Any:
        """§6.15 Update multicast."""
        return await sup.post("/multicast/update", {"version": version} if version else None)

    @tool(mcp)
    async def multicast_restart() -> Any:
        """§6.15 Restart multicast."""
        return await sup.post("/multicast/restart")

    @tool(mcp)
    async def multicast_logs(lines: int = 200) -> str:
        """§6.15 Multicast logs."""
        return await sup.logs("/multicast/logs", lines=lines)

    # ---------- 6.16 Observer ----------
    @tool(mcp)
    async def observer_info() -> Any:
        """§6.16 Observer plugin info."""
        return await sup.get("/observer/info")

    @tool(mcp)
    async def observer_update(version: str | None = None) -> Any:
        """§6.16 Update observer."""
        return await sup.post("/observer/update", {"version": version} if version else None)

    return 70
