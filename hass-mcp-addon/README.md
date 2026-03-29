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
