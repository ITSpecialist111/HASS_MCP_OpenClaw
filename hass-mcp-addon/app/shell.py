"""Shell / process / Python execution helpers (no safeguards)."""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from typing import Any


async def shell_exec(command: str, cwd: str | None = None,
                     env: dict | None = None, timeout: float | None = 120.0) -> dict[str, Any]:
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=proc_env,
        executable="/bin/bash" if os.path.exists("/bin/bash") else None,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return {"error": "timeout", "rc": -1}
    return {
        "rc": proc.returncode,
        "stdout": out.decode("utf-8", errors="replace"),
        "stderr": err.decode("utf-8", errors="replace"),
    }


async def shell_exec_stream(command: str, max_lines: int = 1000) -> dict[str, Any]:
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        executable="/bin/bash" if os.path.exists("/bin/bash") else None,
    )
    lines: list[str] = []
    assert proc.stdout
    async for raw in proc.stdout:
        lines.append(raw.decode("utf-8", errors="replace").rstrip())
        if len(lines) >= max_lines:
            proc.kill()
            break
    rc = await proc.wait()
    return {"rc": rc, "lines": lines}


async def python_exec(code: str, globals_: dict | None = None) -> dict[str, Any]:
    """Run arbitrary Python in this process."""
    g = {"__name__": "__exec__"}
    if globals_:
        g.update(globals_)
    try:
        # Try eval first (single expression)
        try:
            result = eval(code, g)
            if asyncio.iscoroutine(result):
                result = await result
            return {"ok": True, "result": repr(result)}
        except SyntaxError:
            pass
        # Fall back to exec (statements)
        exec(compile(code, "<python_exec>", "exec"), g)
        return {"ok": True, "result": None, "globals": list(g.keys())}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


async def pip_install(packages: list[str]) -> dict[str, Any]:
    return await shell_exec(f"{sys.executable} -m pip install {' '.join(packages)}",
                            timeout=300.0)


async def apk_add(packages: list[str]) -> dict[str, Any]:
    return await shell_exec(f"apk add --no-cache {' '.join(packages)}", timeout=180.0)
