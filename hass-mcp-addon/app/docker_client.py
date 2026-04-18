"""Docker socket client for advanced ops."""
from __future__ import annotations

from typing import Any

try:
    import docker as _docker
    _client_err: str | None = None
except Exception as e:  # pragma: no cover
    _docker = None
    _client_err = str(e)


def _client():
    if _docker is None:
        raise RuntimeError(f"docker SDK unavailable: {_client_err}")
    return _docker.from_env()


def ps(all_: bool = True) -> list[dict[str, Any]]:
    c = _client()
    return [{"id": x.short_id, "name": x.name, "image": x.image.tags,
             "status": x.status} for x in c.containers.list(all=all_)]


def logs(name: str, tail: int = 200) -> str:
    return _client().containers.get(name).logs(tail=tail).decode("utf-8", errors="replace")


def stats(name: str) -> dict[str, Any]:
    return _client().containers.get(name).stats(stream=False)


def inspect(name: str) -> dict[str, Any]:
    return _client().containers.get(name).attrs


def exec_(name: str, cmd: str) -> dict[str, Any]:
    res = _client().containers.get(name).exec_run(cmd)
    return {"rc": res.exit_code, "output": res.output.decode("utf-8", errors="replace")}


def restart(name: str) -> dict[str, Any]:
    _client().containers.get(name).restart()
    return {"ok": True}


def kill(name: str) -> dict[str, Any]:
    _client().containers.get(name).kill()
    return {"ok": True}


def pull(image: str) -> dict[str, Any]:
    img = _client().images.pull(image)
    return {"id": img.short_id, "tags": img.tags}


def image_ls() -> list[dict[str, Any]]:
    return [{"id": i.short_id, "tags": i.tags} for i in _client().images.list()]


def image_rm(image: str, force: bool = False) -> dict[str, Any]:
    _client().images.remove(image, force=force)
    return {"ok": True}


def network_ls() -> list[dict[str, Any]]:
    return [{"id": n.short_id, "name": n.name} for n in _client().networks.list()]


def volume_ls() -> list[dict[str, Any]]:
    return [{"name": v.name} for v in _client().volumes.list()]


def prune() -> dict[str, Any]:
    c = _client()
    return {
        "containers": c.containers.prune(),
        "images": c.images.prune(),
        "volumes": c.volumes.prune(),
        "networks": c.networks.prune(),
    }


def docker_run(image: str, command: str | None = None, **kwargs) -> dict[str, Any]:
    c = _client()
    out = c.containers.run(image, command=command, detach=True, **kwargs)
    return {"id": out.short_id, "name": out.name}
