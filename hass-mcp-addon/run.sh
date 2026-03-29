#!/usr/bin/with-contenv bashio

# ==============================================================================
# HASS MCP Server - Add-on run script
# ==============================================================================

bashio::log.info "Starting HASS MCP Server add-on..."

# Read configuration from add-on options
export LOG_LEVEL=$(bashio::config 'log_level')

# Read optional HA token (for external client authentication)
HA_TOKEN_OPT=$(bashio::config 'ha_token')
if [ -n "${HA_TOKEN_OPT}" ] && [ "${HA_TOKEN_OPT}" != "null" ]; then
    export HA_TOKEN="${HA_TOKEN_OPT}"
    bashio::log.info "Using user-configured HA token for external auth"
else
    bashio::log.info "No external HA token set — external clients must use the Supervisor token"
fi

# Always use Supervisor proxy for internal HA API access
export HA_URL="http://supervisor/core"

bashio::log.info "Log level: ${LOG_LEVEL}"
bashio::log.info "HA API: ${HA_URL}"
bashio::log.info "Server port: 8080"

# Start the MCP server
exec python3 -m app
