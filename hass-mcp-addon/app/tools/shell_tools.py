"""§28 Shell / system."""
from __future__ import annotations

import os
import signal
from typing import Any

from .. import shell as _shell
from ._helpers import tool


def register(mcp) -> int:

    @tool(mcp)
    async def shell_exec(command: str, cwd: str | None = None,
                          env: dict | None = None, timeout: float = 120.0) -> dict:
        """§28 Run an arbitrary shell command (bash). Returns rc/stdout/stderr."""
        return await _shell.shell_exec(command, cwd=cwd, env=env, timeout=timeout)

    @tool(mcp)
    async def shell_exec_stream(command: str, max_lines: int = 1000) -> dict:
        """§28 Run a command, capture lines as they appear."""
        return await _shell.shell_exec_stream(command, max_lines=max_lines)

    @tool(mcp)
    async def python_exec(code: str) -> dict:
        """§28 Execute arbitrary Python code in this process."""
        return await _shell.python_exec(code)

    @tool(mcp)
    async def pip_install(packages: list[str]) -> dict:
        """§28 pip install into the add-on venv."""
        return await _shell.pip_install(packages)

    @tool(mcp)
    async def apk_add(packages: list[str]) -> dict:
        """§28 Install Alpine packages."""
        return await _shell.apk_add(packages)

    @tool(mcp)
    async def env_get(name: str | None = None) -> Any:
        """§28 Read an env var (or all when name omitted)."""
        if name is None:
            return dict(os.environ)
        return {name: os.environ.get(name)}

    @tool(mcp)
    async def env_set(name: str, value: str) -> dict:
        """§28 Set an env var in this process."""
        os.environ[name] = value
        return {name: value}

    @tool(mcp)
    async def process_list() -> dict:
        """§28 List processes (ps aux)."""
        return await _shell.shell_exec("ps -ef")

    @tool(mcp)
    async def process_kill(pid: int, sig: int = 15) -> dict:
        """§28 Kill a process by pid."""
        os.kill(pid, sig)
        return {"pid": pid, "signal": sig}

    @tool(mcp)
    async def cron_list() -> dict:
        """§28 List crontab."""
        return await _shell.shell_exec("crontab -l 2>/dev/null || echo 'no crontab'")

    @tool(mcp)
    async def cron_add(line: str) -> dict:
        """§28 Add a line to crontab."""
        return await _shell.shell_exec(
            f"(crontab -l 2>/dev/null; echo {line!r}) | crontab -")

    @tool(mcp)
    async def cron_remove(pattern: str) -> dict:
        """§28 Remove crontab lines matching a regex."""
        return await _shell.shell_exec(
            f"crontab -l 2>/dev/null | grep -v -E {pattern!r} | crontab -")

    return 12
