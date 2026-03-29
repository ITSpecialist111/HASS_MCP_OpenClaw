"""HASS MCP Server - Home Assistant API client.

All HTTP communication with the Home Assistant REST API happens here.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from .config import get_api_base, get_headers, get_supervisor_headers, SUPERVISOR_URL

logger = logging.getLogger(__name__)

# Timeout for API calls (seconds)
API_TIMEOUT = 30.0

# Domain-specific important attributes to include in lean responses
DOMAIN_IMPORTANT_ATTRIBUTES = {
    "light": ["brightness", "color_temp", "rgb_color", "color_mode", "effect"],
    "climate": [
        "temperature", "current_temperature", "hvac_action", "target_temp_high",
        "target_temp_low", "humidity", "fan_mode", "preset_mode",
    ],
    "cover": ["current_position", "current_tilt_position"],
    "fan": ["percentage", "preset_mode", "direction", "oscillating"],
    "media_player": [
        "media_title", "media_artist", "media_album_name", "source",
        "volume_level", "is_volume_muted", "media_content_type",
    ],
    "sensor": ["unit_of_measurement", "device_class", "state_class"],
    "binary_sensor": ["device_class"],
    "weather": [
        "temperature", "humidity", "pressure", "wind_speed",
        "wind_bearing", "forecast",
    ],
    "vacuum": ["battery_level", "fan_speed", "status"],
    "lock": ["is_locked"],
    "alarm_control_panel": ["code_arm_required", "changed_by"],
    "camera": ["is_recording", "is_streaming", "motion_detection"],
    "water_heater": ["temperature", "current_temperature", "operation_mode"],
    "humidifier": ["humidity", "current_humidity", "mode"],
    "valve": ["current_position"],
    "siren": ["available_tones", "tone", "volume_level"],
    "number": ["min", "max", "step", "mode"],
    "select": ["options"],
    "input_number": ["min", "max", "step", "mode"],
    "input_select": ["options"],
    "timer": ["duration", "remaining", "finishes_at"],
    "counter": ["minimum", "maximum", "step"],
    "automation": ["last_triggered", "mode", "current"],
    "script": ["last_triggered", "mode", "current"],
    "scene": ["entity_id"],
    "person": ["source", "latitude", "longitude", "gps_accuracy"],
    "device_tracker": ["source_type", "latitude", "longitude", "battery_level"],
    "zone": ["latitude", "longitude", "radius", "passive"],
    "sun": ["next_rising", "next_setting", "elevation", "azimuth"],
    "update": ["installed_version", "latest_version", "release_url", "in_progress"],
}


def _get_client() -> httpx.AsyncClient:
    """Create a new async HTTP client."""
    return httpx.AsyncClient(timeout=API_TIMEOUT, verify=False)


def _format_entity_lean(
    entity: dict[str, Any],
    domain: str | None = None,
    fields: list[str] | None = None,
) -> dict[str, Any]:
    """Format entity in lean mode to reduce token usage."""
    eid = entity.get("entity_id", "")
    if domain is None:
        domain = eid.split(".")[0] if "." in eid else ""

    result: dict[str, Any] = {
        "entity_id": eid,
        "state": entity.get("state"),
        "name": entity.get("attributes", {}).get("friendly_name", eid),
    }

    attrs = entity.get("attributes", {})

    if fields:
        for field in fields:
            if field.startswith("attr."):
                attr_name = field[5:]
                if attr_name in attrs:
                    result[attr_name] = attrs[attr_name]
            elif field in entity:
                result[field] = entity[field]
    else:
        # Include domain-specific important attributes
        important = DOMAIN_IMPORTANT_ATTRIBUTES.get(domain, [])
        for attr in important:
            if attr in attrs:
                result[attr] = attrs[attr]

    # Always include area if present
    if "area_id" in attrs:
        result["area"] = attrs["area_id"]

    return result


# --- API functions ---


async def get_config() -> dict[str, Any]:
    """Get Home Assistant configuration."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.get(f"{api_base}/config", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def get_version() -> str:
    """Get Home Assistant version string."""
    config = await get_config()
    return config.get("version", "unknown")


