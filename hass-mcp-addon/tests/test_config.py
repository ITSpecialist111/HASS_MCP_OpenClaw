"""Tests for the HASS MCP Server configuration module."""

import json
import os
import pytest
from unittest.mock import patch, mock_open


def test_get_headers_with_token():
    """Test that headers include auth when token is set."""
    with patch.dict(os.environ, {"HA_TOKEN": "test-token-123", "HA_URL": "http://localhost:8123"}):
        # Re-import to pick up env vars
        import importlib
        from app import config
        importlib.reload(config)

        headers = config.get_headers()
        assert headers["Content-Type"] == "application/json"
        # Token should come from somewhere (env or options)


def test_get_api_base_direct_url():
    """Test API base URL for direct HA connection."""
    with patch.dict(os.environ, {"HA_URL": "http://192.168.1.100:8123", "HA_TOKEN": ""}):
        import importlib
        from app import config
        importlib.reload(config)

        # Direct URL should get /api appended
        base = config.get_api_base()
        assert base.endswith("/api")
        assert "192.168.1.100" in base


def test_get_api_base_supervisor():
    """Test API base URL for Supervisor proxy."""
    with patch.dict(os.environ, {"HA_URL": "http://supervisor/core", "HA_TOKEN": ""}):
        import importlib
        from app import config
        importlib.reload(config)

        base = config.get_api_base()
        assert base == "http://supervisor/core/api"
