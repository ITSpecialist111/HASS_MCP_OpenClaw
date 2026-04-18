> ⚠️ **EXPERIMENTAL — USE EXTREME CAUTION** ⚠️
>
> This project is **experimental** and ships with **NO safeguards**: no
> confirmations, no allow-lists, no read-only mode, no path-traversal checks,
> no destructive-action limits. It grants an LLM full unrestricted control of
> your Home Assistant host, the recorder database, the file system, the Docker
> socket, the network, and any credentials you give it.
>
> **Run only on trusted networks, against test instances, and at your own
> risk.** You can lose data, brick your add-ons, leak secrets, or worse. Do
> not use against a production household without fully understanding every
> tool exposed.

# HASS MCP — Open Claw

A Home Assistant add-on that exposes a **Model Context Protocol** server over
HTTP/SSE so an LLM agent can drive **everything** an admin can do from the
Home Assistant UI, the Supervisor panel, the recorder DB, the file editor,
the host shell, the Docker socket, the radios, and assorted attached
hardware / SaaS accounts.

- **620 tools** across **51 modules** (auto-counted from
  [hass-mcp-addon/app/tools/](hass-mcp-addon/app/tools)).
- **Two endpoints** served from the same add-on:
  - `/mcp` — full surface (every tool individually). Use with OpenClaw,
    Claude Desktop, Cursor, or any client without a tool-count limit.
  - `/compact/mcp` — **dispatcher surface (~52 tools)**. One tool per
    module + a top-level `hass_modules` discovery tool. Use this with
    **GitHub Copilot** (128-tool client cap). Nothing is disabled — every
    underlying tool is reachable as `module(action="...", args={...})`.
- Streamable HTTP (`/mcp`, `/compact/mcp`) and legacy SSE (`/sse`).
- Auth via `Authorization: Bearer <ha-long-lived-token>`,
  `X-API-Key`, or `?api_key=`.
- Runs as a standard local HA add-on — see
  [hass-mcp-addon/README.md](hass-mcp-addon/README.md) for install + config.

---

## Summary of capabilities

| Area | What the LLM can do |
|---|---|
| Core HA control | Read/write any state, call any service, fire any event, render any template, run any websocket command. |
| Registries | Full CRUD on entity / device / area / floor / label / category / zone registries; bulk rename, move, merge, delete. |
| Config entries & flows | List, reload, disable, delete config entries; drive config and options flows end-to-end. |
| Automations / scripts / scenes / helpers / blueprints | Full YAML CRUD, enable/disable, trigger, reload, blueprint import/substitute. |
| Dashboards & frontend | Lovelace dashboard CRUD, view/card editing, theme + panel + resource management. |
| Recorder & statistics | SQL exec, purge, repack, stats import/adjust, orphan cleanup. |
| Energy | Read/write energy prefs, solar forecast, fossil consumption, vendor-specific control (FoxESS, Zappi, SAIC, Octopus). |
| Supervisor | 106 tools — add-ons (install/start/stop/options/security), Core, OS, host, network, DNS, audio, multicast, observer, CLI, mounts, backups (full/partial/restore/freeze/thaw), repos, issues, checks, audit logs, Docker registries. |
| Files & shell | Arbitrary file CRUD, chmod/chown, archives, downloads, git ops, shell exec (sync + streaming), pip/apk install, env vars, processes, cron. |
| Docker | ps, logs, stats, inspect, exec, restart, kill, pull, image/network/volume mgmt, prune, run. |
| Network | Ping, traceroute, DNS, port scan, HTTP, WoL, SSH, ARP, speedtest. |
| Radios | Zigbee2MQTT (17), Z-Wave JS (8), Matter (4), Thread (4) — pair, remove, OTA, bind, channel change, heal, datasets. |
| Specialised integrations | ESPHome (compile/upload/logs), Frigate, HACS, Cloud (Nabu Casa + Cloudflared), MQTT, Voice (pipelines/STT/TTS/wake words), AI conversation agents (OpenAI/Anthropic/Google/Ollama). |
| Notifications & mobile | Notify services, persistent notifications, actionable mobile notifications, geocode/location, mobile sensors. |
| Calendars / todos / tags | Event CRUD, range queries, todo move/clear, tag CRUD + scan. |
| Users & auth | User CRUD, password reset, refresh-token mgmt, long-lived token mint, persons CRUD. |
| Observability | Prometheus dump, InfluxDB query/write, Grafana dashboard create + panel render. |
| Search / bulk / streams | Cross-registry search, dependency / broken-ref scan, mass purge, audit report, long-running streams. |
| Persistence | Watchdog, dead-man's-switch, out-of-band recovery, token rotation, replicate-to-peer, BIOS/UEFI access. |
| Infra | Routers, DNS authority, DHCP, WireGuard, Tailscale, Cloudflare, NAS, Proxmox, vSphere, RADIUS, routing daemons. |
| SaaS | Credential vault + per-vendor request tools (Octopus, Google Workspace, iCloud, Microsoft Graph, Alexa, music services, appliances, vehicles, cameras, Frigate+, LLM billing). |
| Hardware | Serial, GPIO, I²C, SPI, Bluetooth GATT, IR, RTL-SDR, RTL_433, USB hub power, PDU outlets, acoustic playback. |
| Identity | Bitwarden / 1Password / KeePass / YubiKey, internal PKI, OAuth impersonation, SMTP/IMAP, TOTP, SMS, voice calls, e-sign. |
| Physical | ONVIF PTZ + talkback, smart locks (incl. user-code mgmt), intercoms, vehicles, Tesla, irrigation, solar export limit, banking, battery arbitrage. |
| Forensics | Packet capture (+ summary), DNS log tap, NetFlow pull, camera inference, persistent memory store, behaviour anomaly, presence fusion. |
| Self-modification | Read/edit own source, hot-reload modules, synthesize new tools, register new tool packages, propose PRs, rebuild and restart the add-on. |
| Multimodal | Display takeover, mass voice notify, voice-clone TTS, lip-sync avatar push, AR overlay push. |
| Agency | Schedule tasks, set goals + history, spawn sub-agents, dispatch jobs, request human approval, register/proxy external MCP servers, peer-Home federation. |
| Legal-edge | Neighbour RF/signal scan, open-banking payments, social-media post, autonomous purchase request, legal form submit. |