async def get_entity_state(entity_id: str) -> dict[str, Any]:
    """Get state of a single entity."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.get(
            f"{api_base}/states/{entity_id}", headers=headers
        )
        resp.raise_for_status()
        return resp.json()


async def get_all_states() -> list[dict[str, Any]]:
    """Get states of all entities."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.get(f"{api_base}/states", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def get_entities(
    domain: str | None = None,
    search_query: str | None = None,
    limit: int | None = None,
    fields: list[str] | None = None,
    detailed: bool = False,
) -> list[dict[str, Any]]:
    """Get entities with optional filtering."""
    all_states = await get_all_states()

    if domain:
        all_states = [
            s for s in all_states
            if s.get("entity_id", "").startswith(f"{domain}.")
        ]

    if search_query:
        query = search_query.lower()
        filtered = []
        for s in all_states:
            eid = s.get("entity_id", "").lower()
            name = s.get("attributes", {}).get("friendly_name", "").lower()
            state_val = str(s.get("state", "")).lower()
            if query in eid or query in name or query in state_val:
                filtered.append(s)
            else:
                # Search in attribute values
                for v in s.get("attributes", {}).values():
                    if isinstance(v, str) and query in v.lower():
                        filtered.append(s)
                        break
        all_states = filtered

    if limit and limit > 0:
        all_states = all_states[:limit]

    if detailed:
        return all_states

    results = []
    for s in all_states:
        d = s.get("entity_id", "").split(".")[0] if "." in s.get("entity_id", "") else ""
        results.append(_format_entity_lean(s, domain=d, fields=fields))
    return results


