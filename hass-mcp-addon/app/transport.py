"""HASS MCP Server - HTTP transport with API key authentication.

Uses the MCP SDK's built-in Streamable HTTP and SSE transports,
wrapped with authentication middleware for OpenClaw compatibility.
"""

import logging
from contextlib import AsyncExitStack, asynccontextmanager

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from .config import HA_TOKEN, get_option
from .server import mcp
from .compact import build_compact

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
            "version": "2.5.0",
            "description": "Home Assistant MCP Server Add-on (full-control + God Mode)",
            "transports": ["streamable-http", "sse"],
            "auth_methods": ["bearer_token", "x-api-key", "query_param"],
            "endpoints": {
                "/mcp": "full surface (~620 tools) — use with OpenClaw/Claude/Cursor",
                "/compact/mcp": "dispatcher surface (~52 tools) — use with GitHub Copilot (128-tool cap)",
                "/sse": "legacy SSE transport",
            },
        }
    )


# --------------------------------------------------------------------------
# Starlette app
# --------------------------------------------------------------------------

def create_app() -> Starlette:
    """Create the Starlette ASGI app.

    Combines two FastMCP streamable-HTTP apps (full + compact dispatcher)
    under one parent Starlette app with a merged lifespan so both session
    managers start. Auth middleware wraps everything.
    """
    # Build the SDK streamable HTTP app (full surface, ~620 tools).
    streamable_app = mcp.streamable_http_app()

    # Build the SDK SSE app and grab its routes (SSE has no lifespan).
    sse_app = mcp.sse_app()

    # Build the compact dispatcher surface (~52 tools) — same underlying
    # tools, reshaped so clients with tool-count caps (e.g. GitHub Copilot,
    # 128) still see everything via per-module dispatchers.
    compact_mcp = build_compact()
    compact_app = compact_mcp.streamable_http_app()

    # Merged lifespan — starts BOTH FastMCP session managers.
    @asynccontextmanager
    async def combined_lifespan(app):
        async with AsyncExitStack() as stack:
            if streamable_app.router.lifespan_context is not None:
                await stack.enter_async_context(
                    streamable_app.router.lifespan_context(streamable_app)
                )
            if compact_app.router.lifespan_context is not None:
                await stack.enter_async_context(
                    compact_app.router.lifespan_context(compact_app)
                )
            yield

    # Parent app — carries the combined lifespan and all routes.
    routes: list = list(streamable_app.routes)
    routes.extend(sse_app.routes)
    routes.append(Route("/health", handle_health, methods=["GET"]))
    routes.append(Route("/info", handle_info, methods=["GET"]))
    # Compact dispatcher surface at /compact/mcp
    routes.append(Mount("/compact", app=compact_app))

    parent = Starlette(
        routes=routes,
        lifespan=combined_lifespan,
        middleware=[Middleware(AuthMiddleware)],
    )
    return parent