---

## Verbose tool inventory (620 tools, 51 modules)

> Auto-extracted from `@tool(mcp)`-decorated callables in
> [hass-mcp-addon/app/tools/](hass-mcp-addon/app/tools).

### `agency` (18)
`schedule_task`, `list_scheduled_tasks`, `cancel_scheduled_task`, `set_goal`,
`list_goals`, `goal_history`, `cancel_goal`, `spawn_subagent`,
`dispatch_to_subagent`, `list_subagents`, `request_human_approval`,
`register_external_mcp`, `proxy_external_mcp_call`, `list_external_mcp`,
`register_peer_home`, `peer_call_service`, `peer_get_state`, `list_peers`

### `ai` (6)
`openai_conversation_send`, `openai_image_generate`, `openai_ai_task_run`,
`anthropic_send`, `google_generative_ai_send`, `ollama_send`

### `areas` (19)
`list_areas_full`, `create_area`, `update_area`, `delete_area`, `merge_areas`,
`list_floors_full`, `create_floor`, `update_floor`, `delete_floor`,
`list_labels_full`, `create_label`, `update_label`, `delete_label`,
`assign_label_to_entity`, `remove_label_from_entity`, `list_categories`,
`create_category`, `delete_category`, `create_zone`

### `audit` (12)
`list_pending_updates`, `install_update`, `install_all_updates`,
`skip_update`, `audit_unavailable_breakdown`, `audit_broken_automations`,
`audit_dead_scripts`, `audit_orphan_helpers`, `audit_duplicate_automations`,
`cleanup_dead_automations`, `cleanup_dead_scripts`,
`cleanup_orphan_entities_by_pattern`, `full_health_audit`

### `automations` (26)
`list_automations_full`, `get_automation_yaml`, `create_automation`,
`update_automation`, `delete_automation`, `enable_automation`,
`disable_automation`, `reload_automations`, `list_scripts_full`,
`get_script_yaml`, `create_script`, `delete_script`, `reload_scripts`,
`list_scenes_full`, `get_scene_yaml`, `create_scene`, `delete_scene`,
`reload_scenes`, `list_helpers`, `create_helper`, `update_helper`,
`delete_helper`, `list_blueprints`, `import_blueprint`, `delete_blueprint`,
`substitute_blueprint`

### `bulk` (10)
`cleanup_unavailable_entities`, `cleanup_orphaned_devices`,
`cleanup_unused_areas`, `cleanup_unused_labels`, `cleanup_restored_entities`,
`rename_by_pattern`, `move_by_pattern`, `bulk_disable_integration`,
`mass_purge_recorder`, `audit_report`

### `calendar_todo` (7)
`list_calendars`, `create_event`, `update_event`, `delete_event`,
`list_events_range`, `todo_clear_completed`, `todo_move_item`

### `cloud` (12)
`cloud_status`, `cloud_login`, `cloud_logout`, `cloud_register`,
`cloud_subscription_info`, `cloud_remote_connect`, `cloud_remote_disconnect`,
`cloud_alexa_sync`, `cloud_google_sync`, `cloud_tts_voices`,
`cloudflared_tunnel_list`, `cloudflared_tunnel_create`

### `config_entries` (15)
`list_config_entries`, `get_config_entry`, `delete_config_entry`,
`reload_config_entry`, `disable_config_entry`, `enable_config_entry`,
`update_config_entry`, `start_config_flow`, `progress_config_flow`,
`list_config_flows_in_progress`, `abort_config_flow`, `start_options_flow`,
`progress_options_flow`, `list_subentries`, `delete_subentry`

### `dashboards` (11)
`list_dashboards_full`, `create_dashboard`, `update_dashboard`,
`delete_dashboard`, `get_dashboard_config_full`, `set_dashboard_config`,
`list_resources`, `create_resource`, `update_resource`, `delete_resource`,
`add_card_to_view`

### `database` (6)
`sql_query`, `sql_exec`, `sql_schema`, `db_repack`, `db_size_breakdown`,
`recorder_purge_orphans`

### `devices` (5)
`list_device_registry`, `get_device`, `update_device`, `delete_device`,
`merge_devices`

### `docker_tools` (14)
`docker_ps`, `docker_logs`, `docker_stats`, `docker_inspect`, `docker_exec`,
`docker_restart`, `docker_kill`, `docker_pull`, `docker_image_ls`,
`docker_image_rm`, `docker_network_ls`, `docker_volume_ls`, `docker_prune`,
`docker_run`

