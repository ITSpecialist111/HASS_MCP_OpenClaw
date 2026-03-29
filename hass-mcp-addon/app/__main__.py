"""HASS MCP Server - Main entry point.

Runs the HTTP transport server (uvicorn) for Streamable HTTP and SSE access.
"""

import logging
import sys

from .config import LOG_LEVEL, SERVER_PORT
from .transport import create_app

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


def main():
    """Start the MCP HTTP server."""
    import uvicorn

    logger.info("Starting HASS MCP Server on port %d", SERVER_PORT)
    logger.info("Log level: %s", LOG_LEVEL)

    app = create_app()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=SERVER_PORT,
        log_level=LOG_LEVEL.lower(),
        access_log=LOG_LEVEL == "DEBUG",
    )


if __name__ == "__main__":
    main()
