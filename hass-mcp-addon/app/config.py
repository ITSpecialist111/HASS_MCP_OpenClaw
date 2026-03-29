"""HASS MCP Server - Configuration module.

Reads configuration from /data/options.json (HA add-on config)
or falls back to environment variables for standalone usage.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# HA add-on options file path
OPTIONS_FILE = Path("/data/options.json")


def _load_addon_options() -> dict:
    """Load options from HA add-on config file."""
    if OPTIONS_FILE.exists():
        try:
            with open(OPTIONS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read add-on options: %s", e)
    return {}


_options = _load_addon_options()


def get_option(key: str, default: str = "") -> str:
    """Get a config value from add-on options or environment variable."""
    val = _options.get(key, "")
    if val:
        return str(val)
    return os.environ.get(key.upper(), default)


# --- Resolved configuration ---

# Home Assistant URL: env var (set by run.sh) or Supervisor proxy or localhost
HA_URL = os.environ.get("HA_URL", "") or "http://supervisor/core"

# Authentication token for HA API calls:
# - Inside add-on: SUPERVISOR_TOKEN is auto-injected
# - Standalone: user sets HA_TOKEN env var
# The user-configured ha_token from add-on options is used for EXTERNAL client auth,
# not for internal HA API calls. Internal calls always use SUPERVISOR_TOKEN.
HA_TOKEN = (
    os.environ.get("SUPERVISOR_TOKEN", "")
    or os.environ.get("HA_TOKEN", "")
)

# Server port (fixed at 8080 to match Docker port mapping)
SERVER_PORT = 8080

LOG_LEVEL = get_option("log_level", "info").upper()


def get_headers() -> dict[str, str]:
    """Build HTTP headers for Home Assistant API requests."""
    headers = {"Content-Type": "application/json"}
    if HA_TOKEN:
        headers["Authorization"] = f"Bearer {HA_TOKEN}"
    return headers


def get_api_base() -> str:
    """Return the HA API base URL (with /api suffix)."""
    base = HA_URL.rstrip("/")
    if base.endswith("/core"):
        return f"{base}/api"
    return f"{base}/api"


# Supervisor API base URL and headers
SUPERVISOR_URL = "http://supervisor"


def get_supervisor_headers() -> dict[str, str]:
    """Build HTTP headers for Supervisor API requests."""
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("SUPERVISOR_TOKEN", "") or HA_TOKEN
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers
