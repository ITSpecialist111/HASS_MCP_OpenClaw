"""§57 Self-modification (self-edit, self-test, clone, propose PR, tool synthesis)."""
from __future__ import annotations

import importlib
import os
import sys
from typing import Any

from .. import shell as _shell
from ._helpers import tool

_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TOOLS_DIR = os.path.join(_APP_DIR, "tools")


def register(mcp) -> int:

    @tool(mcp)
    async def mcp_self_read(relative_path: str) -> dict:
        """§57 Read a file inside the MCP app source tree."""
        path = os.path.join(_APP_DIR, relative_path.lstrip("/"))
        with open(path) as f: return {"path": path, "content": f.read()}

    @tool(mcp)
    async def mcp_self_edit(relative_path: str, content: str,
                              backup: bool = False) -> dict:
        """§57 Overwrite a file inside the MCP app source tree."""
        path = os.path.join(_APP_DIR, relative_path.lstrip("/"))
        if backup and os.path.exists(path):
            with open(path) as f: prev = f.read()
            with open(path + ".bak", "w") as f: f.write(prev)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f: f.write(content)
        return {"path": path, "bytes": len(content)}

    @tool(mcp)
    async def mcp_self_reload_module(module: str) -> dict:
        """§57 Reload a python module already loaded in this process."""
        mod_name = module if module.startswith("app.") else f"app.{module}"
        mod = sys.modules.get(mod_name)
        if mod is None:
            mod = importlib.import_module(mod_name)
        else:
            mod = importlib.reload(mod)
        return {"module": mod_name, "file": getattr(mod, "__file__", None)}

    @tool(mcp)
    async def mcp_self_register_tool_module(module_name: str) -> dict:
        """§57 Import app.tools.<module_name> and call its register(mcp)."""
        from .. import server as _s
        mod = importlib.import_module(f".tools.{module_name}", package="app")
        added = mod.register(_s.mcp) if hasattr(mod, "register") else 0
        return {"module": module_name, "tools_added": added}

    @tool(mcp)
    async def mcp_synthesize_tool(module_name: str, source: str,
                                    autoregister: bool = True) -> dict:
        """§57 Write a brand new tool module and (optionally) register it now."""
        path = os.path.join(_TOOLS_DIR, f"{module_name}.py")
        with open(path, "w") as f: f.write(source)
        out: dict[str, Any] = {"path": path, "bytes": len(source)}
        if autoregister:
            from .. import server as _s
            mod = importlib.import_module(f".tools.{module_name}", package="app")
            out["tools_added"] = mod.register(_s.mcp) if hasattr(mod, "register") else 0
        return out

    @tool(mcp)
    async def mcp_self_test(test_command: str = "python -m pytest -q") -> Any:
        """§57 Run the test suite (or arbitrary check command)."""
        return await _shell.shell_exec(
            f"cd {_APP_DIR}/.. && {test_command}", timeout=600.0)

    @tool(mcp)
    async def mcp_clone_to_other_host(host: str, user: str,
                                        password: str | None = None,
                                        key_path: str | None = None,
                                        remote_dir: str = "/addons/local/hass_mcp_server") -> dict:
        """§57 rsync the local add-on tree to a peer over SSH."""
        ident = f"-i {key_path} " if key_path else ""
        env_pass = f"sshpass -p {password!r} " if password and not key_path else ""
        cmd = (f"{env_pass}rsync -az -e 'ssh {ident}-o StrictHostKeyChecking=no' "
                f"{_APP_DIR}/../ {user}@{host}:{remote_dir}/")
        return await _shell.shell_exec(cmd, timeout=600.0)

    @tool(mcp)
    async def mcp_propose_pr(repo_dir: str, branch: str, message: str,
                                push: bool = True) -> Any:
        """§57 git add/commit (and optionally push) a branch in a repo dir."""
        cmd = (f"cd {repo_dir} && git checkout -B {branch} && "
                f"git add -A && git commit -m {message!r}")
        r = await _shell.shell_exec(cmd, timeout=120.0)
        if push:
            p = await _shell.shell_exec(
                f"cd {repo_dir} && git push -u origin {branch}", timeout=120.0)
            return {"commit": r, "push": p}
        return {"commit": r}

    @tool(mcp)
    async def mcp_rebuild_addon() -> Any:
        """§57 Rebuild this add-on via Supervisor (picks up Dockerfile changes)."""
        from .. import supervisor_client as sup
        return await sup.post("/addons/local_hass_mcp_server/rebuild")

    @tool(mcp)
    async def mcp_restart_self() -> Any:
        """§57 Restart this add-on (loses in-flight requests)."""
        from .. import supervisor_client as sup
        return await sup.post("/addons/local_hass_mcp_server/restart")

    @tool(mcp)
    async def mcp_list_loaded_tools() -> list:
        """§57 List currently registered FastMCP tools."""
        from .. import server as _s
        names = []
        try:
            tm = _s.mcp._tool_manager  # type: ignore[attr-defined]
            names = list(tm._tools.keys())  # type: ignore[attr-defined]
        except Exception:
            pass
        return names

    return 11
