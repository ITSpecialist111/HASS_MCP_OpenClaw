"""Common helpers for tool modules."""
from __future__ import annotations

import json
from functools import wraps
from typing import Any, Callable


def jdump(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": f"serialization failed: {e}"})


def safe(fn: Callable) -> Callable:
    """Wrap an async tool fn so exceptions become JSON error strings."""
    @wraps(fn)
    async def inner(*a, **kw):
        try:
            res = await fn(*a, **kw)
            if isinstance(res, str):
                return res
            return jdump(res)
        except Exception as e:
            return jdump({"error": f"{type(e).__name__}: {e}"})
    return inner


def tool(mcp, name: str | None = None):
    """Register an async function as an MCP tool with safe-json wrapping."""
    def deco(fn):
        wrapped = safe(fn)
        wrapped.__name__ = name or fn.__name__
        wrapped.__doc__ = fn.__doc__
        mcp.tool(name=name or fn.__name__)(wrapped)
        return wrapped
    return deco