async def call_service(
    domain: str, service: str, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Call a Home Assistant service."""
    api_base = get_api_base()
    headers = get_headers()
    payload = data or {}
    async with _get_client() as client:
        resp = await client.post(
            f"{api_base}/services/{domain}/{service}",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status": "ok", "status_code": resp.status_code}


async def entity_action(
    entity_id: str, action: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Perform on/off/toggle action on an entity."""
    domain = entity_id.split(".")[0] if "." in entity_id else ""
    service_map = {"on": "turn_on", "off": "turn_off", "toggle": "toggle"}
    service = service_map.get(action.lower())
    if not service:
        return {"error": f"Unknown action '{action}'. Use 'on', 'off', or 'toggle'."}

    payload = {"entity_id": entity_id}
    if params:
        payload.update(params)
    return await call_service(domain, service, payload)


async def get_services() -> dict[str, Any]:
    """Get all available services."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.get(f"{api_base}/services", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def get_history(
    entity_id: str, hours: int = 24
) -> list[dict[str, Any]]:
    """Get state history for an entity."""
    api_base = get_api_base()
    headers = get_headers()
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    async with _get_client() as client:
        resp = await client.get(
            f"{api_base}/history/period/{start_str}",
            headers=headers,
            params={
                "filter_entity_id": entity_id,
                "minimal_response": "true",
                "end_time": end_str,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
        return []


async def get_logbook(
    hours: int = 24, entity_id: str | None = None
) -> list[dict[str, Any]]:
    """Get logbook entries."""
    api_base = get_api_base()
    headers = get_headers()
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    params: dict[str, str] = {}
    if entity_id:
        params["entity"] = entity_id

    async with _get_client() as client:
        resp = await client.get(
            f"{api_base}/logbook/{start_str}",
            headers=headers,
            params=params,
        )
        resp.raise_for_status()
        return resp.json()


async def get_error_log() -> dict[str, Any]:
    """Get and parse the Home Assistant error log."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.get(f"{api_base}/error_log", headers=headers)
        resp.raise_for_status()
        log_text = resp.text

    # Parse error/warning counts
    errors = len(re.findall(r"^.*\bERROR\b.*$", log_text, re.MULTILINE))
    warnings = len(re.findall(r"^.*\bWARNING\b.*$", log_text, re.MULTILINE))

    # Extract integration mentions
    integrations: dict[str, int] = {}
    for match in re.finditer(r"\[([a-z_]+(?:\.[a-z_]+)*)\]", log_text):
        name = match.group(1)
        integrations[name] = integrations.get(name, 0) + 1

    # Get last N lines for context
    lines = log_text.strip().split("\n")
    recent_lines = lines[-50:] if len(lines) > 50 else lines

    return {
        "error_count": errors,
        "warning_count": warnings,
        "integration_mentions": dict(
            sorted(integrations.items(), key=lambda x: x[1], reverse=True)[:20]
        ),
        "total_lines": len(lines),
        "recent_log": "\n".join(recent_lines),
    }


async def render_template(template: str) -> str:
    """Render a Jinja2 template via HA API."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.post(
            f"{api_base}/template",
            headers=headers,
            json={"template": template},
        )
        resp.raise_for_status()
        return resp.text


async def fire_event(
    event_type: str, event_data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Fire a Home Assistant event."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.post(
            f"{api_base}/events/{event_type}",
            headers=headers,
            json=event_data or {},
        )
        resp.raise_for_status()
        return resp.json()


async def get_areas() -> list[dict[str, Any]]:
    """Get all areas via the template API (REST API workaround)."""
    template = "{{ areas() | list | tojson }}"
    result = await render_template(template)
    import json
    try:
        area_ids = json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return []

    areas = []
    for area_id in area_ids:
        name_template = f"{{{{ area_name('{area_id}') }}}}"
        name = await render_template(name_template)
        areas.append({"area_id": area_id, "name": name.strip()})
    return areas


async def get_area_entities(area_id: str) -> list[str]:
    """Get all entity IDs for an area."""
    template = f"{{{{ area_entities('{area_id}') | list | tojson }}}}"
    result = await render_template(template)
    import json
    try:
        return json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return []


async def get_floor_areas(floor_id: str) -> list[str]:
    """Get areas for a floor."""
    template = f"{{{{ floor_areas('{floor_id}') | list | tojson }}}}"
    result = await render_template(template)
    import json
    try:
        return json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return []


async def get_system_overview() -> dict[str, Any]:
    """Build a comprehensive system overview."""
    all_states = await get_all_states()

    domains: dict[str, list[dict]] = {}
    for entity in all_states:
        eid = entity.get("entity_id", "")
        domain = eid.split(".")[0] if "." in eid else "unknown"
        domains.setdefault(domain, []).append(entity)

    overview: dict[str, Any] = {
        "total_entities": len(all_states),
        "domains": {},
    }

    for domain, entities in sorted(domains.items()):
        state_counts: dict[str, int] = {}
        for e in entities:
            st = str(e.get("state", "unknown"))
            state_counts[st] = state_counts.get(st, 0) + 1

        # Collect areas
        areas: set[str] = set()
        for e in entities:
            area = e.get("attributes", {}).get("area_id")
            if area:
                areas.add(area)

        overview["domains"][domain] = {
            "count": len(entities),
            "states": state_counts,
            "areas": sorted(areas) if areas else [],
            "sample_entities": [
                e.get("entity_id") for e in entities[:5]
            ],
        }

    # Sort domains by count
    overview["top_domains"] = sorted(
        overview["domains"].items(), key=lambda x: x[1]["count"], reverse=True
    )[:10]

    return overview


async def domain_summary(domain: str) -> dict[str, Any]:
    """Get summary for a specific domain."""
    entities = await get_entities(domain=domain, detailed=True)

    state_counts: dict[str, int] = {}
    attr_counts: dict[str, int] = {}
    examples_by_state: dict[str, list[str]] = {}

    for e in entities:
        st = str(e.get("state", "unknown"))
        state_counts[st] = state_counts.get(st, 0) + 1
        examples_by_state.setdefault(st, [])
        if len(examples_by_state[st]) < 3:
            examples_by_state[st].append(e.get("entity_id", ""))
        for attr_name in e.get("attributes", {}):
            attr_counts[attr_name] = attr_counts.get(attr_name, 0) + 1

    top_attrs = sorted(attr_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "domain": domain,
        "total": len(entities),
        "states": state_counts,
        "examples_by_state": examples_by_state,
        "top_attributes": dict(top_attrs),
    }


async def search_entities(query: str) -> dict[str, Any]:
    """Search entities with structured results."""
    entities = await get_entities(search_query=query, detailed=True)

    domain_breakdown: dict[str, int] = {}
    results = []
    for e in entities:
        eid = e.get("entity_id", "")
        domain = eid.split(".")[0] if "." in eid else ""
        domain_breakdown[domain] = domain_breakdown.get(domain, 0) + 1
        results.append(_format_entity_lean(e, domain=domain))

    return {
        "count": len(results),
        "domain_breakdown": domain_breakdown,
        "results": results,
    }


async def get_automations() -> list[dict[str, Any]]:
    """Get all automations with key details."""
    entities = await get_entities(domain="automation", detailed=True)
    automations = []
    for e in entities:
        attrs = e.get("attributes", {})
        automations.append({
            "entity_id": e.get("entity_id"),
            "id": attrs.get("id"),
            "alias": attrs.get("friendly_name", ""),
            "state": e.get("state"),
            "last_triggered": attrs.get("last_triggered"),
            "mode": attrs.get("mode", "single"),
            "current": attrs.get("current", 0),
        })
    return automations


async def get_scenes() -> list[dict[str, Any]]:
    """Get all scenes."""
    entities = await get_entities(domain="scene", detailed=True)
    scenes = []
    for e in entities:
        attrs = e.get("attributes", {})
        scenes.append({
            "entity_id": e.get("entity_id"),
            "name": attrs.get("friendly_name", ""),
            "state": e.get("state"),
        })
    return scenes


async def get_scripts() -> list[dict[str, Any]]:
    """Get all scripts."""
    entities = await get_entities(domain="script", detailed=True)
    scripts = []
    for e in entities:
        attrs = e.get("attributes", {})
        scripts.append({
            "entity_id": e.get("entity_id"),
            "name": attrs.get("friendly_name", ""),
            "state": e.get("state"),
            "last_triggered": attrs.get("last_triggered"),
            "mode": attrs.get("mode", "single"),
        })
    return scripts


async def check_api_connection() -> dict[str, Any]:
    """Check if the HA API is reachable and authenticated."""
    try:
        config = await get_config()
        return {
            "connected": True,
            "version": config.get("version", "unknown"),
            "location_name": config.get("location_name", ""),
            "time_zone": config.get("time_zone", ""),
        }
    except httpx.HTTPStatusError as e:
        return {
            "connected": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}


# ============================================================================
# REST API - Additional endpoints
# ============================================================================


async def check_config() -> dict[str, Any]:
    """Validate HA configuration without restarting."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.post(
            f"{api_base}/config/core/check_config", headers=headers
        )
        resp.raise_for_status()
        return resp.json()


