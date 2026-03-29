"""Tests for the HASS MCP Server - HA API client functions."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx async client."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Set environment variables for testing."""
    monkeypatch.setenv("HA_URL", "http://localhost:8123")
    monkeypatch.setenv("HA_TOKEN", "test-token-abc")


class TestGetVersion:
    @pytest.mark.asyncio
    async def test_get_version(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"version": "2026.3.1"}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import get_version
            version = await get_version()
            assert version == "2026.3.1"


class TestGetEntityState:
    @pytest.mark.asyncio
    async def test_get_entity_state(self, mock_httpx_client):
        entity_data = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "brightness": 255,
                "color_temp": 370,
            },
            "last_changed": "2026-03-29T10:00:00+00:00",
        }
        mock_response = MagicMock()
        mock_response.json.return_value = entity_data
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import get_entity_state
            result = await get_entity_state("light.living_room")
            assert result["entity_id"] == "light.living_room"
            assert result["state"] == "on"
            assert result["attributes"]["brightness"] == 255


class TestCallService:
    @pytest.mark.asyncio
    async def test_call_service(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.json.return_value = [{"entity_id": "light.living_room", "state": "on"}]
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import call_service
            result = await call_service("light", "turn_on", {"entity_id": "light.living_room"})
            assert isinstance(result, list)


class TestEntityAction:
    @pytest.mark.asyncio
    async def test_entity_action_on(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.json.return_value = [{"entity_id": "light.bedroom", "state": "on"}]
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import entity_action
            result = await entity_action("light.bedroom", "on", {"brightness": 128})
            mock_httpx_client.post.assert_called_once()
            call_url = mock_httpx_client.post.call_args[0][0]
            assert "light/turn_on" in call_url

    @pytest.mark.asyncio
    async def test_entity_action_invalid(self, mock_httpx_client):
        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import entity_action
            result = await entity_action("light.bedroom", "invalid_action")
            assert "error" in result


class TestFormatEntityLean:
    def test_lean_format_light(self):
        from app.hass import _format_entity_lean
        entity = {
            "entity_id": "light.kitchen",
            "state": "on",
            "attributes": {
                "friendly_name": "Kitchen Light",
                "brightness": 200,
                "color_temp": 300,
                "supported_features": 63,
                "icon": "mdi:lightbulb",
            },
        }
        result = _format_entity_lean(entity, domain="light")
        assert result["entity_id"] == "light.kitchen"
        assert result["state"] == "on"
        assert result["name"] == "Kitchen Light"
        assert result["brightness"] == 200
        assert result["color_temp"] == 300
        # Should NOT include non-important attributes
        assert "supported_features" not in result
        assert "icon" not in result

    def test_lean_format_sensor(self):
        from app.hass import _format_entity_lean
        entity = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "attributes": {
                "friendly_name": "Temperature",
                "unit_of_measurement": "°C",
                "device_class": "temperature",
                "state_class": "measurement",
                "icon": "mdi:thermometer",
            },
        }
        result = _format_entity_lean(entity, domain="sensor")
        assert result["unit_of_measurement"] == "°C"
        assert result["device_class"] == "temperature"
        assert "icon" not in result

    def test_lean_format_custom_fields(self):
        from app.hass import _format_entity_lean
        entity = {
            "entity_id": "climate.thermostat",
            "state": "heat",
            "attributes": {
                "friendly_name": "Thermostat",
                "temperature": 22,
                "current_temperature": 20,
                "hvac_action": "heating",
            },
        }
        result = _format_entity_lean(
            entity, domain="climate", fields=["attr.temperature", "attr.hvac_action"]
        )
        assert result["temperature"] == 22
        assert result["hvac_action"] == "heating"
        assert "current_temperature" not in result


class TestGetErrorLog:
    @pytest.mark.asyncio
    async def test_parse_error_log(self, mock_httpx_client):
        log_text = """2026-03-29 10:00:00 ERROR (MainThread) [homeassistant.components.mqtt] Connection failed
2026-03-29 10:01:00 WARNING (MainThread) [homeassistant.components.zwave] Device timeout
2026-03-29 10:02:00 ERROR (MainThread) [homeassistant.components.mqtt] Retry failed
2026-03-29 10:03:00 INFO (MainThread) [homeassistant.core] Bus ready"""

        mock_response = MagicMock()
        mock_response.text = log_text
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import get_error_log
            result = await get_error_log()
            assert result["error_count"] == 2
            assert result["warning_count"] == 1
            assert "homeassistant.components.mqtt" in result["integration_mentions"]
            assert result["integration_mentions"]["homeassistant.components.mqtt"] == 2


class TestSearchEntities:
    @pytest.mark.asyncio
    async def test_search(self, mock_httpx_client):
        all_states = [
            {"entity_id": "light.living_room", "state": "on",
             "attributes": {"friendly_name": "Living Room Light"}},
            {"entity_id": "light.bedroom", "state": "off",
             "attributes": {"friendly_name": "Bedroom Light"}},
            {"entity_id": "sensor.temperature", "state": "22",
             "attributes": {"friendly_name": "Living Room Temp"}},
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = all_states
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import search_entities
            result = await search_entities("living")
            assert result["count"] == 2  # light.living_room + sensor (Living Room Temp)


class TestCheckConfig:
    @pytest.mark.asyncio
    async def test_check_config_valid(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "valid", "errors": None}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import check_config
            result = await check_config()
            assert result["result"] == "valid"


class TestGetComponents:
    @pytest.mark.asyncio
    async def test_list_components(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.json.return_value = ["mqtt", "zwave_js", "light", "sensor"]
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import get_components
            result = await get_components()
            assert "mqtt" in result
            assert len(result) == 4


class TestGetCalendarEvents:
    @pytest.mark.asyncio
    async def test_get_calendars(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"entity_id": "calendar.family", "name": "Family"},
            {"entity_id": "calendar.work", "name": "Work"},
        ]
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import get_calendars
            result = await get_calendars()
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_calendar_events(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"summary": "Meeting", "start": {"dateTime": "2026-03-29T10:00:00"}},
        ]
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import get_calendar_events
            result = await get_calendar_events("calendar.family", days=7)
            assert len(result) == 1
            assert result[0]["summary"] == "Meeting"


class TestGetPersons:
    @pytest.mark.asyncio
    async def test_get_persons(self, mock_httpx_client):
        all_states = [
            {"entity_id": "person.john", "state": "home",
             "attributes": {"friendly_name": "John", "source": "device_tracker.phone",
                            "latitude": 51.5, "longitude": -0.1}},
            {"entity_id": "person.jane", "state": "not_home",
             "attributes": {"friendly_name": "Jane"}},
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = all_states
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import get_persons
            result = await get_persons()
            assert len(result) == 2
            assert result[0]["state"] == "home"
            assert result[1]["state"] == "not_home"


class TestSupervisorAPI:
    @pytest.mark.asyncio
    async def test_get_host_info(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": "ok",
            "data": {
                "hostname": "homeassistant",
                "operating_system": "Home Assistant OS 14.2",
                "disk_total": 32.0,
                "disk_used": 8.5,
                "disk_free": 23.5,
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import get_host_info
            result = await get_host_info()
            assert result["hostname"] == "homeassistant"
            assert result["disk_total"] == 32.0

    @pytest.mark.asyncio
    async def test_list_addons(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": "ok",
            "data": {
                "addons": [
                    {"name": "Mosquitto", "slug": "core_mosquitto",
                     "version": "6.4.1", "state": "started",
                     "update_available": False},
                    {"name": "SSH", "slug": "a0d7b954_ssh",
                     "version": "9.14.0", "state": "started",
                     "update_available": True},
                ],
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import list_addons
            result = await list_addons()
            assert len(result) == 2
            assert result[0]["name"] == "Mosquitto"

    @pytest.mark.asyncio
    async def test_list_backups(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": "ok",
            "data": {
                "backups": [
                    {"slug": "abc123", "name": "Daily backup",
                     "date": "2026-03-28T03:00:00", "type": "full",
                     "size": 1.2},
                ],
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import list_backups
            result = await list_backups()
            assert len(result) == 1
            assert result[0]["slug"] == "abc123"

    @pytest.mark.asyncio
    async def test_addon_action_invalid(self, mock_httpx_client):
        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import addon_action
            result = await addon_action("core_mosquitto", "destroy")
            assert "error" in result

    @pytest.mark.asyncio
    async def test_create_backup(self, mock_httpx_client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": "ok",
            "data": {"slug": "new_backup_123"},
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        with patch("app.hass._get_client", return_value=mock_httpx_client):
            from app.hass import create_backup
            result = await create_backup(name="Test backup")
            assert result["slug"] == "new_backup_123"