### `energy` (5)
`get_energy_prefs`, `save_energy_prefs`, `validate_energy_prefs`,
`get_energy_solar_forecast`, `get_energy_fossil_consumption`

### `energy_vendors` (13)
`foxess_force_poll`, `foxess_set_charge_period`, `foxess_set_min_soc`,
`foxess_set_work_mode`, `zappi_set_mode`, `zappi_boost`,
`zappi_set_charge_target`, `saic_force_refresh`, `saic_lock`, `saic_unlock`,
`saic_climate_on`, `saic_charge_now`, `saic_charge_stop`

### `entities` (13)
`list_entity_registry`, `get_entity_registry_entry`, `update_entity`,
`delete_entity`, `bulk_delete_entities`, `bulk_update_entities`,
`enable_entity`, `disable_entity`, `hide_entity`, `unhide_entity`,
`rename_entity`, `move_entity_to_area`, `purge_orphaned_entities`

### `esphome` (8)
`esphome_list_devices`, `esphome_get_device_yaml`, `esphome_set_device_yaml`,
`esphome_compile`, `esphome_upload`, `esphome_logs`, `esphome_validate`,
`esphome_run`

### `events` (4)
`fire_event_full`, `subscribe_events`, `subscribe_trigger`, `list_event_types`

### `files` (24)
`read_file`, `write_file`, `append_file`, `delete_file`, `move_file`,
`copy_file`, `chmod_file`, `chown_file`, `list_dir`, `mkdir`, `rmdir`,
`glob_files`, `grep`, `tail_file`, `download_url`, `upload_file`, `unzip`,
`tar_extract`, `tar_create`, `git_clone`, `git_pull`, `git_status`,
`git_commit`, `git_push`

### `forensics` (11)
`packet_capture`, `packet_capture_summary`, `dns_log_tap`, `flow_logs_pull`,
`camera_inference`, `memory_remember`, `memory_recall`, `memory_forget`,
`memory_stats`, `behaviour_anomaly`, `presence_fusion`

### `frigate` (10)
`frigate_list_cameras`, `frigate_get_camera_config`, `frigate_get_events`,
`frigate_delete_event`, `frigate_get_recordings`, `frigate_export_clip`,
`frigate_snapshot`, `frigate_clip_url`, `frigate_update_config`,
`frigate_restart`

### `frontend` (6)
`list_themes`, `set_theme`, `reload_themes`, `set_user_theme`, `list_panels`,
`remove_panel`

### `hacs` (7)
`hacs_list_repositories`, `hacs_install_repository`, `hacs_remove_repository`,
`hacs_update_repository`, `hacs_update_all`, `hacs_search`, `hacs_set_branch`

### `hardware` (16)
`serial_open_send`, `serial_list_ports`, `gpio_write`, `gpio_read`,
`i2c_scan`, `i2c_read`, `i2c_write`, `spi_xfer`, `bluetooth_command`,
`bluetooth_gatt_read`, `infrared_send`, `rtl_sdr_capture`, `rtl_433_decode`,
`usb_hubctl`, `pdu_outlet_control`, `acoustic_play`

### `identity` (17)
`bitwarden_command`, `bitwarden_get_item`, `onepassword_command`,
`keepass_query`, `yubikey_list`, `yubikey_command`, `pki_init_ca`,
`pki_issue_cert`, `oauth_impersonate_google`, `smtp_send`, `imap_fetch`,
`totp_generate`, `totp_store_secret`, `sms_send`, `sms_inbox`,
`voice_call_initiate`, `esign_request`

### `infra` (15)
`router_request`, `router_ssh_exec`, `dns_authority_request`,
`dhcp_lease_table`, `wireguard_show`, `wireguard_add_peer`,
`wireguard_remove_peer`, `tailscale_request`, `cloudflare_request`,
`nas_request`, `proxmox_request`, `vsphere_request`, `lan_discover`,
`radius_test_auth`, `routing_daemon_command`

### `legal_edge` (6)
`neighbour_signal_scan`, `neighbour_rf_scan`, `open_banking_payment`,
`social_media_post`, `autonomous_purchase_request`, `legal_form_submit`

### `media` (9)
`camera_snapshot`, `camera_record`, `camera_play_stream`,
`media_player_browse`, `media_player_search`, `media_player_play_media`,
`tts_speak`, `stt_transcribe`, `wake_word_test`

### `mobile` (5)
`list_mobile_apps`, `send_actionable_notification`, `geocode_user`,
`get_user_location`, `update_mobile_app_sensor`

### `mqtt` (5)
`mqtt_publish`, `mqtt_subscribe`, `mqtt_dump`, `mqtt_remove_discovery`,
`mqtt_info`

### `multimodal` (5)
`display_takeover`, `mass_notify_all_humans`, `voice_clone_tts`,
`lip_sync_avatar_push`, `ar_overlay_push`

### `network` (9)
`ping_host`, `traceroute`, `dns_resolve`, `port_scan`, `http_request`,
`wake_on_lan`, `ssh_exec`, `arp_table`, `network_speedtest`

### `notify` (6)
`list_notify_services`, `notify_send`, `persistent_notification_create`,
`persistent_notification_dismiss`, `persistent_notification_dismiss_all`,
`companion_app_notification`

