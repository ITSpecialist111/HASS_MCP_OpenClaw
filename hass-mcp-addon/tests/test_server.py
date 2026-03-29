"""Tests for the MCP server tool/resource/prompt registration."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("HA_URL", "http://localhost:8123")
    monkeypatch.setenv("HA_TOKEN", "test-token")


class TestServerRegistration:
    """Test that all tools, resources, and prompts are registered."""

    def test_server_has_name(self):
        from app.server import mcp
        assert mcp.name == "HASS-MCP"

    @pytest.mark.asyncio
    async def test_tools_registered(self):
        from app.server import mcp
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        expected_tools = [
            "get_version",
            "check_connection",
            "get_entity",
            "list_entities",
            "entity_action",
            "call_service",
            "list_services",
            "search_entities",
            "domain_summary",
            "system_overview",
            "list_automations",
            "list_scenes",
            "list_scripts",
            "activate_scene",
            "run_script",
            "trigger_automation",
            "toggle_automation",
            "get_history",
            "get_logbook",
            "get_error_log",
            "render_template",
            "fire_event",
            "get_areas",
            "get_area_entities",
            "restart_ha",
            "send_notification",
            # Phase 2 tools
            "check_config",
            "list_integrations",
            "get_camera_image",
            "get_calendar_events",
            "get_persons",
            "get_weather",
            "get_host_info",
            "get_updates",
            "list_addons",
            "get_addon_info",
            "addon_start_stop",
            "list_backups",
            "create_backup",
            # Phase 3 tools
            "list_devices",
            "get_device_entities",
            "list_floors",
            "list_labels",
            "get_label_entities",
            "set_state",
            "conversation_process",
            "get_automation_config",
            "create_automation",
            "delete_automation",
            "get_script_config",
            "create_script",
            "delete_script",
            "get_automation_traces",
            "get_todo_items",
            "add_todo_item",
            "update_todo_item",
            "remove_todo_item",
            "create_calendar_event",
            "list_dashboards",
            "get_dashboard_config",
            "save_dashboard_config",
            "bulk_control",
            "bulk_get_states",
            "deep_search",
            "get_supervisor_logs",
            "get_core_logs",
            "get_addon_logs",
            "get_os_info",
            "get_network_info",
            "get_hardware_info",
            "get_resolution_info",
            "browse_addon_store",
            "list_config_files",
            "read_config_file",
            "write_config_file",
            "reload_config",
        ]

        for expected in expected_tools:
            assert expected in tool_names, f"Tool '{expected}' not registered"

    @pytest.mark.asyncio
    async def test_resources_registered(self):
        from app.server import mcp
        resources = await mcp.list_resources()
        # Resource templates have uri_template
        # Check we have at least the static resources
        assert len(resources) >= 1

    @pytest.mark.asyncio
    async def test_prompts_registered(self):
        from app.server import mcp
        prompts = await mcp.list_prompts()
        prompt_names = [p.name for p in prompts]

        expected_prompts = [
            "create_automation",
            "debug_automation",
            "troubleshoot_entity",
            "routine_optimizer",
            "automation_health_check",
            "entity_naming_consistency",
            "dashboard_layout_generator",
            # Phase 3 prompts
            "energy_optimizer",
            "security_audit",
            "device_troubleshooter",
            "template_helper",
            "scene_builder",
            "backup_strategy",
            "floor_plan_organizer",
        ]

        for expected in expected_prompts:
            assert expected in prompt_names, f"Prompt '{expected}' not registered"


class TestToolCalls:
    """Test tool execution with mocked HA API."""

    @pytest.mark.asyncio
    async def test_get_version_tool(self):
        with patch("app.hass.get_version", new_callable=AsyncMock, return_value="2026.3.1"):
            from app.server import mcp
            result = await mcp.call_tool("get_version", {})
            assert len(result) > 0
            # result is a list of content objects
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "2026.3.1" in text

    @pytest.mark.asyncio
    async def test_check_connection_tool(self):
        mock_result = {"connected": True, "version": "2026.3.1"}
        with patch("app.hass.check_api_connection", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("check_connection", {})
            # Extract text from content object
            content = result[0]
            text = content.text if hasattr(content, 'text') else str(content)
            assert "connected" in text
            assert "2026.3.1" in text

    @pytest.mark.asyncio
    async def test_entity_action_tool(self):
        mock_result = [{"entity_id": "light.test", "state": "on"}]
        with patch("app.hass.entity_action", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("entity_action", {
                "entity_id": "light.test",
                "action": "on",
            })
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "light.test" in text

    @pytest.mark.asyncio
    async def test_render_template_tool(self):
        with patch("app.hass.render_template", new_callable=AsyncMock, return_value="22.5"):
            from app.server import mcp
            result = await mcp.call_tool("render_template", {
                "template": "{{ states('sensor.temp') }}",
            })
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "22.5" in text

    @pytest.mark.asyncio
    async def test_check_config_tool(self):
        mock_result = {"result": "valid", "errors": None}
        with patch("app.hass.check_config", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("check_config", {})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "valid" in text

    @pytest.mark.asyncio
    async def test_list_integrations_tool(self):
        with patch("app.hass.get_components", new_callable=AsyncMock, return_value=["mqtt", "zwave_js"]):
            from app.server import mcp
            result = await mcp.call_tool("list_integrations", {})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "mqtt" in text
            assert "zwave_js" in text

    @pytest.mark.asyncio
    async def test_get_persons_tool(self):
        mock_result = [{"entity_id": "person.john", "name": "John", "state": "home"}]
        with patch("app.hass.get_persons", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("get_persons", {})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "John" in text
            assert "home" in text

    @pytest.mark.asyncio
    async def test_get_host_info_tool(self):
        mock_result = {"hostname": "ha-dell", "disk_free": 23.5}
        with patch("app.hass.get_host_info", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("get_host_info", {})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "ha-dell" in text

    @pytest.mark.asyncio
    async def test_list_addons_tool(self):
        mock_result = [
            {"name": "Mosquitto", "slug": "core_mosquitto", "version": "6.4.1",
             "state": "started", "update_available": False, "description": "MQTT"},
        ]
        with patch("app.hass.list_addons", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("list_addons", {})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "Mosquitto" in text

    @pytest.mark.asyncio
    async def test_create_backup_tool(self):
        mock_result = {"slug": "backup_abc"}
        with patch("app.hass.create_backup", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("create_backup", {"name": "Pre-update"})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "backup_abc" in text

    @pytest.mark.asyncio
    async def test_tool_handles_error(self):
        with patch("app.hass.get_version", new_callable=AsyncMock, side_effect=Exception("Connection refused")):
            from app.server import mcp
            result = await mcp.call_tool("get_version", {})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "Error" in text

    # --- Phase 3 tool tests ---

    @pytest.mark.asyncio
    async def test_list_devices_tool(self):
        mock_result = [{"device_id": "abc123", "name": "Kitchen Light", "manufacturer": "Philips", "model": "Hue"}]
        with patch("app.hass.get_devices", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("list_devices", {})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "Kitchen Light" in text
            assert "Philips" in text

    @pytest.mark.asyncio
    async def test_list_floors_tool(self):
        mock_result = [{"floor_id": "ground", "name": "Ground Floor", "areas": ["kitchen", "living_room"]}]
        with patch("app.hass.get_floors", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("list_floors", {})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "Ground Floor" in text

    @pytest.mark.asyncio
    async def test_set_state_tool(self):
        mock_result = {"entity_id": "input_boolean.test", "state": "on"}
        with patch("app.hass.set_state", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("set_state", {"entity_id": "input_boolean.test", "state": "on"})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "input_boolean.test" in text

    @pytest.mark.asyncio
    async def test_conversation_process_tool(self):
        mock_result = {"response": {"speech": {"plain": {"speech": "Turned on the lights"}}}}
        with patch("app.hass.conversation_process", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("conversation_process", {"text": "turn on lights"})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "lights" in text.lower()

    @pytest.mark.asyncio
    async def test_create_automation_tool(self):
        mock_result = {"result": "ok"}
        with patch("app.hass.update_automation_config", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            config = {"alias": "Test", "trigger": [], "action": []}
            result = await mcp.call_tool("create_automation", {"automation_id": "test_auto", "config": config})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "ok" in text

    @pytest.mark.asyncio
    async def test_deep_search_tool(self):
        mock_result = {"query": "kitchen", "total_matches": 5, "matches": {"entities": {"count": 5, "results": []}}}
        with patch("app.hass.deep_search", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("deep_search", {"query": "kitchen"})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "kitchen" in text

    @pytest.mark.asyncio
    async def test_bulk_control_tool(self):
        mock_result = [{"entity_id": "light.a", "result": "ok"}, {"entity_id": "light.b", "result": "ok"}]
        with patch("app.hass.bulk_control", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("bulk_control", {"entity_ids": ["light.a", "light.b"], "action": "off"})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "light.a" in text

    @pytest.mark.asyncio
    async def test_get_resolution_info_tool(self):
        mock_result = {"issues": [], "suggestions": [], "unhealthy": []}
        with patch("app.hass.get_resolution_info", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("get_resolution_info", {})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "issues" in text

    @pytest.mark.asyncio
    async def test_reload_config_tool(self):
        mock_result = []
        with patch("app.hass.reload_all", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("reload_config", {"target": "all"})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert text is not None

    @pytest.mark.asyncio
    async def test_add_todo_item_tool(self):
        mock_result = []
        with patch("app.hass.add_todo_item", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("add_todo_item", {"entity_id": "todo.shopping", "item": "Milk"})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert text is not None

    @pytest.mark.asyncio
    async def test_list_dashboards_tool(self):
        mock_result = [{"url_path": "lovelace", "title": "Home"}]
        with patch("app.hass.get_dashboards", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("list_dashboards", {})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "Home" in text

    @pytest.mark.asyncio
    async def test_get_automation_traces_tool(self):
        mock_result = [{"run_id": "123", "state": "stopped"}]
        with patch("app.hass.get_automation_traces", new_callable=AsyncMock, return_value=mock_result):
            from app.server import mcp
            result = await mcp.call_tool("get_automation_traces", {"automation_id": "abc"})
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            assert "123" in text


class TestTransport:
    """Test the HTTP transport layer."""

    @pytest.mark.asyncio
    async def test_public_endpoints_no_auth(self):
        from starlette.testclient import TestClient
        from app.transport import create_app

        with patch("app.transport._external_api_key", "test-key-123"):
            app = create_app()
            client = TestClient(app)

            # Health is public (no auth required)
            resp = client.get("/health")
            assert resp.status_code in (200, 503)

            # Info is public
            resp = client.get("/info")
            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == "HASS-MCP"
            assert "streamable-http" in data["transports"]

    @pytest.mark.asyncio
    async def test_mcp_endpoint_rejects_no_auth(self):
        from starlette.testclient import TestClient
        from app.transport import create_app

        with patch("app.transport._external_api_key", "test-key-123"):
            app = create_app()
            client = TestClient(app)

            # MCP endpoint should reject without auth
            resp = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "method": "initialize", "id": 1},
            )
            assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_mcp_endpoint_accepts_bearer_token(self):
        from starlette.testclient import TestClient
        from app.transport import create_app

        with patch("app.transport._external_api_key", "test-key-123"):
            app = create_app()
            # Use raise_server_exceptions=False since the SDK transport
            # requires lifespan context (managed by uvicorn in production).
            # We verify auth passes (not 401) even if the transport
            # internals fail without a running event loop.
            client = TestClient(app, raise_server_exceptions=False)

            resp = client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "id": 1,
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"},
                    },
                },
                headers={"Authorization": "Bearer test-key-123"},
            )
            # Should NOT be 401 (auth passed). May be 500 due to
            # missing lifespan context in test, but auth was accepted.
            assert resp.status_code != 401
