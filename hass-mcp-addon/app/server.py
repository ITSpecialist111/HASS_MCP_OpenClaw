"""HASS MCP Server - MCP tool/resource/prompt definitions.

This module registers all MCP tools, resources, and prompts on the FastMCP server.
"""

import json
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import hass

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "HASS-MCP",
    host="0.0.0.0",
    port=8080,
)


# ============================================================================
# TOOLS
# ============================================================================


@mcp.tool()
async def get_version() -> str:
    """Get the Home Assistant version.

    Returns the current version string of the connected Home Assistant instance.
    """
    try:
        return await hass.get_version()
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def check_connection() -> str:
    """Check the connection to Home Assistant.

    Verifies that the MCP server can reach and authenticate with Home Assistant.
    Returns connection status, version, location name, and timezone.
    """
    result = await hass.check_api_connection()
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_entity(
    entity_id: str,
    detailed: bool = False,
    fields: list[str] | None = None,
) -> str:
    """Get the state of a specific Home Assistant entity.

    Args:
        entity_id: The entity ID (e.g. 'light.living_room', 'sensor.temperature').
        detailed: If True, return all attributes. Defaults to lean output.
        fields: Optional list of specific fields to include. Use 'attr.X' for attributes.

    Returns:
        JSON with entity state and attributes.
    """
    try:
        state = await hass.get_entity_state(entity_id)
        if detailed:
            return json.dumps(state, indent=2, default=str)
        domain = entity_id.split(".")[0] if "." in entity_id else ""
        lean = hass._format_entity_lean(state, domain=domain, fields=fields)
        return json.dumps(lean, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def list_entities(
    domain: str | None = None,
    search_query: str | None = None,
    limit: int | None = None,
    fields: list[str] | None = None,
    detailed: bool = False,
) -> str:
    """List Home Assistant entities with optional filtering.

    Args:
        domain: Filter by domain (e.g. 'light', 'sensor', 'switch', 'climate').
        search_query: Search text to filter by name, ID, state, or attributes.
        limit: Maximum number of entities to return.
        fields: Specific fields to include. Use 'attr.X' for attributes.
        detailed: If True, return all attributes. Defaults to lean output.

    Returns:
        JSON array of matching entities.
    """
    try:
        entities = await hass.get_entities(
            domain=domain,
            search_query=search_query,
            limit=limit,
            fields=fields,
            detailed=detailed,
        )
        return json.dumps(entities, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def entity_action(
    entity_id: str,
    action: str,
    params: dict[str, Any] | None = None,
) -> str:
    """Turn on, turn off, or toggle a Home Assistant entity.

    Args:
        entity_id: The entity to control (e.g. 'light.bedroom', 'switch.fan').
        action: One of 'on', 'off', or 'toggle'.
        params: Optional parameters (e.g. {'brightness': 128} for lights,
                {'temperature': 22} for climate).

    Returns:
        JSON with the service call result.
    """
    try:
        result = await hass.entity_action(entity_id, action, params)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def call_service(
    domain: str,
    service: str,
    data: dict[str, Any] | None = None,
) -> str:
    """Call any Home Assistant service.

    This is the low-level service call tool. Use this for services not covered
    by entity_action (e.g. fan.set_percentage, media_player.play_media,
    notify.mobile_app, tts.google_translate_say).

    Args:
        domain: Service domain (e.g. 'light', 'fan', 'media_player', 'notify').
        service: Service name (e.g. 'turn_on', 'set_percentage', 'play_media').
        data: Service data including target entity_id and parameters.

    Returns:
        JSON with the service call result.
    """
    try:
        result = await hass.call_service(domain, service, data)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def list_services() -> str:
    """List all available Home Assistant services.

    Returns a summary of all service domains and their available services.
    Useful for discovering what actions can be performed.
    """
    try:
        services = await hass.get_services()
        # Summarize: domain -> list of service names
        summary = {}
        for item in services:
            domain = item.get("domain", "unknown")
            svc_names = list(item.get("services", {}).keys())
            summary[domain] = svc_names
        return json.dumps(summary, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def search_entities(query: str) -> str:
    """Search for entities by text query.

    Searches entity IDs, friendly names, states, and attribute values.
    Returns structured results with count and domain breakdown.

    Args:
        query: Search text (case-insensitive).

    Returns:
        JSON with count, domain_breakdown, and results.
    """
    try:
        result = await hass.search_entities(query)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def domain_summary(domain: str) -> str:
    """Get a summary of entities in a specific domain.

    Shows total count, state distribution, example entities per state,
    and most common attributes.

    Args:
        domain: The domain to summarize (e.g. 'light', 'sensor', 'automation').

    Returns:
        JSON summary of the domain.
    """
    try:
        result = await hass.domain_summary(domain)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def system_overview() -> str:
    """Get a comprehensive overview of the entire Home Assistant instance.

    Returns total entity count, per-domain counts and state distributions,
    area distribution, and top domains.
    """
    try:
        result = await hass.get_system_overview()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def list_automations() -> str:
    """List all Home Assistant automations.

    Returns each automation's entity_id, ID, alias, state (on/off),
    last_triggered time, and mode.
    """
    try:
        result = await hass.get_automations()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def list_scenes() -> str:
    """List all Home Assistant scenes.

    Returns each scene's entity_id, name, and state.
    """
    try:
        result = await hass.get_scenes()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def list_scripts() -> str:
    """List all Home Assistant scripts.

    Returns each script's entity_id, name, state, last_triggered, and mode.
    """
    try:
        result = await hass.get_scripts()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def activate_scene(scene_entity_id: str) -> str:
    """Activate a Home Assistant scene.

    Args:
        scene_entity_id: The scene entity ID (e.g. 'scene.movie_time').

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.call_service(
            "scene", "turn_on", {"entity_id": scene_entity_id}
        )
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def run_script(
    script_entity_id: str,
    variables: dict[str, Any] | None = None,
) -> str:
    """Run a Home Assistant script.

    Args:
        script_entity_id: The script entity ID (e.g. 'script.morning_routine').
        variables: Optional variables to pass to the script.

    Returns:
        JSON with the result.
    """
    try:
        data: dict[str, Any] = {"entity_id": script_entity_id}
        if variables:
            data["variables"] = variables
        result = await hass.call_service("script", "turn_on", data)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def trigger_automation(automation_entity_id: str) -> str:
    """Manually trigger a Home Assistant automation.

    Args:
        automation_entity_id: The automation entity ID (e.g. 'automation.motion_lights').

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.call_service(
            "automation", "trigger", {"entity_id": automation_entity_id}
        )
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def toggle_automation(
    automation_entity_id: str, enable: bool = True
) -> str:
    """Enable or disable a Home Assistant automation.

    Args:
        automation_entity_id: The automation entity ID.
        enable: True to enable, False to disable.

    Returns:
        JSON with the result.
    """
    try:
        service = "turn_on" if enable else "turn_off"
        result = await hass.call_service(
            "automation", service, {"entity_id": automation_entity_id}
        )
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_history(entity_id: str, hours: int = 24) -> str:
    """Get the state change history for an entity.

    Args:
        entity_id: The entity to get history for.
        hours: Number of hours of history (default 24).

    Returns:
        JSON array of timestamped state changes.
    """
    try:
        result = await hass.get_history(entity_id, hours)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_logbook(
    hours: int = 24, entity_id: str | None = None
) -> str:
    """Get logbook entries showing what happened in Home Assistant.

    Args:
        hours: Number of hours of history (default 24).
        entity_id: Optional entity to filter logbook for.

    Returns:
        JSON array of logbook entries.
    """
    try:
        result = await hass.get_logbook(hours, entity_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_error_log() -> str:
    """Get the Home Assistant error log with analysis.

    Returns error count, warning count, top integration mentions,
    and recent log lines.
    """
    try:
        result = await hass.get_error_log()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def render_template(template: str) -> str:
    """Render a Jinja2 template using Home Assistant's template engine.

    This is extremely powerful — it can access any entity state, perform
    math, format dates, list areas/devices, and much more.

    Args:
        template: A Jinja2 template string (e.g. '{{ states("sensor.temp") }}').

    Returns:
        The rendered template result.
    """
    try:
        return await hass.render_template(template)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def fire_event(
    event_type: str, event_data: dict[str, Any] | None = None
) -> str:
    """Fire a custom event on the Home Assistant event bus.

    Args:
        event_type: Event type name (e.g. 'my_custom_event').
        event_data: Optional data payload for the event.

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.fire_event(event_type, event_data)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_areas() -> str:
    """Get all configured areas/rooms in Home Assistant.

    Returns area IDs and names.
    """
    try:
        result = await hass.get_areas()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_area_entities(area_id: str) -> str:
    """Get all entities assigned to a specific area.

    Args:
        area_id: The area ID (e.g. 'living_room', 'kitchen').

    Returns:
        JSON array of entity IDs in the area.
    """
    try:
        result = await hass.get_area_entities(area_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def restart_ha() -> str:
    """Restart Home Assistant.

    WARNING: This will restart the entire Home Assistant instance.
    All automations will be reloaded. There will be a brief period of downtime.

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.call_service("homeassistant", "restart", {})
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def send_notification(
    message: str,
    title: str | None = None,
    service: str = "persistent_notification",
    target: str | None = None,
    data: dict[str, Any] | None = None,
) -> str:
    """Send a notification through Home Assistant.

    Args:
        message: Notification message text.
        title: Optional notification title.
        service: Notification service (default: 'persistent_notification').
                 Use 'notify.mobile_app_PHONE' for mobile push.
        target: Optional target for the notification.
        data: Optional extra data (e.g. for mobile push actions, images).

    Returns:
        JSON with the result.
    """
    try:
        if service == "persistent_notification":
            payload: dict[str, Any] = {"message": message}
            if title:
                payload["title"] = title
            result = await hass.call_service(
                "persistent_notification", "create", payload
            )
        else:
            # parse domain.service format
            parts = service.split(".", 1)
            domain = parts[0] if len(parts) > 1 else "notify"
            svc = parts[1] if len(parts) > 1 else parts[0]
            payload = {"message": message}
            if title:
                payload["title"] = title
            if target:
                payload["target"] = target
            if data:
                payload["data"] = data
            result = await hass.call_service(domain, svc, payload)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Configuration & Diagnostics
# ============================================================================


@mcp.tool()
async def check_config() -> str:
    """Validate the Home Assistant configuration without restarting.

    Always run this before calling restart_ha to catch config errors.
    Returns validation result (valid/invalid with error details).
    """
    try:
        result = await hass.check_config()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def list_integrations() -> str:
    """List all loaded integrations/components.

    Returns all active integration names (e.g. 'mqtt', 'zwave_js', 'hue').
    Useful for checking if a specific integration is loaded.
    """
    try:
        components = await hass.get_components()
        return json.dumps({
            "count": len(components),
            "integrations": sorted(components),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Camera & Calendar
# ============================================================================


@mcp.tool()
async def get_camera_image(camera_entity_id: str) -> str:
    """Get a snapshot image from a camera entity.

    Returns the image as a base64-encoded string suitable for
    multimodal AI analysis.

    Args:
        camera_entity_id: The camera entity ID (e.g. 'camera.front_door').

    Returns:
        Base64-encoded image data with mime type.
    """
    import base64
    try:
        image_bytes = await hass.get_camera_image(camera_entity_id)
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return json.dumps({
            "entity_id": camera_entity_id,
            "mime_type": "image/jpeg",
            "size_bytes": len(image_bytes),
            "image_base64": b64,
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_calendar_events(
    calendar_entity_id: str | None = None, days: int = 7
) -> str:
    """Get calendar events from Home Assistant.

    Args:
        calendar_entity_id: Specific calendar entity (e.g. 'calendar.family').
                           If not provided, lists all available calendars.
        days: Number of days to look ahead (default 7).

    Returns:
        JSON with calendar events or list of calendars.
    """
    try:
        if calendar_entity_id:
            events = await hass.get_calendar_events(calendar_entity_id, days)
            return json.dumps({
                "calendar": calendar_entity_id,
                "days": days,
                "events": events,
            }, indent=2, default=str)
        else:
            calendars = await hass.get_calendars()
            return json.dumps(calendars, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — People & Weather (convenience)
# ============================================================================


@mcp.tool()
async def get_persons() -> str:
    """Get all person entities showing who is home and their location.

    Returns each person's name, state (home/not_home/zone), and
    GPS coordinates if available.
    """
    try:
        result = await hass.get_persons()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_weather(weather_entity_id: str | None = None) -> str:
    """Get weather information.

    Args:
        weather_entity_id: Specific weather entity (e.g. 'weather.home').
                          If not provided, returns all weather entities.

    Returns:
        JSON with temperature, humidity, wind, pressure, and forecast.
    """
    try:
        result = await hass.get_weather(weather_entity_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Supervisor API (Add-ons, Backups, Host)
# ============================================================================


@mcp.tool()
async def get_host_info() -> str:
    """Get host system information.

    Returns hostname, operating system, disk usage, memory, architecture,
    and available features. Useful for diagnostics and capacity planning.
    """
    try:
        result = await hass.get_host_info()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_updates() -> str:
    """Check for available updates.

    Returns pending updates for Home Assistant Core, OS, Supervisor,
    and installed add-ons.
    """
    try:
        result = await hass.get_available_updates()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def list_addons() -> str:
    """List all installed Home Assistant add-ons.

    Returns each add-on's name, slug, version, state (started/stopped),
    and update availability.
    """
    try:
        addons = await hass.list_addons()
        # Simplify the output to key fields
        summary = []
        for addon in addons:
            summary.append({
                "name": addon.get("name"),
                "slug": addon.get("slug"),
                "version": addon.get("version"),
                "state": addon.get("state"),
                "update_available": addon.get("update_available", False),
                "description": addon.get("description", ""),
            })
        return json.dumps(summary, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_addon_info(addon_slug: str) -> str:
    """Get detailed information about a specific add-on.

    Args:
        addon_slug: The add-on slug (e.g. 'core_mosquitto', 'a0d7b954_ssh').
                   Use list_addons to see available slugs.

    Returns:
        JSON with version, state, options, network, resource usage, etc.
    """
    try:
        result = await hass.get_addon_info(addon_slug)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def addon_start_stop(addon_slug: str, action: str) -> str:
    """Start, stop, or restart a Home Assistant add-on.

    Args:
        addon_slug: The add-on slug (e.g. 'core_mosquitto').
        action: One of 'start', 'stop', or 'restart'.

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.addon_action(addon_slug, action)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def list_backups() -> str:
    """List all Home Assistant backups.

    Returns each backup's name, date, type (full/partial), and size.
    """
    try:
        backups = await hass.list_backups()
        summary = []
        for backup in backups:
            summary.append({
                "slug": backup.get("slug"),
                "name": backup.get("name"),
                "date": backup.get("date"),
                "type": backup.get("type"),
                "size": backup.get("size"),
                "protected": backup.get("protected", False),
            })
        return json.dumps(summary, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def create_backup(
    name: str | None = None,
    partial: bool = False,
    addons: list[str] | None = None,
    folders: list[str] | None = None,
) -> str:
    """Create a Home Assistant backup.

    Always recommended before making significant changes (restarts,
    updates, automation changes).

    Args:
        name: Optional backup name. Auto-generated if not provided.
        partial: If True, only back up specified addons/folders.
        addons: List of add-on slugs to include (partial mode only).
        folders: List of folders to include (partial mode only).
                 Available: 'homeassistant', 'ssl', 'share', 'media', 'addons/local'.

    Returns:
        JSON with the backup slug/result.
    """
    try:
        result = await hass.create_backup(name, partial, addons, folders)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Device Registry
# ============================================================================


@mcp.tool()
async def list_devices(limit: int = 50) -> str:
    """List all physical devices in Home Assistant.

    Returns each device's name, manufacturer, model, area, and disabled status.
    Useful for understanding what hardware is in the home.

    Args:
        limit: Maximum devices to return (default 50).

    Returns:
        JSON array of device info.
    """
    try:
        devices = await hass.get_devices()
        return json.dumps(devices[:limit], indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_device_entities(device_id: str) -> str:
    """Get all entity IDs belonging to a specific device.

    Args:
        device_id: The device ID (from list_devices).

    Returns:
        JSON array of entity IDs.
    """
    try:
        result = await hass.get_device_entities(device_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Floor / Label Hierarchy
# ============================================================================


@mcp.tool()
async def list_floors() -> str:
    """List all floors with their areas.

    Returns the floor → area hierarchy for understanding the
    spatial organization of the home.
    """
    try:
        result = await hass.get_floors()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def list_labels() -> str:
    """List all labels and their tagged entities.

    Labels are HA's tagging system for grouping entities by
    function (e.g. 'critical', 'energy', 'outdoor').
    """
    try:
        result = await hass.get_labels()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_label_entities(label_id: str) -> str:
    """Get all entities tagged with a specific label.

    Args:
        label_id: The label ID.

    Returns:
        JSON array of entity IDs.
    """
    try:
        result = await hass.get_label_entities(label_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — State Setting
# ============================================================================


@mcp.tool()
async def set_state(
    entity_id: str,
    state: str,
    attributes: dict[str, Any] | None = None,
) -> str:
    """Set the state of an entity directly.

    Primarily useful for input helpers (input_boolean, input_number,
    input_text, input_select, input_datetime) and template sensors.

    WARNING: This bypasses normal entity update flows. Use entity_action
    or call_service for most entities.

    Args:
        entity_id: The entity to update.
        state: The new state value.
        attributes: Optional attributes to set.

    Returns:
        JSON with the updated entity state.
    """
    try:
        result = await hass.set_state(entity_id, state, attributes)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Conversation
# ============================================================================


@mcp.tool()
async def conversation_process(text: str, language: str = "en") -> str:
    """Send natural language to Home Assistant's conversation agent.

    This lets you delegate commands to HA's own NLP pipeline
    (e.g. 'turn on the living room lights').

    Args:
        text: The natural language command.
        language: Language code (default 'en').

    Returns:
        JSON with the conversation response.
    """
    try:
        result = await hass.conversation_process(text, language)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Automation / Script CRUD
# ============================================================================


@mcp.tool()
async def get_automation_config(automation_id: str) -> str:
    """Get the YAML configuration of an automation.

    Args:
        automation_id: The automation's ID (not entity_id). Use list_automations
                      to find IDs.

    Returns:
        JSON with the automation configuration.
    """
    try:
        result = await hass.get_automation_config(automation_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def create_automation(
    automation_id: str,
    config: dict[str, Any],
) -> str:
    """Create or update an automation.

    Args:
        automation_id: Unique ID for the automation (e.g. 'motion_lights_kitchen').
        config: Automation config dict with keys: alias, description, trigger,
                condition (optional), action, mode (optional).

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.update_automation_config(automation_id, config)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def delete_automation(automation_id: str) -> str:
    """Delete an automation.

    Args:
        automation_id: The automation's ID (not entity_id).

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.delete_automation_config(automation_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_script_config(script_id: str) -> str:
    """Get the YAML configuration of a script.

    Args:
        script_id: The script's ID (e.g. 'morning_routine').

    Returns:
        JSON with the script configuration.
    """
    try:
        result = await hass.get_script_config(script_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def create_script(
    script_id: str,
    config: dict[str, Any],
) -> str:
    """Create or update a script.

    Args:
        script_id: Unique ID for the script (e.g. 'morning_routine').
        config: Script config dict with keys: alias, sequence, mode (optional),
                description (optional).

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.update_script_config(script_id, config)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def delete_script(script_id: str) -> str:
    """Delete a script.

    Args:
        script_id: The script's ID.

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.delete_script_config(script_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Automation Traces
# ============================================================================


@mcp.tool()
async def get_automation_traces(automation_id: str) -> str:
    """Get execution traces for an automation.

    Shows step-by-step execution history: what triggered, what conditions
    were checked, what actions ran. Essential for debugging automations.

    Args:
        automation_id: The automation's ID (not entity_id).

    Returns:
        JSON array of trace entries.
    """
    try:
        result = await hass.get_automation_traces(automation_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Todo List Management
# ============================================================================


@mcp.tool()
async def get_todo_items(entity_id: str) -> str:
    """Get items from a Home Assistant todo list.

    Args:
        entity_id: The todo entity ID (e.g. 'todo.shopping_list').

    Returns:
        JSON with todo items.
    """
    try:
        result = await hass.get_todo_items(entity_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def add_todo_item(
    entity_id: str, item: str, due_date: str | None = None
) -> str:
    """Add an item to a todo list.

    Args:
        entity_id: The todo entity ID.
        item: The item text.
        due_date: Optional due date (YYYY-MM-DD).

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.add_todo_item(entity_id, item, due_date)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def update_todo_item(
    entity_id: str, item: str,
    rename: str | None = None, status: str | None = None,
) -> str:
    """Update a todo list item (rename or change status).

    Args:
        entity_id: The todo entity ID.
        item: The current item text.
        rename: New name for the item.
        status: New status ('needs_action' or 'completed').

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.update_todo_item(entity_id, item, rename, status)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def remove_todo_item(entity_id: str, item: str) -> str:
    """Remove an item from a todo list.

    Args:
        entity_id: The todo entity ID.
        item: The item text to remove.

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.remove_todo_item(entity_id, item)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Calendar Event CRUD
# ============================================================================


@mcp.tool()
async def create_calendar_event(
    entity_id: str, summary: str,
    start: str, end: str,
    description: str | None = None, location: str | None = None,
) -> str:
    """Create a calendar event.

    Args:
        entity_id: Calendar entity ID (e.g. 'calendar.family').
        summary: Event title.
        start: Start datetime (ISO format, e.g. '2026-04-01T09:00:00').
        end: End datetime (ISO format).
        description: Optional event description.
        location: Optional event location.

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.create_calendar_event(
            entity_id, summary, start, end, description, location
        )
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Dashboard Management
# ============================================================================


@mcp.tool()
async def list_dashboards() -> str:
    """List all Lovelace dashboards.

    Returns each dashboard's URL path, title, and mode.
    """
    try:
        result = await hass.get_dashboards()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_dashboard_config(dashboard_id: str | None = None) -> str:
    """Get the configuration of a Lovelace dashboard.

    Args:
        dashboard_id: Dashboard URL path (e.g. 'lovelace-rooms'). If not
                     provided, returns the default dashboard config.

    Returns:
        JSON with the dashboard configuration (views, cards, etc.).
    """
    try:
        result = await hass.get_dashboard_config(dashboard_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def save_dashboard_config(
    config: dict[str, Any], dashboard_id: str | None = None
) -> str:
    """Save a Lovelace dashboard configuration.

    WARNING: This overwrites the entire dashboard config.
    Use get_dashboard_config first to read the current config.

    Args:
        config: Full dashboard config (must include 'views' array).
        dashboard_id: Dashboard URL path. Defaults to the main dashboard.

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.save_dashboard_config(config, dashboard_id)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Bulk Operations
# ============================================================================


@mcp.tool()
async def bulk_control(
    entity_ids: list[str], action: str,
    params: dict[str, Any] | None = None,
) -> str:
    """Control multiple entities at once (turn on/off/toggle).

    Args:
        entity_ids: List of entity IDs to control.
        action: One of 'on', 'off', or 'toggle'.
        params: Optional shared parameters (e.g. {'brightness': 128}).

    Returns:
        JSON array with results for each entity.
    """
    try:
        result = await hass.bulk_control(entity_ids, action, params)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def bulk_get_states(entity_ids: list[str]) -> str:
    """Get states of multiple entities at once.

    More efficient than calling get_entity multiple times.

    Args:
        entity_ids: List of entity IDs to query.

    Returns:
        JSON array of entity states.
    """
    try:
        result = await hass.bulk_get_states(entity_ids)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Deep Search
# ============================================================================


@mcp.tool()
async def deep_search(query: str) -> str:
    """Search across all HA configuration: entities, automations,
    scripts, scenes, and areas.

    More comprehensive than search_entities which only searches entities.

    Args:
        query: Search text (case-insensitive).

    Returns:
        JSON with matches grouped by type.
    """
    try:
        result = await hass.deep_search(query)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Supervisor Logs & Diagnostics
# ============================================================================


@mcp.tool()
async def get_supervisor_logs(lines: int = 100) -> str:
    """Get Supervisor logs.

    Args:
        lines: Number of recent log lines to return (default 100).

    Returns:
        Plain text log output.
    """
    try:
        return await hass.get_supervisor_logs(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def get_core_logs(lines: int = 100) -> str:
    """Get Home Assistant Core container logs.

    More structured than get_error_log. Shows all Core log output.

    Args:
        lines: Number of recent log lines to return (default 100).

    Returns:
        Plain text log output.
    """
    try:
        return await hass.get_core_logs(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def get_addon_logs(addon_slug: str, lines: int = 100) -> str:
    """Get logs from a specific add-on.

    Args:
        addon_slug: The add-on slug (e.g. 'core_mosquitto').
        lines: Number of recent log lines (default 100).

    Returns:
        Plain text log output.
    """
    try:
        return await hass.get_addon_logs(addon_slug, lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def get_os_info() -> str:
    """Get HAOS information (version, board, data disk).

    Returns:
        JSON with OS details.
    """
    try:
        result = await hass.get_os_info()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_network_info() -> str:
    """Get network configuration (interfaces, DNS, IP config).

    Returns:
        JSON with network details.
    """
    try:
        result = await hass.get_network_info()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_hardware_info() -> str:
    """Get hardware info (USB devices, GPIO, serial ports).

    Useful for Zigbee/Z-Wave stick troubleshooting.

    Returns:
        JSON with hardware details.
    """
    try:
        result = await hass.get_hardware_info()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_resolution_info() -> str:
    """Get system resolution center (issues, suggestions, unhealthy flags).

    HA's built-in self-diagnostics. Shows problems that need attention.

    Returns:
        JSON with issues and suggestions.
    """
    try:
        result = await hass.get_resolution_info()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def browse_addon_store(search: str | None = None) -> str:
    """Browse available add-ons from the HA add-on store.

    Args:
        search: Optional search text to filter add-ons.

    Returns:
        JSON array of available add-ons with name, description, version.
    """
    try:
        addons = await hass.get_store_addons()
        if search:
            q = search.lower()
            addons = [
                a for a in addons
                if q in a.get("name", "").lower()
                or q in a.get("description", "").lower()
                or q in a.get("slug", "").lower()
            ]
        # Slim down the output
        summary = []
        for a in addons[:50]:
            summary.append({
                "name": a.get("name"),
                "slug": a.get("slug"),
                "description": a.get("description", "")[:200],
                "version": a.get("version"),
                "installed": a.get("installed", False),
                "available": a.get("available", True),
            })
        return json.dumps(summary, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Config File Access
# ============================================================================


@mcp.tool()
async def list_config_files(path: str = "") -> str:
    """List files in the Home Assistant /config directory.

    Args:
        path: Subdirectory path within /config (default: root).

    Returns:
        JSON array of file/directory names.
    """
    try:
        result = await hass.list_config_files(path)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def read_config_file(path: str) -> str:
    """Read a configuration file from /config.

    Useful for inspecting configuration.yaml, automations.yaml, etc.
    Cannot read secrets.yaml for security.

    Args:
        path: File path relative to /config (e.g. 'configuration.yaml').

    Returns:
        File contents as text.
    """
    try:
        return await hass.read_config_file(path)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def write_config_file(path: str, content: str) -> str:
    """Write content to a config file in /config.

    Automatically creates a .bak backup of the existing file.
    Cannot write to secrets.yaml, .storage, or the database.

    WARNING: Use check_config after writing to verify the config is valid.

    Args:
        path: File path relative to /config (e.g. 'automations.yaml').
        content: The file content to write.

    Returns:
        JSON with the result.
    """
    try:
        result = await hass.write_config_file(path, content)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# TOOLS — Reload Configuration
# ============================================================================


@mcp.tool()
async def reload_config(target: str = "all") -> str:
    """Reload configuration without restarting Home Assistant.

    Much faster than restart_ha. Use after modifying YAML config files.

    Args:
        target: What to reload: 'all', 'core', 'automations', 'scripts', 'scenes'.

    Returns:
        JSON with the result.
    """
    try:
        if target == "all":
            result = await hass.reload_all()
        elif target == "core":
            result = await hass.reload_core_config()
        elif target == "automations":
            result = await hass.reload_automations()
        elif target == "scripts":
            result = await hass.reload_scripts()
        elif target == "scenes":
            result = await hass.reload_scenes()
        else:
            return json.dumps({"error": f"Unknown target '{target}'. Use: all, core, automations, scripts, scenes"})
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# RESOURCES
# ============================================================================


@mcp.resource("hass://entities/{entity_id}")
async def entity_resource(entity_id: str) -> str:
    """Get entity state as a resource.

    Returns a markdown-formatted view of the entity with key attributes.
    """
    try:
        state = await hass.get_entity_state(entity_id)
        domain = entity_id.split(".")[0] if "." in entity_id else ""
        attrs = state.get("attributes", {})
        name = attrs.get("friendly_name", entity_id)

        lines = [
            f"# {name}",
            f"**Entity ID:** `{entity_id}`",
            f"**State:** `{state.get('state')}`",
            f"**Domain:** `{domain}`",
            "",
        ]

        # Domain-specific attributes
        important = hass.DOMAIN_IMPORTANT_ATTRIBUTES.get(domain, [])
        if important:
            lines.append("## Key Attributes")
            for attr in important:
                if attr in attrs:
                    lines.append(f"- **{attr}:** {attrs[attr]}")

        lines.extend([
            "",
            f"**Last Changed:** {state.get('last_changed', 'N/A')}",
            f"**Last Updated:** {state.get('last_updated', 'N/A')}",
        ])

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching {entity_id}: {e}"


@mcp.resource("hass://entities/{entity_id}/detailed")
async def entity_detailed_resource(entity_id: str) -> str:
    """Get detailed entity state including all attributes."""
    try:
        state = await hass.get_entity_state(entity_id)
        return json.dumps(state, indent=2, default=str)
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("hass://entities")
async def all_entities_resource() -> str:
    """Get all entities grouped by domain."""
    try:
        all_states = await hass.get_all_states()
        domains: dict[str, list] = {}
        for e in all_states:
            eid = e.get("entity_id", "")
            d = eid.split(".")[0] if "." in eid else "unknown"
            domains.setdefault(d, []).append(e)

        lines = ["# Home Assistant Entities", ""]
        for d in sorted(domains.keys()):
            entities = domains[d]
            lines.append(f"## {d} ({len(entities)})")
            for e in entities:
                name = e.get("attributes", {}).get("friendly_name", e.get("entity_id"))
                lines.append(f"- `{e.get('entity_id')}` — {e.get('state')} ({name})")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("hass://entities/domain/{domain}")
async def domain_entities_resource(domain: str) -> str:
    """Get all entities for a specific domain."""
    try:
        entities = await hass.get_entities(domain=domain)
        lines = [f"# {domain} Entities", ""]
        for e in entities:
            lines.append(
                f"- `{e.get('entity_id')}` — **{e.get('state')}** ({e.get('name', '')})"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("hass://system")
async def system_resource() -> str:
    """Get system overview as a resource."""
    try:
        overview = await hass.get_system_overview()
        return json.dumps(overview, indent=2, default=str)
    except Exception as e:
        return f"Error: {e}"


# ============================================================================
# PROMPTS
# ============================================================================


@mcp.prompt()
async def create_automation(
    trigger_type: str = "state",
    entity_id: str | None = None,
) -> str:
    """Guided conversation for creating a Home Assistant automation.

    Args:
        trigger_type: Type of trigger (state, time, sun, event, numeric_state, zone).
        entity_id: Optional entity for the trigger.
    """
    return f"""I want to create a new Home Assistant automation.

Trigger type: {trigger_type}
{"Entity: " + entity_id if entity_id else "No specific entity yet."}

Please help me build this automation step by step:
1. First, define the trigger conditions
2. Then, define any conditions that should be checked
3. Finally, define the actions to perform

Ask me questions to clarify what I want the automation to do, then generate
the YAML configuration I can add to my automations.yaml.

Use the list_entities tool to help me find the right entities.
Use the list_services tool to show available actions."""


@mcp.prompt()
async def debug_automation(automation_id: str) -> str:
    """Troubleshooting guide for a broken automation.

    Args:
        automation_id: The automation entity ID to debug.
    """
    return f"""I need help debugging this Home Assistant automation: {automation_id}

Please follow these steps:
1. Use get_entity to check the automation's current state
2. Use get_history to see when it was last triggered
3. Use get_logbook to check for recent activity
4. Use get_error_log to look for related errors
5. Analyze the results and suggest fixes

Common issues to check:
- Is the automation enabled (state: on)?
- Has it triggered recently?
- Are there errors mentioning the automation or its entities?
- Are the referenced entities valid and available?"""


@mcp.prompt()
async def troubleshoot_entity(entity_id: str) -> str:
    """Diagnostic guide for a malfunctioning entity.

    Args:
        entity_id: The entity to troubleshoot.
    """
    return f"""I need help troubleshooting this Home Assistant entity: {entity_id}

Please follow these diagnostic steps:
1. Use get_entity with detailed=True to see all attributes and context
2. Use get_history to check recent state changes (or lack thereof)
3. Use get_error_log to look for related errors
4. Check if the entity's integration is mentioned in errors

Look for:
- Is the entity available or unavailable?
- Is the state 'unknown' or unexpected?
- When was the last state change?
- Are there error log entries for the integration?"""


@mcp.prompt()
async def routine_optimizer() -> str:
    """Analyzes usage patterns and suggests optimized routines."""
    return """Please analyze my Home Assistant setup and suggest automation improvements.

Steps:
1. Use system_overview to understand overall setup
2. Use list_automations to see existing automations
3. Use domain_summary for key domains (light, climate, sensor)
4. Look for patterns and opportunities

Suggest:
- Automations that could save energy
- Routines that combine multiple actions
- Improvements to existing automations
- New automations based on available sensors and devices"""


@mcp.prompt()
async def automation_health_check() -> str:
    """Reviews all automations for conflicts, redundancies, or improvements."""
    return """Please perform a health check on all my Home Assistant automations.

Steps:
1. Use list_automations to get all automations
2. Check each automation's state and last_triggered time
3. Use get_error_log to find automation-related errors
4. Analyze for issues

Report on:
- Disabled automations (should they be removed or fixed?)
- Automations that haven't triggered in a long time
- Potential conflicts between automations
- Error log entries mentioning automations
- Suggestions for improvement"""


@mcp.prompt()
async def entity_naming_consistency() -> str:
    """Audits entity naming conventions and suggests standardization."""
    return """Please audit my Home Assistant entity naming conventions.

Steps:
1. Use list_entities for each major domain
2. Analyze naming patterns
3. Look for inconsistencies

Check for:
- Mixed naming conventions (snake_case vs other)
- Missing friendly names
- Unclear or generic entity IDs
- Inconsistent prefixes/suffixes within domains
- Suggest a standardized naming scheme"""


@mcp.prompt()
async def dashboard_layout_generator() -> str:
    """Creates optimized dashboard layouts based on available entities."""
    return """Please help me design a Home Assistant dashboard layout.

Steps:
1. Use system_overview to understand what's available
2. Use get_areas to see rooms/areas
3. Use domain_summary for key domains
4. Design an optimal layout

Generate a YAML dashboard configuration with:
- Overview tab with key status indicators
- Per-area/room tabs
- Domain-specific cards (lights, climate, media, security)
- Sensor graphs for key metrics
- Quick action buttons for common tasks"""


# ============================================================================
# RESOURCES — New
# ============================================================================


@mcp.resource("hass://devices")
async def devices_resource() -> str:
    """Get all physical devices with manufacturer and model info."""
    try:
        devices = await hass.get_devices()
        lines = ["# Home Assistant Devices", ""]
        by_mfg: dict[str, list] = {}
        for d in devices:
            mfg = d.get("manufacturer", "Unknown") or "Unknown"
            by_mfg.setdefault(mfg, []).append(d)

        for mfg in sorted(by_mfg.keys()):
            devs = by_mfg[mfg]
            lines.append(f"## {mfg} ({len(devs)})")
            for d in devs:
                model = d.get("model", "")
                area = d.get("area_id", "")
                name = d.get("name", "unknown")
                disabled = " [DISABLED]" if d.get("disabled_by") and d["disabled_by"] != "None" else ""
                lines.append(f"- **{name}** — {model} (area: {area}){disabled}")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("hass://areas/tree")
async def areas_tree_resource() -> str:
    """Get the full spatial hierarchy: floors → areas → entity counts."""
    try:
        floors = await hass.get_floors()
        areas = await hass.get_areas()
        area_ids_in_floors = set()

        lines = ["# Home Spatial Hierarchy", ""]

        if floors:
            for f in floors:
                lines.append(f"## Floor: {f['name']}")
                for area_id in f.get("areas", []):
                    area_ids_in_floors.add(area_id)
                    entities = await hass.get_area_entities(area_id)
                    area_name = next(
                        (a["name"] for a in areas if a["area_id"] == area_id),
                        area_id,
                    )
                    lines.append(f"  - **{area_name}** ({len(entities)} entities)")
                lines.append("")

        # Areas not assigned to any floor
        unassigned = [a for a in areas if a["area_id"] not in area_ids_in_floors]
        if unassigned:
            lines.append("## Unassigned Areas")
            for a in unassigned:
                entities = await hass.get_area_entities(a["area_id"])
                lines.append(f"  - **{a['name']}** ({len(entities)} entities)")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("hass://automations")
async def automations_resource() -> str:
    """Get all automations with details."""
    try:
        automations = await hass.get_automations()
        lines = ["# Home Assistant Automations", ""]
        on = [a for a in automations if a.get("state") == "on"]
        off = [a for a in automations if a.get("state") != "on"]

        lines.append(f"## Enabled ({len(on)})")
        for a in on:
            last = a.get("last_triggered", "never")
            lines.append(f"- `{a['entity_id']}` — {a['alias']} (last: {last})")
        lines.append("")

        if off:
            lines.append(f"## Disabled ({len(off)})")
            for a in off:
                lines.append(f"- `{a['entity_id']}` — {a['alias']}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("hass://labels")
async def labels_resource() -> str:
    """Get all labels and their tagged entities."""
    try:
        labels = await hass.get_labels()
        if not labels:
            return "No labels configured."
        lines = ["# Home Assistant Labels", ""]
        for label in labels:
            lines.append(f"## {label['name']} ({label['entity_count']} entities)")
            for eid in label.get("entities", []):
                lines.append(f"- `{eid}`")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("hass://addons")
async def addons_resource() -> str:
    """Get installed add-ons overview."""
    try:
        addons = await hass.list_addons()
        lines = ["# Installed Add-ons", ""]
        started = [a for a in addons if a.get("state") == "started"]
        other = [a for a in addons if a.get("state") != "started"]

        lines.append(f"## Running ({len(started)})")
        for a in started:
            update = " [UPDATE AVAILABLE]" if a.get("update_available") else ""
            lines.append(f"- **{a['name']}** v{a.get('version', '?')}{update}")
        lines.append("")

        if other:
            lines.append(f"## Stopped/Other ({len(other)})")
            for a in other:
                lines.append(f"- **{a['name']}** ({a.get('state', '?')})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("hass://health")
async def health_resource() -> str:
    """Combined system health report."""
    try:
        sections: list[str] = ["# System Health Report", ""]

        # Connection
        conn = await hass.check_api_connection()
        sections.append(f"## Connection")
        sections.append(f"- HA Version: {conn.get('version', '?')}")
        sections.append(f"- Connected: {conn.get('connected', False)}")
        sections.append("")

        # Host info
        try:
            host = await hass.get_host_info()
            sections.append("## Host")
            sections.append(f"- OS: {host.get('operating_system', '?')}")
            sections.append(f"- Disk: {host.get('disk_used', '?')}GB / {host.get('disk_total', '?')}GB ({host.get('disk_free', '?')}GB free)")
            sections.append("")
        except Exception:
            pass

        # Resolution issues
        try:
            res = await hass.get_resolution_info()
            issues = res.get("issues", [])
            suggestions = res.get("suggestions", [])
            unhealthy = res.get("unhealthy", [])
            sections.append("## Issues & Suggestions")
            if unhealthy:
                sections.append(f"- **UNHEALTHY**: {', '.join(str(u) for u in unhealthy)}")
            sections.append(f"- Issues: {len(issues)}")
            for i in issues[:10]:
                sections.append(f"  - [{i.get('severity', '?')}] {i.get('type', '?')}: {i.get('context', '')}")
            sections.append(f"- Suggestions: {len(suggestions)}")
            sections.append("")
        except Exception:
            pass

        # Add-ons in error state
        try:
            addons = await hass.list_addons()
            error_addons = [a for a in addons if a.get("state") == "error"]
            if error_addons:
                sections.append("## Add-ons in Error")
                for a in error_addons:
                    sections.append(f"- **{a['name']}** ({a.get('slug')})")
                sections.append("")
        except Exception:
            pass

        # Error log summary
        try:
            error_log = await hass.get_error_log()
            sections.append("## Error Log Summary")
            sections.append(f"- Errors: {error_log.get('error_count', 0)}")
            sections.append(f"- Warnings: {error_log.get('warning_count', 0)}")
            top_integrations = error_log.get("integration_mentions", {})
            if top_integrations:
                top3 = list(top_integrations.items())[:3]
                sections.append(f"- Top offenders: {', '.join(f'{k} ({v})' for k, v in top3)}")
        except Exception:
            pass

        return "\n".join(sections)
    except Exception as e:
        return f"Error: {e}"


# ============================================================================
# PROMPTS — New
# ============================================================================


@mcp.prompt()
async def energy_optimizer() -> str:
    """Analyze energy usage and suggest optimizations."""
    return """Please analyze my Home Assistant setup for energy optimization opportunities.

Steps:
1. Use list_entities with domain='sensor' and search_query='energy' to find energy sensors
2. Use list_entities with domain='sensor' and search_query='power' to find power monitoring
3. Use domain_summary for 'light', 'climate', 'switch', 'fan' domains
4. Use get_history on key energy sensors for usage patterns
5. Check automations related to energy/power

Analyze and suggest:
- Devices with high standby power consumption
- Lights left on patterns (check history of light entities)
- Climate/HVAC optimization opportunities
- Automations that could reduce energy usage
- Solar/battery optimization if applicable
- Specific automation YAML to implement savings"""


@mcp.prompt()
async def security_audit() -> str:
    """Comprehensive security audit of the HA instance."""
    return """Please perform a security audit of my Home Assistant instance.

Steps:
1. Use get_version to check HA version (is it up to date?)
2. Use get_updates to check for pending security updates
3. Use list_addons to find outdated or error-state add-ons
4. Use list_integrations to check for known insecure integrations
5. Use get_network_info to review network exposure
6. Use get_resolution_info for system-identified issues
7. Use list_entities with domain='lock' to check lock entities
8. Use list_entities with domain='alarm_control_panel' to check alarms
9. Use list_entities with domain='camera' to check cameras
10. Use get_error_log for security-related errors

Report on:
- Outdated software that needs updating
- Network exposure risks
- Weak or missing device configurations
- Add-ons with known issues
- Suggestions for security automations (door locks, camera alerts)
- Missing security devices or sensors"""


@mcp.prompt()
async def device_troubleshooter(device_name: str) -> str:
    """Troubleshoot a specific device by checking all its entities, logs, and connectivity.

    Args:
        device_name: Name or keyword to identify the device.
    """
    return f"""I need help troubleshooting a device: {device_name}

Steps:
1. Use deep_search to find all entities and configurations related to '{device_name}'
2. Use list_devices to find the device and get its device_id
3. Use get_device_entities to see all entities belonging to this device
4. For each entity, use get_entity with detailed=True to check state and attributes
5. Use get_history on key entities to check recent activity/failures
6. Use get_error_log and search for the device/integration name
7. Use get_resolution_info to check for related system issues

Diagnose:
- Is the device online and communicating?
- Are entities showing 'unavailable' or 'unknown'?
- When was the last successful state change?
- Are there error log entries for this device's integration?
- What resolution issues exist?
- Recommended actions to fix the issue"""


@mcp.prompt()
async def template_helper() -> str:
    """Interactive Jinja2 template writing assistant."""
    return """I want help writing Jinja2 templates for Home Assistant.

I'll describe what I want the template to do, and you'll:
1. Write the template using HA's Jinja2 syntax
2. Use render_template to test it against my actual data
3. Iterate until the output is correct

Common template functions you can use:
- states('entity_id') — get state value
- state_attr('entity_id', 'attribute') — get attribute
- areas() — list all area IDs
- area_entities('area_id') — entities in an area
- device_attr('device_id', 'attr') — device attributes
- label_entities('label_id') — entities with a label
- integration_entities('integration') — entities from an integration
- is_state('entity_id', 'value') — check state
- states.domain — all entities in a domain
- now() / utcnow() — current time
- relative_time(timestamp) — human-readable time delta

Ask me what template I'd like to create!"""


@mcp.prompt()
async def scene_builder(area: str | None = None) -> str:
    """Build a scene by capturing current entity states.

    Args:
        area: Optional area name to focus on.
    """
    area_filter = f"in the '{area}' area" if area else "in your home"
    return f"""Let's build a Home Assistant scene from the current state of entities {area_filter}.

Steps:
1. {"Use get_area_entities('" + area + "') to get entities in the area" if area else "Use system_overview to see available entities"}
2. Check current states of relevant entities (lights, climate, media_player, cover)
3. Let you choose which entities to include
4. Generate the scene YAML configuration

I'll check the current states and help you create a scene that captures
exactly what's happening right now (or let you customize it).

Which entities or room should we capture?"""


@mcp.prompt()
async def backup_strategy() -> str:
    """Analyze backup history and recommend a backup plan."""
    return """Please analyze my backup situation and recommend a strategy.

Steps:
1. Use list_backups to see existing backups
2. Use get_host_info to check disk space
3. Use list_addons to see what add-ons need backing up
4. Analyze backup frequency, types, and sizes

Report on:
- Current backup inventory (dates, types, sizes)
- Available disk space vs backup space usage
- Backup frequency (is it sufficient?)
- Recommend a backup schedule
- Suggest partial vs full backup strategy
- Identify critical data that must be in every backup
- Create an automation for scheduled backups if one doesn't exist"""


@mcp.prompt()
async def floor_plan_organizer() -> str:
    """Organize entities into floors, areas, and labels."""
    return """Please help me organize my Home Assistant entities into a clean hierarchy.

Steps:
1. Use list_floors to see current floor structure
2. Use get_areas to see current areas
3. Use list_labels to see current labels
4. Use system_overview to see all entities and their current area assignments
5. Use list_devices to see devices and their areas

Analyze and suggest:
- Missing floors (e.g. Ground Floor, First Floor, Garden)
- Missing areas (rooms without any area assignment)
- Entities not assigned to any area
- Devices without area assignments
- Label suggestions for grouping (e.g. 'energy', 'security', 'outdoor')
- A clean naming convention for areas
- Step-by-step instructions to implement the organization"""


# ============================================================================
# v2.0 - Register all expanded tool modules (~410 new tools across 39 modules)
# ============================================================================
from . import tools as _tools_pkg
_tools_pkg.register_all(mcp)