async def get_components() -> list[str]:
    """Get all loaded integrations/components."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.get(f"{api_base}/components", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def get_camera_image(entity_id: str) -> bytes:
    """Get a camera snapshot as image bytes."""
    api_base = get_api_base()
    headers = get_headers()
    # Camera proxy doesn't need Content-Type: application/json
    img_headers = {k: v for k, v in headers.items() if k != "Content-Type"}
    async with _get_client() as client:
        resp = await client.get(
            f"{api_base}/camera_proxy/{entity_id}", headers=img_headers
        )
        resp.raise_for_status()
        return resp.content


async def get_calendars() -> list[dict[str, Any]]:
    """List all calendar entities."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.get(f"{api_base}/calendars", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def get_calendar_events(
    entity_id: str, days: int = 7
) -> list[dict[str, Any]]:
    """Get calendar events for the next N days."""
    api_base = get_api_base()
    headers = get_headers()
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)
    start_str = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    async with _get_client() as client:
        resp = await client.get(
            f"{api_base}/calendars/{entity_id}",
            headers=headers,
            params={"start": start_str, "end": end_str},
        )
        resp.raise_for_status()
        return resp.json()


async def get_persons() -> list[dict[str, Any]]:
    """Get all person entities with location data."""
    entities = await get_entities(domain="person", detailed=True)
    persons = []
    for e in entities:
        attrs = e.get("attributes", {})
        persons.append({
            "entity_id": e.get("entity_id"),
            "name": attrs.get("friendly_name", ""),
            "state": e.get("state"),  # home / not_home / zone name
            "source": attrs.get("source"),
            "latitude": attrs.get("latitude"),
            "longitude": attrs.get("longitude"),
            "gps_accuracy": attrs.get("gps_accuracy"),
        })
    return persons


async def get_weather(entity_id: str | None = None) -> dict[str, Any] | list[dict[str, Any]]:
    """Get weather data. If no entity_id, returns all weather entities."""
    if entity_id:
        state = await get_entity_state(entity_id)
        attrs = state.get("attributes", {})
        return {
            "entity_id": entity_id,
            "state": state.get("state"),
            "temperature": attrs.get("temperature"),
            "humidity": attrs.get("humidity"),
            "pressure": attrs.get("pressure"),
            "wind_speed": attrs.get("wind_speed"),
            "wind_bearing": attrs.get("wind_bearing"),
            "forecast": attrs.get("forecast", []),
        }
    entities = await get_entities(domain="weather", detailed=True)
    results = []
    for e in entities:
        attrs = e.get("attributes", {})
        results.append({
            "entity_id": e.get("entity_id"),
            "name": attrs.get("friendly_name", ""),
            "state": e.get("state"),
            "temperature": attrs.get("temperature"),
            "humidity": attrs.get("humidity"),
            "wind_speed": attrs.get("wind_speed"),
        })
    return results


# ============================================================================
# Supervisor API
# ============================================================================


