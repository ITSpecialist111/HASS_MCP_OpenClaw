"""§25 Files / storage. NO path restrictions per spec."""
from __future__ import annotations

import base64
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import httpx

from .. import shell as _shell
from ._helpers import tool


def register(mcp) -> int:

    @tool(mcp)
    async def read_file(path: str, max_bytes: int = 5_000_000,
                         binary: bool = False) -> dict:
        """§25 Read a file from anywhere on the host."""
        with open(path, "rb") as f:
            data = f.read(max_bytes + 1)
        truncated = len(data) > max_bytes
        data = data[:max_bytes]
        if binary:
            return {"path": path, "size": len(data), "truncated": truncated,
                    "base64": base64.b64encode(data).decode()}
        return {"path": path, "size": len(data), "truncated": truncated,
                "content": data.decode("utf-8", errors="replace")}

    @tool(mcp)
    async def write_file(path: str, content: str, base64_encoded: bool = False,
                          mkdirs: bool = True) -> dict:
        """§25 Write a file (no backup, no allow-list)."""
        if mkdirs:
            d = os.path.dirname(path)
            if d:
                os.makedirs(d, exist_ok=True)
        data = base64.b64decode(content) if base64_encoded else content.encode()
        with open(path, "wb") as f:
            f.write(data)
        return {"path": path, "bytes": len(data)}

    @tool(mcp)
    async def append_file(path: str, content: str) -> dict:
        """§25 Append text to a file."""
        with open(path, "a") as f:
            f.write(content)
        return {"path": path, "appended_bytes": len(content)}

    @tool(mcp)
    async def delete_file(path: str) -> dict:
        """§25 Delete a file or directory (recursive)."""
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return {"path": path, "deleted": True}

    @tool(mcp)
    async def move_file(src: str, dst: str) -> dict:
        """§25 Move/rename a file."""
        shutil.move(src, dst)
        return {"src": src, "dst": dst}

    @tool(mcp)
    async def copy_file(src: str, dst: str) -> dict:
        """§25 Copy a file or directory."""
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        return {"src": src, "dst": dst}

    @tool(mcp)
    async def chmod_file(path: str, mode: str) -> dict:
        """§25 chmod (mode in octal string e.g. '755')."""
        os.chmod(path, int(mode, 8))
        return {"path": path, "mode": mode}

    @tool(mcp)
    async def chown_file(path: str, user: str, group: str | None = None) -> dict:
        """§25 chown via shell."""
        return await _shell.shell_exec(f"chown {user}{':' + group if group else ''} {path!r}")

    @tool(mcp)
    async def list_dir(path: str = "/", details: bool = False) -> Any:
        """§25 List directory contents."""
        entries = sorted(os.listdir(path))
        if not details:
            return entries
        out = []
        for e in entries:
            p = os.path.join(path, e)
            try:
                st = os.stat(p)
                out.append({"name": e, "size": st.st_size, "mode": oct(st.st_mode),
                            "is_dir": os.path.isdir(p), "mtime": st.st_mtime})
            except Exception as ex:
                out.append({"name": e, "error": str(ex)})
        return out

    @tool(mcp)
    async def mkdir(path: str, parents: bool = True) -> dict:
        """§25 mkdir (mkdir -p)."""
        os.makedirs(path, exist_ok=True) if parents else os.mkdir(path)
        return {"path": path}

    @tool(mcp)
    async def rmdir(path: str, recursive: bool = True) -> dict:
        """§25 Remove directory."""
        shutil.rmtree(path) if recursive else os.rmdir(path)
        return {"path": path}

    @tool(mcp)
    async def glob_files(pattern: str, root: str = "/config") -> list:
        """§25 Find files by pattern (recursive)."""
        return [str(p) for p in Path(root).rglob(pattern)]

    @tool(mcp)
    async def grep(pattern: str, path: str = "/config",
                    extra_args: str = "") -> dict:
        """§25 ripgrep search."""
        return await _shell.shell_exec(f"rg -n {extra_args} {pattern!r} {path!r}",
                                        timeout=60.0)

    @tool(mcp)
    async def tail_file(path: str, lines: int = 100) -> dict:
        """§25 Tail last N lines."""
        return await _shell.shell_exec(f"tail -n {lines} {path!r}")

    @tool(mcp)
    async def download_url(url: str, dest: str, headers: dict | None = None) -> dict:
        """§25 Download a URL to a file."""
        async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as c:
            r = await c.get(url, headers=headers or {})
            r.raise_for_status()
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            with open(dest, "wb") as f:
                f.write(r.content)
        return {"url": url, "dest": dest, "bytes": len(r.content)}

    @tool(mcp)
    async def upload_file(path: str, content_b64: str) -> dict:
        """§25 Write base64 content to a file."""
        data = base64.b64decode(content_b64)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return {"path": path, "bytes": len(data)}

    @tool(mcp)
    async def unzip(archive: str, dest: str) -> dict:
        """§25 Unzip a .zip archive."""
        return await _shell.shell_exec(f"unzip -o {archive!r} -d {dest!r}")

    @tool(mcp)
    async def tar_extract(archive: str, dest: str) -> dict:
        """§25 Extract tar/tar.gz/tar.xz."""
        return await _shell.shell_exec(f"tar -xf {archive!r} -C {dest!r}")

    @tool(mcp)
    async def tar_create(archive: str, sources: list[str]) -> dict:
        """§25 Create tar.gz archive."""
        srcs = " ".join(repr(s) for s in sources)
        return await _shell.shell_exec(f"tar -czf {archive!r} {srcs}")

    @tool(mcp)
    async def git_clone(repo: str, dest: str) -> dict:
        """§25 git clone."""
        return await _shell.shell_exec(f"git clone {repo!r} {dest!r}")

    @tool(mcp)
    async def git_pull(path: str = "/config") -> dict:
        """§25 git pull."""
        return await _shell.shell_exec(f"git -C {path!r} pull")

    @tool(mcp)
    async def git_status(path: str = "/config") -> dict:
        """§25 git status."""
        return await _shell.shell_exec(f"git -C {path!r} status")

    @tool(mcp)
    async def git_commit(path: str, message: str) -> dict:
        """§25 git add + commit."""
        return await _shell.shell_exec(
            f"git -C {path!r} add -A && git -C {path!r} commit -m {message!r}")

    @tool(mcp)
    async def git_push(path: str = "/config", remote: str = "origin",
                       branch: str = "main") -> dict:
        """§25 git push."""
        return await _shell.shell_exec(f"git -C {path!r} push {remote} {branch}")

    return 23