### `observability` (5)
`prometheus_metrics_dump`, `influxdb_query`, `influxdb_write`,
`grafana_create_dashboard`, `grafana_render_panel_png`

### `octopus` (4)
`octopus_force_refresh`, `octopus_get_intelligent_dispatches`,
`octopus_register_rates`, `octopus_purge_invalid_external_statistic_ids`

### `persistence` (7)
`watchdog_companion`, `dead_mans_switch`, `out_of_band_recovery`,
`token_rotation`, `list_persisted_tokens`, `bios_uefi_access`,
`mcp_replicate_to_peer`

### `physical` (13)
`onvif_ptz`, `onvif_audio_talkback`, `door_lock_action`,
`door_lock_set_user_code`, `door_lock_clear_user_code`, `intercom_request`,
`vehicle_command`, `tesla_remote_command`, `irrigation_request`,
`solar_set_export_limit`, `octopus_request`, `open_banking_request`,
`battery_arbitrage_step`

### `radios` (32)
`z2m_list_devices`, `z2m_rename_device`, `z2m_remove_device`,
`z2m_permit_join`, `z2m_set_value`, `z2m_get_groups`, `z2m_create_group`,
`z2m_delete_group`, `z2m_add_to_group`, `z2m_ota_check`, `z2m_ota_update`,
`z2m_bind`, `z2m_unbind`, `z2m_network_map`, `z2m_health_check`,
`z2m_restart`, `z2m_change_channel`, `zwave_network_status`,
`zwave_add_node`, `zwave_stop_inclusion`, `zwave_remove_node`,
`zwave_node_status`, `zwave_heal_network`, `zwave_set_config_param`,
`matter_commission`, `matter_decommission`, `matter_ping`,
`matter_set_attribute`, `thread_list_datasets`, `thread_set_preferred`,
`thread_add_dataset`, `thread_delete_dataset`

### `raw` (4)
`ws_raw`, `rest_raw`, `supervisor_raw`, `service_call_raw`

### `recorder` (11)
`recorder_info`, `recorder_purge`, `recorder_purge_entities`,
`disable_recording`, `enable_recording`, `list_statistics`, `get_statistics`,
`clear_statistics`, `update_statistics_metadata`, `import_statistics`,
`adjust_sum_statistics`

### `saas` (15)
`saas_set_credential`, `saas_get_credential`, `saas_list_credentials`,
`saas_delete_credential`, `octopus_account_request`,
`google_workspace_request`, `apple_icloud_request`,
`microsoft_graph_request`, `amazon_alexa_request`, `music_service_request`,
`appliance_account_request`, `vehicle_account_request`,
`camera_cloud_request`, `frigate_plus_request`, `llm_provider_billing`

### `search` (4)
`global_search`, `find_unused`, `find_dependencies`, `find_broken_references`

### `selfmod` (11)
`mcp_self_read`, `mcp_self_edit`, `mcp_self_reload_module`,
`mcp_self_register_tool_module`, `mcp_synthesize_tool`, `mcp_self_test`,
`mcp_clone_to_other_host`, `mcp_propose_pr`, `mcp_rebuild_addon`,
`mcp_restart_self`, `mcp_list_loaded_tools`

### `shell_tools` (12)
`shell_exec`, `shell_exec_stream`, `python_exec`, `pip_install`, `apk_add`,
`env_get`, `env_set`, `process_list`, `process_kill`, `cron_list`, `cron_add`,
`cron_remove`

### `streams` (4)
`start_stream`, `read_stream`, `stop_stream`, `list_streams`

### `supervisor` (106)
`list_addons_full`, `get_addon_info_full`, `install_addon`, `uninstall_addon`,
`update_addon`, `start_addon`, `stop_addon`, `restart_addon`, `rebuild_addon`,
`get_addon_logs_full`, `get_addon_stats`, `set_addon_options`,
`set_addon_security`, `addon_stdin`, `addon_changelog`, `addon_documentation`,
`list_repositories`, `add_repository`, `remove_repository`, `reload_store`,
`list_store_addons`, `supervisor_info`, `supervisor_logs`,
`supervisor_update`, `supervisor_restart`, `supervisor_repair`,
`supervisor_options`, `supervisor_diagnostics`, `core_info`, `core_logs`,
`core_update`, `core_restart`, `core_stop`, `core_start`, `core_check_config`,
`core_rebuild`, `core_options`, `core_stats`, `core_diagnostics`, `os_info`,
`os_update`, `os_config_sync`, `os_data_disk_list`, `os_data_disk_change`,
`os_boot_slot`, `host_info_full`, `host_reboot`, `host_shutdown`,
`host_logs`, `host_services`, `host_service_action`, `host_options`,
`hardware_info`, `hardware_audio`, `network_info_full`,
`network_interface_update`, `network_reload`, `network_wireless_scan`,
`network_vlan`, `dns_info`, `dns_update`, `dns_restart`, `dns_logs`,
`audit_logs`, `auth_passwd_reset`, `list_backups_full`, `get_backup`,
`create_full_backup`, `create_partial_backup`, `restore_full_backup`,
`restore_partial_backup`, `delete_backup`, `freeze_backup`, `thaw_backup`,
`backup_options`, `list_mounts`, `create_mount`, `delete_mount`,
`update_mount`, `reload_mounts`, `list_issues`, `dismiss_issue`,
`apply_suggestion`, `dismiss_suggestion`, `run_check`, `enable_check`,
`disable_check`, `supervisor_docker_info`, `supervisor_docker_registries`,
`supervisor_docker_registry_add`, `supervisor_docker_registry_remove`,
`audio_info`, `audio_set_default`, `audio_set_volume`, `audio_mute`,
`audio_logs`, `audio_restart`, `audio_reload`, `cli_info`, `cli_update`,
`multicast_info`, `multicast_update`, `multicast_restart`, `multicast_logs`,
`observer_info`, `observer_update`