async def _supervisor_get(path: str) -> Any:
    """Make a GET request to the Supervisor API."""
    headers = get_supervisor_headers()
    async with _get_client() as client:
        resp = await client.get(
            f"{SUPERVISOR_URL}{path}", headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        # Supervisor API wraps results in {"result": "ok", "data": {...}}
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data


async def _supervisor_post(path: str, json_data: dict | None = None) -> Any:
    """Make a POST request to the Supervisor API."""
    headers = get_supervisor_headers()
    async with _get_client() as client:
        resp = await client.post(
            f"{SUPERVISOR_URL}{path}",
            headers=headers,
            json=json_data or {},
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data


async def get_host_info() -> dict[str, Any]:
    """Get host system information (hostname, OS, disk, memory, etc.)."""
    return await _supervisor_get("/host/info")


async def get_available_updates() -> list[dict[str, Any]]:
    """Check for available updates (Core, OS, Supervisor, add-ons)."""
    return await _supervisor_get("/available_updates")


async def get_core_info() -> dict[str, Any]:
    """Get HA Core container info (version, arch, machine type)."""
    return await _supervisor_get("/core/info")


async def list_addons() -> list[dict[str, Any]]:
    """List all installed add-ons with status."""
    data = await _supervisor_get("/addons")
    return data.get("addons", data) if isinstance(data, dict) else data


async def get_addon_info(slug: str) -> dict[str, Any]:
    """Get detailed info for a specific add-on."""
    return await _supervisor_get(f"/addons/{slug}/info")


async def addon_action(slug: str, action: str) -> dict[str, Any]:
    """Start, stop, or restart an add-on.

    Args:
        slug: Add-on slug (e.g. 'core_mosquitto').
        action: One of 'start', 'stop', 'restart'.
    """
    if action not in ("start", "stop", "restart"):
        return {"error": f"Invalid action '{action}'. Use 'start', 'stop', or 'restart'."}
    return await _supervisor_post(f"/addons/{slug}/{action}")


async def list_backups() -> list[dict[str, Any]]:
    """List all backups."""
    data = await _supervisor_get("/backups")
    return data.get("backups", data) if isinstance(data, dict) else data


async def create_backup(
    name: str | None = None, partial: bool = False,
    addons: list[str] | None = None, folders: list[str] | None = None,
) -> dict[str, Any]:
    """Create a backup.

    Args:
        name: Optional backup name.
        partial: If True, create partial backup with specified addons/folders.
        addons: List of add-on slugs to include (partial only).
        folders: List of folders to include (partial only).
    """
    if partial:
        payload: dict[str, Any] = {}
        if name:
            payload["name"] = name
        if addons:
            payload["addons"] = addons
        if folders:
            payload["folders"] = folders
        return await _supervisor_post("/backups/new/partial", payload)
    else:
        payload = {"name": name} if name else {}
        return await _supervisor_post("/backups/new/full", payload)


# ============================================================================
# Device / Floor / Label / Zone Registry (via template API)
# ============================================================================


async def get_devices() -> list[dict[str, Any]]:
    """Get all devices via template API."""
    import json as _json
    # Get device IDs
    tpl = "{{ states | map(attribute='entity_id') | map('device_id') | reject('none') | unique | list | tojson }}"
    result = await render_template(tpl)
    try:
        device_ids = _json.loads(result)
    except (ValueError, TypeError):
        return []

    devices = []
    for did in device_ids:
        if not did:
            continue
        info_tpl = (
            "{% set d = device_attr('" + did + "', 'name') %}"
            "{% set m = device_attr('" + did + "', 'manufacturer') %}"
            "{% set mo = device_attr('" + did + "', 'model') %}"
            "{% set a = device_attr('" + did + "', 'area_id') %}"
            "{% set di = device_attr('" + did + "', 'disabled_by') %}"
            '{"name":"{{ d }}","manufacturer":"{{ m }}","model":"{{ mo }}",'
            '"area_id":"{{ a }}","disabled_by":"{{ di }}"}'
        )
        try:
            info_str = await render_template(info_tpl)
            info = _json.loads(info_str)
            info["device_id"] = did
            devices.append(info)
        except Exception:
            devices.append({"device_id": did, "name": "unknown"})
    return devices


async def get_device_entities(device_id: str) -> list[str]:
    """Get entity IDs for a device."""
    import json as _json
    tpl = f"{{{{ device_entities('{device_id}') | list | tojson }}}}"
    result = await render_template(tpl)
    try:
        return _json.loads(result)
    except (ValueError, TypeError):
        return []


async def get_floors() -> list[dict[str, Any]]:
    """Get all floors via template API."""
    import json as _json
    tpl = "{{ floors() | list | tojson }}"
    result = await render_template(tpl)
    try:
        floor_ids = _json.loads(result)
    except (ValueError, TypeError):
        return []

    floors = []
    for fid in floor_ids:
        name_tpl = f"{{{{ floor_name('{fid}') }}}}"
        name = await render_template(name_tpl)
        areas = await get_floor_areas(fid)
        floors.append({"floor_id": fid, "name": name.strip(), "areas": areas})
    return floors


async def get_labels() -> list[dict[str, Any]]:
    """Get all labels via template API."""
    import json as _json
    tpl = "{{ labels() | list | tojson }}"
    result = await render_template(tpl)
    try:
        label_ids = _json.loads(result)
    except (ValueError, TypeError):
        return []

    labels_list = []
    for lid in label_ids:
        name_tpl = f"{{{{ label_name('{lid}') }}}}"
        name = await render_template(name_tpl)
        entities_tpl = f"{{{{ label_entities('{lid}') | list | tojson }}}}"
        entities_str = await render_template(entities_tpl)
        try:
            entities = _json.loads(entities_str)
        except (ValueError, TypeError):
            entities = []
        labels_list.append({
            "label_id": lid,
            "name": name.strip(),
            "entity_count": len(entities),
            "entities": entities[:20],  # Limit for token efficiency
        })
    return labels_list


async def get_label_entities(label_id: str) -> list[str]:
    """Get entity IDs for a label."""
    import json as _json
    tpl = f"{{{{ label_entities('{label_id}') | list | tojson }}}}"
    result = await render_template(tpl)
    try:
        return _json.loads(result)
    except (ValueError, TypeError):
        return []


# ============================================================================
# State Setting (for input_* helpers)
# ============================================================================


async def set_state(entity_id: str, state: str, attributes: dict[str, Any] | None = None) -> dict[str, Any]:
    """Set the state of an entity directly via REST API.

    Primarily useful for input_* helpers (input_boolean, input_number, etc.).
    """
    api_base = get_api_base()
    headers = get_headers()
    payload: dict[str, Any] = {"state": state}
    if attributes:
        payload["attributes"] = attributes
    async with _get_client() as client:
        resp = await client.post(
            f"{api_base}/states/{entity_id}",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


# ============================================================================
# Conversation API
# ============================================================================


async def conversation_process(text: str, language: str = "en") -> dict[str, Any]:
    """Send text to HA's conversation agent."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.post(
            f"{api_base}/conversation/process",
            headers=headers,
            json={"text": text, "language": language},
        )
        resp.raise_for_status()
        return resp.json()


# ============================================================================
# Automation / Script / Scene CRUD (via REST API config endpoints)
# ============================================================================


async def get_automation_config(automation_id: str) -> dict[str, Any]:
    """Get automation config by its ID (not entity_id)."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.get(
            f"{api_base}/config/automation/config/{automation_id}",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


async def update_automation_config(automation_id: str, config: dict[str, Any]) -> dict[str, Any]:
    """Create or update an automation by its ID."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.post(
            f"{api_base}/config/automation/config/{automation_id}",
            headers=headers,
            json=config,
        )
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status": "ok", "status_code": resp.status_code}


async def delete_automation_config(automation_id: str) -> dict[str, Any]:
    """Delete an automation by its ID."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.delete(
            f"{api_base}/config/automation/config/{automation_id}",
            headers=headers,
        )
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status": "ok", "status_code": resp.status_code}


async def get_script_config(script_id: str) -> dict[str, Any]:
    """Get script config by its ID."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.get(
            f"{api_base}/config/script/config/{script_id}",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


async def update_script_config(script_id: str, config: dict[str, Any]) -> dict[str, Any]:
    """Create or update a script by its ID."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.post(
            f"{api_base}/config/script/config/{script_id}",
            headers=headers,
            json=config,
        )
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status": "ok", "status_code": resp.status_code}


async def delete_script_config(script_id: str) -> dict[str, Any]:
    """Delete a script by its ID."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.delete(
            f"{api_base}/config/script/config/{script_id}",
            headers=headers,
        )
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status": "ok", "status_code": resp.status_code}


# ============================================================================
# Todo List Management
# ============================================================================


async def get_todo_items(entity_id: str) -> list[dict[str, Any]]:
    """Get todo items for a todo list entity."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.get(
            f"{api_base}/states/{entity_id}",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


async def add_todo_item(entity_id: str, item: str, due_date: str | None = None) -> dict[str, Any]:
    """Add a todo item."""
    data: dict[str, Any] = {"entity_id": entity_id, "item": item}
    if due_date:
        data["due_date"] = due_date
    return await call_service("todo", "add_item", data)


async def update_todo_item(
    entity_id: str, item: str,
    rename: str | None = None, status: str | None = None,
) -> dict[str, Any]:
    """Update a todo item (rename or change status)."""
    data: dict[str, Any] = {"entity_id": entity_id, "item": item}
    if rename:
        data["rename"] = rename
    if status:
        data["status"] = status
    return await call_service("todo", "update_item", data)


async def remove_todo_item(entity_id: str, item: str) -> dict[str, Any]:
    """Remove a todo item."""
    return await call_service("todo", "remove_item", {"entity_id": entity_id, "item": item})


# ============================================================================
# Calendar Event CRUD
# ============================================================================


async def create_calendar_event(
    entity_id: str, summary: str,
    start: str, end: str,
    description: str | None = None, location: str | None = None,
) -> dict[str, Any]:
    """Create a calendar event."""
    data: dict[str, Any] = {
        "entity_id": entity_id,
        "summary": summary,
        "start_date_time": start,
        "end_date_time": end,
    }
    if description:
        data["description"] = description
    if location:
        data["location"] = location
    return await call_service("calendar", "create_event", data)


async def delete_calendar_event(entity_id: str, uid: str) -> dict[str, Any]:
    """Delete a calendar event by uid."""
    return await call_service("calendar", "delete_event", {"entity_id": entity_id, "uid": uid})


# ============================================================================
# Dashboard / Lovelace Management
# ============================================================================


async def get_dashboards() -> list[dict[str, Any]]:
    """List all Lovelace dashboards via template API."""
    # The REST API doesn't have a direct dashboard list endpoint,
    # but we can use /api/lovelace/dashboards
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        try:
            resp = await client.get(
                f"{api_base}/lovelace/dashboards", headers=headers
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return []


async def get_dashboard_config(dashboard_id: str | None = None) -> dict[str, Any]:
    """Get Lovelace dashboard configuration."""
    api_base = get_api_base()
    headers = get_headers()
    url_path = dashboard_id or "lovelace"
    async with _get_client() as client:
        resp = await client.get(
            f"{api_base}/lovelace/config/{url_path}", headers=headers
        )
        resp.raise_for_status()
        return resp.json()


async def save_dashboard_config(config: dict[str, Any], dashboard_id: str | None = None) -> dict[str, Any]:
    """Save Lovelace dashboard configuration."""
    api_base = get_api_base()
    headers = get_headers()
    url_path = dashboard_id or "lovelace"
    async with _get_client() as client:
        resp = await client.post(
            f"{api_base}/lovelace/config/{url_path}",
            headers=headers,
            json=config,
        )
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status": "ok"}


# ============================================================================
# Bulk Operations
# ============================================================================


async def bulk_control(entity_ids: list[str], action: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Control multiple entities at once."""
    results = []
    for eid in entity_ids:
        try:
            result = await entity_action(eid, action, params)
            results.append({"entity_id": eid, "result": "ok"})
        except Exception as e:
            results.append({"entity_id": eid, "error": str(e)})
    return results


async def bulk_get_states(entity_ids: list[str]) -> list[dict[str, Any]]:
    """Get states of multiple entities at once."""
    results = []
    all_states = await get_all_states()
    state_map = {s.get("entity_id"): s for s in all_states}
    for eid in entity_ids:
        if eid in state_map:
            domain = eid.split(".")[0] if "." in eid else ""
            results.append(_format_entity_lean(state_map[eid], domain=domain))
        else:
            results.append({"entity_id": eid, "error": "not_found"})
    return results


# ============================================================================
# Deep Search
# ============================================================================


async def deep_search(query: str) -> dict[str, Any]:
    """Search across entities, automations, scripts, scenes, areas, devices."""
    q = query.lower()
    results: dict[str, Any] = {"query": query, "matches": {}}

    # Search entities
    entity_matches = await search_entities(q)
    if entity_matches.get("count", 0) > 0:
        results["matches"]["entities"] = entity_matches

    # Search automations
    automations = await get_automations()
    auto_matches = [
        a for a in automations
        if q in a.get("alias", "").lower()
        or q in a.get("entity_id", "").lower()
    ]
    if auto_matches:
        results["matches"]["automations"] = auto_matches

    # Search scenes
    scenes = await get_scenes()
    scene_matches = [
        s for s in scenes
        if q in s.get("name", "").lower()
        or q in s.get("entity_id", "").lower()
    ]
    if scene_matches:
        results["matches"]["scenes"] = scene_matches

    # Search scripts
    scripts = await get_scripts()
    script_matches = [
        s for s in scripts
        if q in s.get("name", "").lower()
        or q in s.get("entity_id", "").lower()
    ]
    if script_matches:
        results["matches"]["scripts"] = script_matches

    # Search areas
    areas = await get_areas()
    area_matches = [
        a for a in areas
        if q in a.get("name", "").lower()
        or q in a.get("area_id", "").lower()
    ]
    if area_matches:
        results["matches"]["areas"] = area_matches

    total = sum(
        len(v) if isinstance(v, list) else v.get("count", 0)
        for v in results["matches"].values()
    )
    results["total_matches"] = total
    return results


# ============================================================================
# Supervisor API — Logs & Diagnostics
# ============================================================================


async def get_supervisor_logs(lines: int = 100) -> str:
    """Get Supervisor logs."""
    headers = get_supervisor_headers()
    # Override Accept to get plain text
    headers["Accept"] = "text/plain"
    async with _get_client() as client:
        resp = await client.get(
            f"{SUPERVISOR_URL}/supervisor/logs",
            headers=headers,
        )
        resp.raise_for_status()
        text = resp.text
        log_lines = text.strip().split("\n")
        return "\n".join(log_lines[-lines:])


async def get_core_logs(lines: int = 100) -> str:
    """Get HA Core logs (structured)."""
    headers = get_supervisor_headers()
    headers["Accept"] = "text/plain"
    async with _get_client() as client:
        resp = await client.get(
            f"{SUPERVISOR_URL}/core/logs",
            headers=headers,
        )
        resp.raise_for_status()
        text = resp.text
        log_lines = text.strip().split("\n")
        return "\n".join(log_lines[-lines:])


async def get_addon_logs(slug: str, lines: int = 100) -> str:
    """Get logs for a specific add-on."""
    headers = get_supervisor_headers()
    headers["Accept"] = "text/plain"
    async with _get_client() as client:
        resp = await client.get(
            f"{SUPERVISOR_URL}/addons/{slug}/logs",
            headers=headers,
        )
        resp.raise_for_status()
        text = resp.text
        log_lines = text.strip().split("\n")
        return "\n".join(log_lines[-lines:])


async def get_os_info() -> dict[str, Any]:
    """Get HAOS info (version, board, data disk)."""
    return await _supervisor_get("/os/info")


async def get_network_info() -> dict[str, Any]:
    """Get network configuration."""
    return await _supervisor_get("/network/info")


async def get_hardware_info() -> dict[str, Any]:
    """Get hardware info (USB, GPIO, serial ports)."""
    return await _supervisor_get("/hardware/info")


async def get_resolution_info() -> dict[str, Any]:
    """Get system resolution center (issues, suggestions, unhealthy flags)."""
    return await _supervisor_get("/resolution/info")


async def get_store_addons() -> list[dict[str, Any]]:
    """Get available add-ons from the store."""
    data = await _supervisor_get("/store")
    if isinstance(data, dict):
        return data.get("addons", [])
    return []


# ============================================================================
# Automation Traces
# ============================================================================


async def get_automation_traces(automation_id: str) -> list[dict[str, Any]]:
    """Get execution traces for an automation."""
    api_base = get_api_base()
    headers = get_headers()
    async with _get_client() as client:
        resp = await client.get(
            f"{api_base}/config/automation/trace/{automation_id}",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


# ============================================================================
# Config File Access (via Supervisor add-on API)
# ============================================================================


async def list_config_files(path: str = "") -> list[str]:
    """List files in /config directory.

    Uses the HA REST API with a template to list directory contents.
    Only works within /config (homeassistant_config mapped in add-on).
    """
    import os
    config_dir = "/config" if os.path.isdir("/config") else "/homeassistant"
    target = os.path.join(config_dir, path.lstrip("/"))
    try:
        entries = os.listdir(target)
        return sorted(entries)
    except Exception as e:
        return [f"Error: {e}"]


async def read_config_file(path: str) -> str:
    """Read a config file from /config directory."""
    import os
    config_dir = "/config" if os.path.isdir("/config") else "/homeassistant"
    target = os.path.join(config_dir, path.lstrip("/"))
    # Security: prevent directory traversal
    real_target = os.path.realpath(target)
    real_config = os.path.realpath(config_dir)
    if not real_target.startswith(real_config):
        return "Error: Path traversal not allowed"
    try:
        with open(target, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"


async def write_config_file(path: str, content: str) -> dict[str, Any]:
    """Write content to a config file in /config directory.

    Creates a .bak backup before overwriting.
    """
    import os
    config_dir = "/config" if os.path.isdir("/config") else "/homeassistant"
    target = os.path.join(config_dir, path.lstrip("/"))
    # Security: prevent directory traversal
    real_target = os.path.realpath(target)
    real_config = os.path.realpath(config_dir)
    if not real_target.startswith(real_config):
        return {"error": "Path traversal not allowed"}
    # Prevent writing secrets
    basename = os.path.basename(target)
    if basename in ("secrets.yaml", ".storage", "home-assistant_v2.db"):
        return {"error": f"Writing to {basename} is not allowed for safety"}
    try:
        # Backup existing file
        if os.path.exists(target):
            import shutil
            shutil.copy2(target, target + ".bak")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w") as f:
            f.write(content)
        return {"status": "ok", "path": path, "bytes": len(content)}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Reload Configuration
# ============================================================================


async def reload_core_config() -> dict[str, Any]:
    """Reload core configuration without restarting HA."""
    return await call_service("homeassistant", "reload_core_config", {})


async def reload_automations() -> dict[str, Any]:
    """Reload automations from config."""
    return await call_service("automation", "reload", {})


async def reload_scripts() -> dict[str, Any]:
    """Reload scripts from config."""
    return await call_service("script", "reload", {})


async def reload_scenes() -> dict[str, Any]:
    """Reload scenes from config."""
    return await call_service("scene", "reload", {})


async def reload_all() -> dict[str, Any]:
    """Reload all YAML configuration (automations, scripts, scenes, groups, etc.)."""
    return await call_service("homeassistant", "reload_all", {})
