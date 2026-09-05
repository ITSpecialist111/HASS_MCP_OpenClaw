# Changelog

## 2.5.1 - 2026-09-05

### Fixed

- Reuse open Home Assistant WebSocket connections with current `websockets` releases. The previous connection check treated an absent legacy `closed` attribute as a closed connection, opening replacements without releasing existing sockets. This could exhaust Supervisor's connection pool and make other add-ons time out during their opening handshake.
- Keep legacy `closed`-flag compatibility for older WebSocket connection implementations.
- Close candidate connections when authentication fails or is cancelled.
- Prevent a stale reader from clearing a newer connection, its pending requests, or its connected state.
- Replace concatenated add-on manifest blocks with one unambiguous configuration. Preserve all previously effective permissions, options, and runtime settings while correcting the version and repository URL.
- Keep the MCP SDK below version 2, which removed the `FastMCP` API used by this server. This prevents fresh builds from installing an incompatible SDK.

### Validation

- All 65 local tests pass with MCP SDK 1.x, including nine WebSocket lifecycle regressions and three release checks.
- Add regression tests for sequential and concurrent connection reuse, repeated sends, stale readers, reconnects, authentication cleanup, cancellation, and legacy connection state.
- Add release checks for duplicate manifest keys, supported SDK versions, and consistent manifest/runtime/repository metadata.
- Confirm the live fix restores Automation Inspector's connection to Home Assistant 2026.9.0. A fresh inspection completed successfully with 151 automations and 14 scripts.
- A local container build was not run because the Docker engine was unavailable. The live recovery validates the WebSocket fix, not a rebuilt 2.5.1 image.

### Update Notes

- Repository installations: refresh the Home Assistant add-on store and update HASS MCP to 2.5.1.
- Local installations: replace the local add-on source with this release's `hass-mcp-addon` directory, then rebuild the add-on. Restarting alone does not update an existing container image.
- Updating or rebuilding the MCP add-on briefly disconnects MCP clients. Home Assistant Core does not need restarting.
- This is a source release. Home Assistant builds the add-on locally; no prebuilt container image is published.
- Existing experimental/full-control warnings still apply. This release does not add or expand permissions.