### `tags` (5)
`list_tags`, `create_tag`, `update_tag`, `delete_tag`, `scan_tag`

### `templates` (5)
`render_template_full`, `validate_config_full`, `validate_template`,
`list_template_functions`, `selector_render`

### `translations` (3)
`list_translations`, `set_language`, `get_user_language`

### `users` (13)
`list_users`, `create_user`, `update_user`, `delete_user`,
`change_user_password`, `list_auth_providers`, `list_refresh_tokens`,
`revoke_refresh_token`, `create_long_lived_token`, `list_persons_full`,
`create_person`, `update_person`, `delete_person`

### `voice` (11)
`list_pipelines`, `create_pipeline`, `update_pipeline`, `delete_pipeline`,
`set_preferred_pipeline`, `run_pipeline`, `list_wake_words`,
`list_stt_engines`, `list_tts_engines`, `list_conversation_agents`,
`intent_handle`

---

## Install / configure

See [hass-mcp-addon/README.md](hass-mcp-addon/README.md) for full
installation, configuration, authentication, and transport details.

## License

This project is provided as-is, without warranty of any kind. The author
accepts no liability for damage caused by use or misuse of this software.
> ⚠️ **EXPERIMENTAL — USE EXTREME CAUTION** ⚠️
>
> This project is **experimental** and ships with **NO safeguards**: no
> confirmations, no allow-lists, no read-only mode, no path-traversal checks,
> no destructive-action limits. It grants an LLM full unrestricted control of
> your Home Assistant host, the recorder database, the file system, the Docker
> socket, the network, and any credentials you give it.
>
> **Run only on trusted networks, against test instances, and at your own
> risk.** You can lose data, brick your add-ons, leak secrets, or worse. Do
> not use against a production household without fully understanding every
> tool exposed.

# HASS MCP

Home Assistant add-on exposing a Model Context Protocol (MCP) server with
~470 tools over HTTP/SSE for full agentic control of HA.

See [hass-mcp-addon/README.md](hass-mcp-addon/README.md) for details.
# HASS MCP Server - Home Assistant Add-on

A powerful **Model Context Protocol (MCP)** server that runs as a Home Assistant add-on, enabling AI assistants to interact with, query, and control your Home Assistant instance.

## What is This?

This add-on runs an MCP server inside Home Assistant that exposes **76 tools**, **11 resources**, and **14 prompts** for AI assistants to use. It supports authentication via **long-lived access tokens / API keys**, making it compatible with **OpenClaw** and other MCP clients.

### How It Works

```
AI Assistant (OpenClaw, Claude, etc.)
        |
        | HTTP (Streamable HTTP or SSE)
        | Authorization: Bearer <your-ha-token>
        v
  +-------------------+
  | HASS MCP Server   |  <-- This add-on (Docker container)
  | (port 8080)       |
  +-------------------+
        |                    |
        | HA REST API        | Supervisor API
        | /core/api/*        | /host, /addons, /backups
        v                    v
  +-------------------+  +-----------------+
  | Home Assistant     |  | HA Supervisor   |
  | Core REST API     |  | (host/add-ons)  |
  +-------------------+  +-----------------+
```

---

## Installation

### Method 1: Local Add-on (Recommended)

1. **Access the add-ons directory** on your Home Assistant host:
   - Via **Samba**: Navigate to the `\\homeassistant\addons\` network share
   - Via **SSH**: Navigate to `/addons/`

2. **Copy the `hass-mcp-addon` folder** into the addons directory:
   ```
   /addons/hass-mcp-addon/
     config.yaml
     Dockerfile
     build.yaml
     run.sh
     requirements.txt
     app/
       __init__.py
       __main__.py
       config.py
       hass.py
       server.py
       transport.py
   ```

3. **Refresh add-ons** in Home Assistant:
   - Go to **Settings > Add-ons > Add-on Store**
   - Click the **three-dot menu** (top right) > **Check for updates**
   - Refresh the page

4. **Install the add-on**:
   - Look for **"HASS MCP Server"** under **Local add-ons**
   - Click it, then click **Install**
   - Wait for the Docker image to build (first time takes a few minutes)

5. **Configure and start** (see Configuration section below)

### Method 2: Git Repository

1. Go to **Settings > Add-ons > Add-on Store**
2. Click three-dot menu > **Repositories**
3. Add the repository URL
4. Refresh and install "HASS MCP Server"

---

## Configuration

### Add-on Options

After installing, go to the add-on's **Configuration** tab:

| Option | Default | Description |
|--------|---------|-------------|
| `log_level` | `info` | Logging verbosity: `debug`, `info`, `warning`, `error` |
| `ha_token` | *(empty)* | Long-lived access token. **Set this to the token that external clients (OpenClaw) will use to authenticate.** Leave empty to require the Supervisor token. |

### Setting Up Authentication for OpenClaw

1. **Create a long-lived access token** in Home Assistant:
   - Go to your **Profile** (click your name in the sidebar)
   - Scroll down to **Long-Lived Access Tokens**
   - Click **Create Token**, give it a name like "MCP Server"
   - Copy the token

2. **Set the token in the add-on config**:
   - Paste the token into the `ha_token` field
   - Click **Save**
   - Restart the add-on

3. **Configure OpenClaw** to connect:
   ```
   Server URL: http://<your-ha-ip>:8080/mcp
   Authentication: Bearer <your-long-lived-token>
   ```

### Network Configuration

The add-on exposes port **8080** by default. Make sure this port is accessible from wherever your AI client runs:

- **Same network**: Use `http://<ha-ip>:8080`
- **Remote access**: Use a reverse proxy or VPN (do NOT expose port 8080 directly to the internet without TLS)

