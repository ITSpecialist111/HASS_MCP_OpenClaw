"""Compact MCP surface — dispatcher-style.

One MCP tool per source module; each takes `action` + `args`.
Total tool count stays below 128 (per-client limits e.g. GitHub Copilot)
while preserving the entire underlying surface of the full /mcp endpoint.

The compact server shares the same `mcp` backing instance's registered
tools — we just reshape the client-facing interface.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from .server import mcp as full_mcp
from . import tools as _tools_pkg

logger = logging.getLogger(__name__)

mcp_compact = FastMCP(
    "HASS-MCP-Compact",
    host="0.0.0.0",
    port=8080,
)


def _tool_summary(tool_name: str) -> dict[str, Any]:
    t = full_mcp._tool_manager._tools.get(tool_name)  # type: ignore[attr-defined]
    if t is None:
        return {"name": tool_name, "error": "not found"}
    return {
        "name": t.name,
        "description": (t.description or "").strip().split("\n")[0][:200],
        "parameters": t.parameters,
    }


async def _run_tool(tool_name: str, args: dict[str, Any] | None) -> Any:
    t = full_mcp._tool_manager._tools.get(tool_name)  # type: ignore[attr-defined]
    if t is None:
        return {"error": f"unknown action '{tool_name}'"}
    try:
        return await t.run(args or {})
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def _make_dispatcher(module_name: str, tool_names: list[str]):
    """Create a dispatcher coroutine for one module."""
    async def dispatcher(action: str = "list",
                        args: dict[str, Any] | None = None) -> str:
        if action in ("list", "__list__", "help", "?"):
            return json.dumps({
                "module": module_name,
                "count": len(tool_names),
                "actions": [_tool_summary(n) for n in tool_names],
            }, indent=2, default=str)
        if action not in tool_names:
            return json.dumps({
                "error": f"action '{action}' not in module '{module_name}'",
                "hint": f"call with action='list' to see all "
                        f"{len(tool_names)} available actions",
            })
        result = await _run_tool(action, args)
        if isinstance(result, (str, bytes)):
            return result if isinstance(result, str) else result.decode()
        try:
            return json.dumps(result, indent=2, default=str)
        except Exception:
            return str(result)

    dispatcher.__name__ = module_name
    preview = ", ".join(tool_names[:5]) + (
        f", ...+{len(tool_names)-5} more" if len(tool_names) > 5 else "")
    dispatcher.__doc__ = (
        f"Dispatcher for module '{module_name}' — {len(tool_names)} "
        f"underlying actions: {preview}. "
        f"Call with action='list' to enumerate all actions with their "
        f"parameter schemas, then call again with action='<name>' and "
        f"args={{...}} to invoke a specific action."
    )
    return dispatcher


def build_compact() -> FastMCP:
    """Register one dispatcher per module, plus a top-level discovery tool."""
    # Module dispatchers
    for module_name, tool_names in _tools_pkg.MODULE_TOOLS.items():
        if not tool_names:
            continue
        fn = _make_dispatcher(module_name, tool_names)
        mcp_compact.tool(name=module_name)(fn)

    # Also expose every base-level tool declared directly on `mcp` in
    # server.py (get_entity, list_entities, etc.) via a single `core` dispatcher.
    all_names = set(full_mcp._tool_manager._tools.keys())  # type: ignore[attr-defined]
    mod_names: set[str] = set()
    for names in _tools_pkg.MODULE_TOOLS.values():
        mod_names.update(names)
    core_names = sorted(all_names - mod_names)
    if core_names:
        fn = _make_dispatcher("core", core_names)
        mcp_compact.tool(name="core")(fn)

    # Top-level discovery tool
    @mcp_compact.tool(name="hass_modules")
    async def hass_modules() -> str:
        """List every module available on this compact endpoint and the
        number of underlying actions each one dispatches."""
        modules = [
            {"module": "core", "actions": len(core_names)}
        ] if core_names else []
        for module_name, tool_names in _tools_pkg.MODULE_TOOLS.items():
            if tool_names:
                modules.append({
                    "module": module_name,
                    "actions": len(tool_names),
                })
        return json.dumps({
            "modules": modules,
            "total_underlying_tools": sum(m["actions"] for m in modules),
            "usage": (
                "Each module is a dispatcher. Call "
                "<module>(action='list') to see its actions + schemas, "
                "then <module>(action='<name>', args={...}) to invoke."
            ),
        }, indent=2)

    logger.info(
        "Compact endpoint ready: %d dispatchers over %d underlying tools",
        len(_tools_pkg.MODULE_TOOLS) + (1 if core_names else 0) + 1,
        len(all_names),
    )
    return mcp_compact
