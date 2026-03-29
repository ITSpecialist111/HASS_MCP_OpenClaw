"""HASS MCP Server - HTTP transport with API key authentication.

Uses the MCP SDK's built-in Streamable HTTP and SSE transports,
wrapped with authentication middleware for OpenClaw compatibility.
"""

import logging
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .config import HA_TOKEN, get_option
from .server import mcp

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------

# The API key that external MCP clients must provide.
# If the user sets ha_token in add-on config, that value is used as the API key
# for external clients. Otherwise the Supervisor token is used.
_external_api_key = get_option("ha_token") or HA_TOKEN


def _check_auth(request: Request) -> bool:
    """Validate the API key from the request.

    Accepts the token in:
      - Authorization: Bearer <token>
      - X-API-Key: <token>
      - ?api_key=<token> query parameter
    """
    if not _external_api_key:
        logger.warning("No API key configured — MCP server is unauthenticated!")
        return True

    # Check Authorization header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token == _external_api_key:
            return True

    # Check X-API-Key header
    api_key_header = request.headers.get("x-api-key", "")
    if api_key_header and api_key_header == _external_api_key:
        return True

    # Check query parameter
    api_key_param = request.query_params.get("api_key", "")
    if api_key_param and api_key_param == _external_api_key:
        return True

    return False


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces API key auth on MCP endpoints."""

    # Paths that don't require authentication
    PUBLIC_PATHS = {"/health", "/info"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        if not _check_auth(request):
            return JSONResponse(
                {
                    "error": "Unauthorized. Provide a valid API key via "
                    "Authorization: Bearer <token>, X-API-Key header, "
                    "or ?api_key= query parameter."
                },
                status_code=401,
            )

        return await call_next(request)


# --------------------------------------------------------------------------
# Health & info endpoints
# --------------------------------------------------------------------------

async def handle_health(request: Request) -> JSONResponse:
    """Health check endpoint (GET /health)."""
    from . import hass

    status = await hass.check_api_connection()
    code = 200 if status.get("connected") else 503
    return JSONResponse(
        {"status": "ok" if code == 200 else "degraded", "ha": status},
        status_code=code,
    )


async def handle_info(request: Request) -> JSONResponse:
    """Server info endpoint (GET /info)."""
    return JSONResponse(
        {
            "name": "HASS-MCP",
            "version": "1.0.0",
            "description": "Home Assistant MCP Server Add-on",
            "transports": ["streamable-http", "sse"],
            "auth_methods": ["bearer_token", "x-api-key", "query_param"],
        }
    )


# --------------------------------------------------------------------------
# Starlette app
# --------------------------------------------------------------------------

def create_app() -> Starlette:
    """Create the Starlette ASGI app.

    Uses the SDK's built-in Streamable HTTP app as the base (preserving its
    lifespan which initializes the session manager), then adds SSE routes
    and utility endpoints. Auth middleware wraps everything.
    """
    # Build the SDK streamable HTTP app — this has the critical lifespan
    # that starts the session manager (required for /mcp to work).
    streamable_app = mcp.streamable_http_app()

    # Build the SDK SSE app and grab its routes (SSE has no lifespan).
    sse_app = mcp.sse_app()

    # Add SSE routes and our utility routes to the streamable app's router.
    for route in sse_app.routes:
        streamable_app.routes.append(route)
    streamable_app.routes.append(
        Route("/health", handle_health, methods=["GET"])
    )
    streamable_app.routes.append(
        Route("/info", handle_info, methods=["GET"])
    )

    # Add auth middleware to the SDK app.
    streamable_app.add_middleware(AuthMiddleware)

    return streamable_app