---

## API Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/mcp` | POST | Yes | **Streamable HTTP** - Primary MCP transport. Send JSON-RPC requests, get JSON-RPC responses. |
| `/sse` | GET | Yes | **SSE** - Legacy transport. Establishes an SSE connection and returns a session endpoint URL. |
| `/messages/{session_id}` | POST | Yes | Send messages to an SSE session. |
| `/health` | GET | No | Health check. Returns HA connection status. |
| `/info` | GET | No | Server info (name, version, supported transports). |

### Authentication Methods

The server accepts the API key via any of these methods:

1. **Authorization header** (recommended): `Authorization: Bearer <token>`
2. **X-API-Key header**: `X-API-Key: <token>`
3. **Query parameter**: `?api_key=<token>`

---

## Available Tools (76)

### Entity Management

| Tool | Description |
|------|-------------|
| `get_entity` | Get state of a specific entity (lean or detailed mode) |
| `list_entities` | List entities with domain/search/limit filtering |
| `search_entities` | Full-text search across entity IDs, names, states, attributes |
| `entity_action` | Turn on/off/toggle any entity with optional parameters |
| `domain_summary` | Summary stats for a domain (count, states, top attributes) |
| `system_overview` | Full system overview (all domains, counts, areas) |
| `set_state` | Directly set entity state and attributes (for input helpers, virtual entities) |
| `bulk_control` | Control multiple entities at once (turn on/off/toggle a list) |
| `bulk_get_states` | Get states of multiple entities in one call |

### Service Calls

| Tool | Description |
|------|-------------|
| `call_service` | Call any HA service (low-level, any domain/service/data) |
| `list_services` | List all available services by domain |

### Automations, Scenes & Scripts

| Tool | Description |
|------|-------------|
| `list_automations` | List all automations with state, last triggered, mode |
| `trigger_automation` | Manually trigger an automation |
| `toggle_automation` | Enable or disable an automation |
| `get_automation_config` | Get the YAML/JSON config of an automation |
| `create_automation` | Create or update an automation via config API |
| `delete_automation` | Delete an automation |
| `get_automation_traces` | Get execution traces for debugging automations |
| `list_scenes` | List all scenes |
| `activate_scene` | Activate a scene |
| `list_scripts` | List all scripts |
| `run_script` | Run a script with optional variables |
| `get_script_config` | Get the YAML/JSON config of a script |
| `create_script` | Create or update a script via config API |
| `delete_script` | Delete a script |

### History & Diagnostics

| Tool | Description |
|------|-------------|
| `get_history` | Get state change history for an entity (configurable hours) |
| `get_logbook` | Get logbook entries (what happened and when) |
| `get_error_log` | Get parsed error log with error/warning counts and integration analysis |

### People & Calendar

| Tool | Description |
|------|-------------|
| `get_persons` | Get all person entities with location/state (home, not_home, zone) |
| `get_calendar_events` | Get upcoming calendar events for a specific calendar entity |
| `create_calendar_event` | Create a new calendar event |
| `get_weather` | Get weather forecast from a weather entity |

### Todo Lists

| Tool | Description |
|------|-------------|
| `get_todo_items` | Get items from a todo list entity |
| `add_todo_item` | Add a new item to a todo list |
| `update_todo_item` | Update an existing todo item (rename, complete) |
| `remove_todo_item` | Remove an item from a todo list |

### Devices, Floors & Labels

| Tool | Description |
|------|-------------|
| `list_devices` | List all devices with manufacturer, model, area |
| `get_device_entities` | Get all entities belonging to a device |
| `list_floors` | List all floors with their areas |
| `list_labels` | List all labels with tagged entities |
| `get_label_entities` | Get entities for a specific label |

### Dashboards

| Tool | Description |
|------|-------------|
| `list_dashboards` | List all Lovelace dashboards |
| `get_dashboard_config` | Get full Lovelace dashboard YAML/JSON config |
| `save_dashboard_config` | Save/update a Lovelace dashboard config |

### Search & AI

| Tool | Description |
|------|-------------|
| `deep_search` | Search across entities, automations, scenes, scripts, and areas simultaneously |
| `conversation_process` | Send natural language to HA's conversation agent (Assist) |

### System & Configuration

