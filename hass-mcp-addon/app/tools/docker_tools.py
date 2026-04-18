"""§29 Docker socket ops."""
from __future__ import annotations

from .. import docker_client as dc
from ._helpers import tool


def register(mcp) -> int:

    @tool(mcp)
    async def docker_ps(all_: bool = True) -> list:
        """§29 List containers."""
        return dc.ps(all_=all_)

    @tool(mcp)
    async def docker_logs(name: str, tail: int = 200) -> str:
        """§29 Tail container logs."""
        return dc.logs(name, tail=tail)

    @tool(mcp)
    async def docker_stats(name: str) -> dict:
        """§29 Container resource stats."""
        return dc.stats(name)

    @tool(mcp)
    async def docker_inspect(name: str) -> dict:
        """§29 docker inspect <name>."""
        return dc.inspect(name)

    @tool(mcp)
    async def docker_exec(name: str, cmd: str) -> dict:
        """§29 docker exec <name> <cmd>."""
        return dc.exec_(name, cmd)

    @tool(mcp)
    async def docker_restart(name: str) -> dict:
        """§29 Restart a container."""
        return dc.restart(name)

    @tool(mcp)
    async def docker_kill(name: str) -> dict:
        """§29 Kill (SIGKILL) a container."""
        return dc.kill(name)

    @tool(mcp)
    async def docker_pull(image: str) -> dict:
        """§29 docker pull <image>."""
        return dc.pull(image)

    @tool(mcp)
    async def docker_image_ls() -> list:
        """§29 List images."""
        return dc.image_ls()

    @tool(mcp)
    async def docker_image_rm(image: str, force: bool = False) -> dict:
        """§29 Remove an image."""
        return dc.image_rm(image, force=force)

    @tool(mcp)
    async def docker_network_ls() -> list:
        """§29 List networks."""
        return dc.network_ls()

    @tool(mcp)
    async def docker_volume_ls() -> list:
        """§29 List volumes."""
        return dc.volume_ls()

    @tool(mcp)
    async def docker_prune() -> dict:
        """§29 Prune unused docker resources."""
        return dc.prune()

    @tool(mcp)
    async def docker_run(image: str, command: str | None = None,
                          name: str | None = None, env: dict | None = None,
                          volumes: dict | None = None) -> dict:
        """§29 Run a new container (detached)."""
        kwargs: dict = {}
        if name: kwargs["name"] = name
        if env: kwargs["environment"] = env
        if volumes: kwargs["volumes"] = volumes
        return dc.docker_run(image, command=command, **kwargs)

    return 14
