#!/usr/bin/with-contenv bashio

bashio::log.info "Starting HASS MCP Server v2.0 (unrestricted) ..."

export LOG_LEVEL=$(bashio::config 'log_level')
export LOG_TOOL_CALLS=$(bashio::config 'log_tool_calls')

HA_TOKEN_OPT=$(bashio::config 'ha_token')
if [ -n "${HA_TOKEN_OPT}" ] && [ "${HA_TOKEN_OPT}" != "null" ]; then
    export HA_TOKEN="${HA_TOKEN_OPT}"
fi

# Always reach Core via supervisor proxy
export HA_URL="http://supervisor/core"
export HA_WS_URL="ws://supervisor/core/websocket"
export SUPERVISOR_URL="http://supervisor"
export RECORDER_DB="/config/home-assistant_v2.db"

bashio::log.info "Log level: ${LOG_LEVEL}"
bashio::log.info "HA REST: ${HA_URL}"
bashio::log.info "HA WS:   ${HA_WS_URL}"
bashio::log.info "Server port: 8080"

exec python3 -m app
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