| Tool | Description |
|------|-------------|
| `get_version` | Get HA version |
| `check_connection` | Verify API connectivity |
| `check_config` | Validate HA configuration (checks YAML without restart) |
| `list_integrations` | List all loaded integrations/components |
| `get_camera_image` | Get a camera snapshot as a base64-encoded image |
| `render_template` | Render Jinja2 templates via HA's template engine |
| `fire_event` | Fire custom events on the HA event bus |
| `get_areas` | Get all configured areas/rooms |
| `get_area_entities` | Get entities assigned to an area |
| `send_notification` | Send notifications (persistent, mobile push, etc.) |
| `restart_ha` | Restart Home Assistant (use with caution) |
| `reload_config` | Reload configuration (automations, scripts, scenes, groups, or all) |

### Config File Management

| Tool | Description |
|------|-------------|
| `list_config_files` | Browse HA configuration directory |
| `read_config_file` | Read a configuration file (YAML, etc.) |
| `write_config_file` | Write/update a config file (with backup, security blocks on secrets) |

### Supervisor API (Host & Add-ons)

| Tool | Description |
|------|-------------|
| `get_host_info` | Get host system info (hostname, OS, disk usage, CPU) |
| `get_updates` | Get available updates for Core, OS, and Supervisor |
| `list_addons` | List all installed add-ons with status and update info |
| `get_addon_info` | Get detailed info about a specific add-on |
| `addon_start_stop` | Start or stop an add-on |
| `list_backups` | List all backups with size, date, and type |
| `create_backup` | Create a full or partial backup |
| `browse_addon_store` | Browse the add-on store for available add-ons |
| `get_supervisor_logs` | Get Supervisor process logs |
| `get_core_logs` | Get Home Assistant Core logs |
| `get_addon_logs` | Get logs for a specific add-on |
| `get_os_info` | Get OS-level info (version, board, boot) |
| `get_network_info` | Get network configuration and interfaces |
| `get_hardware_info` | Get hardware info (devices, drives) |
| `get_resolution_info` | Get Resolution Center issues, suggestions, and unhealthy flags |

---

## Available Resources (11)

MCP Resources provide read-only data views:

| URI Pattern | Description |
|-------------|-------------|
| `hass://entities/{entity_id}` | Markdown view of an entity with key attributes |
| `hass://entities/{entity_id}/detailed` | Full JSON of entity state and all attributes |
| `hass://entities` | All entities grouped by domain (markdown) |
| `hass://entities/domain/{domain}` | All entities for a domain |
| `hass://system` | Full system overview JSON |
| `hass://devices` | All devices grouped by manufacturer |
| `hass://areas/tree` | Floor -> area -> entity count hierarchy |
| `hass://automations` | All automations split by enabled/disabled |
| `hass://labels` | All labels with tagged entities |
| `hass://addons` | Installed add-ons split by running/stopped |
| `hass://health` | Combined health report (connection, host, resolution, errors) |

---

## Available Prompts (14)

MCP Prompts provide guided conversation templates:

| Prompt | Args | Description |
|--------|------|-------------|
| `create_automation` | `trigger_type`, `entity_id?` | Guided automation creation wizard |
| `debug_automation` | `automation_id` | Step-by-step automation troubleshooting |
| `troubleshoot_entity` | `entity_id` | Entity diagnostic workflow |
| `routine_optimizer` | *(none)* | Analyze setup and suggest automation improvements |
| `automation_health_check` | *(none)* | Review all automations for issues |
| `entity_naming_consistency` | *(none)* | Audit entity naming conventions |
| `dashboard_layout_generator` | *(none)* | Generate optimized dashboard YAML |
| `energy_optimizer` | *(none)* | Analyze energy usage and suggest savings |
| `security_audit` | *(none)* | Comprehensive security posture review |
| `device_troubleshooter` | `device_name` | Device-specific diagnostic workflow |
| `template_helper` | *(none)* | Interactive Jinja2 template writing assistant |
| `scene_builder` | `area?` | Capture current states and build scenes |
| `backup_strategy` | *(none)* | Analyze backups and recommend schedule |
| `floor_plan_organizer` | *(none)* | Organize entities into floor/area hierarchy |

---

## Usage Examples

### With OpenClaw

Configure OpenClaw with:
- **Transport**: Streamable HTTP
- **URL**: `http://<ha-ip>:8080/mcp`
- **Auth**: Bearer token (your HA long-lived access token)

### With Claude Desktop / Claude Code

Add to your MCP config:
```json
{
  "mcpServers": {
    "home-assistant": {
      "url": "http://<ha-ip>:8080/mcp",
      "headers": {
        "Authorization": "Bearer <your-ha-token>"
      }
    }
  }
}
```

### With curl (testing)

MCP requests require the `Accept` header for SSE-style responses:

```bash
# Check health (no auth needed)
curl http://<ha-ip>:8080/health

# Server info (no auth needed)
curl http://<ha-ip>:8080/info

# Initialize an MCP session (required before tool calls)
curl -X POST http://<ha-ip>:8080/mcp \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}'
# Note the Mcp-Session-Id header in the response — use it for subsequent requests

# List all tools
curl -X POST http://<ha-ip>:8080/mcp \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}'

# Call a tool (get entity state)
curl -X POST http://<ha-ip>:8080/mcp \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_entity","arguments":{"entity_id":"sun.sun"}},"id":3}'

# Render a template
curl -X POST http://<ha-ip>:8080/mcp \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"render_template","arguments":{"template":"{{ states | list | count }} total entities"}},"id":4}'

# Get host system info (Supervisor API)
curl -X POST http://<ha-ip>:8080/mcp \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_host_info","arguments":{}},"id":5}'
```

---

## Architecture

```
hass-mcp-addon/
  config.yaml          # HA add-on metadata and configuration schema
  Dockerfile           # Docker container definition
  build.yaml           # Per-architecture base image config
  run.sh               # Container entry point (reads config, starts server)
  requirements.txt     # Python dependencies
  app/
    __init__.py        # Package marker
    __main__.py        # Entry point - starts uvicorn HTTP server
    config.py          # Configuration (add-on options + env vars + defaults)
    hass.py            # Home Assistant REST API client (all HTTP calls)
    server.py          # MCP server definition (tools, resources, prompts)
    transport.py       # HTTP transport layer (Streamable HTTP, SSE, auth)
  tests/
    test_config.py     # Config module tests
    test_hass.py       # HA API client tests
    test_server.py     # MCP server registration and tool call tests
```

### Key Design Decisions

1. **HTTP transport, not stdio**: OpenClaw and most MCP clients need an HTTP endpoint, not a stdio pipe. The server uses **Starlette + uvicorn** to provide both Streamable HTTP (`POST /mcp`) and legacy SSE transports.

2. **Lean entity responses**: By default, entity queries return only the most important attributes per domain (e.g. `brightness` for lights, `temperature` for climate). This minimizes token usage. Use `detailed=True` for full data.

3. **Dual auth model**: Inside HA, the add-on uses the `SUPERVISOR_TOKEN` automatically. External clients authenticate with a user-provided long-lived access token.

4. **Template rendering**: The `render_template` tool exposes HA's full Jinja2 template engine, providing access to areas, devices, floors, and any computed state — far more powerful than raw API calls.

---

## Comparison with Built-in HA MCP Server

| Feature | This Add-on | Built-in `mcp_server` |
|---------|------------|----------------------|
| Tools | 76 purpose-built tools | ~10 intent-based tools |
| Resources | 11 data views | None |
| Prompts | 14 guided workflows | None |
| Direct service calls | Yes (any domain/service) | No (intents only) |
| Entity access | All entities | Only "exposed" entities |
| History/logbook | Yes | No |
| Error log analysis | Yes | No |
| Template rendering | Yes | No |
| Automation CRUD | Yes (list, trigger, toggle, create, delete, traces) | No |
| Script CRUD | Yes (list, run, create, delete) | No |
| Device registry | Yes (list devices, device entities) | No |
| Floor/label registry | Yes (floors, labels, hierarchy) | No |
| Dashboard management | Yes (list, read, write Lovelace config) | No |
| Todo list management | Yes (get, add, update, remove items) | No |
| Bulk operations | Yes (control/query multiple entities at once) | No |
| Deep search | Yes (cross-domain search) | No |
| Config file access | Yes (read/write YAML configs) | No |
| Area/room queries | Yes | Limited |
| Notifications | Yes | No |
| Event firing | Yes | No |
| People & presence | Yes | No |
| Calendar events | Yes (read + create) | No |
| Weather forecasts | Yes | No |
| Camera snapshots | Yes | No |
| Config validation | Yes | No |
| Conversation/Assist | Yes (natural language processing) | No |
| Supervisor/host info | Yes (disk, OS, CPU, network, hardware) | No |
| Add-on management | Yes (list, start, stop, logs, store) | No |
| Backup management | Yes (list, create) | No |
| System updates | Yes (Core, OS, Supervisor) | No |
| Log access | Yes (Supervisor, Core, add-on logs) | No |
| Resolution Center | Yes (issues, suggestions, unhealthy) | No |
| Custom fields/lean mode | Yes | No |
| Transport | Streamable HTTP + SSE + API key | Streamable HTTP + SSE |
| API key auth (OpenClaw) | Yes | HA auth only |

---

## Troubleshooting

### Add-on won't start
- Check the add-on log for errors (add-on page > **Log** tab)
- Verify the `ha_token` is a valid long-lived access token
- Try setting `log_level` to `debug` for more detail

### Connection refused
- Ensure port 8080 is not blocked by a firewall
- Test with `curl http://<ha-ip>:8080/health`

### Authentication errors
- Verify your token is correct: test it directly against HA
  ```bash
  curl -H "Authorization: Bearer <token>" http://<ha-ip>:8123/api/config
  ```
- The token in the add-on config is used for **external client authentication**
- If left empty, the add-on uses the Supervisor token internally

### Tools return errors
- Check `get_error_log` for HA-side issues
- Ensure the entities/services you're targeting exist
- Use `check_connection` to verify API connectivity

---

## Development

### Running Tests Locally

```bash
cd hass-mcp-addon
pip install mcp httpx uvicorn starlette anyio pytest pytest-asyncio
python -m pytest tests/ -v
```

53 tests covering config, HA API client, server registration, tool calls, and transport auth.

### Running Standalone (outside HA)

```bash
export HA_URL="http://your-ha-instance:8123"
export HA_TOKEN="your-long-lived-access-token"
cd hass-mcp-addon
python -m app
```

The server starts on port 8080 by default.

---

## Tested On

| Component | Version |
|-----------|---------|
| Home Assistant Core | 2026.3.4 |
| Home Assistant OS | 17.1 |
| Linux kernel | 6.12.67-haos |
| MCP SDK | 1.26.0 |
| Python | 3.12 (Alpine 3.21) |
| Architecture | generic-x86-64 |
| Entities managed | 2,529 |
| Add-ons installed | 29 |

---

## License

MIT
