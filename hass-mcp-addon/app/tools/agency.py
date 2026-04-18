"""§59 Coordination / Agency (scheduler, goals, multi-agent, federation)."""
from __future__ import annotations

import asyncio
import itertools
import json
import os
import time
import uuid
from typing import Any

import httpx

from ..ws_client import get_ws
from ._helpers import tool

_TASKS: dict[str, dict] = {}      # cron-like scheduled tasks
_GOALS: dict[str, dict] = {}      # persistent objectives
_AGENTS: dict[str, dict] = {}     # spawned sub-agents
_PROXIES: dict[str, dict] = {}    # external MCP servers proxied through this one
_PEERS: dict[str, dict] = {}      # federated HA peers

_PERSIST_PATH = "/data/agency.json"
_ids = itertools.count(1)


def _persist() -> None:
    try:
        with open(_PERSIST_PATH, "w") as f:
            json.dump({"tasks": {k: {kk: vv for kk, vv in v.items()
                                       if kk != "_handle"}
                                  for k, v in _TASKS.items()},
                        "goals": _GOALS,
                        "agents": _AGENTS,
                        "proxies": _PROXIES,
                        "peers": _PEERS}, f)
    except Exception:
        pass


def _load() -> None:
    if not os.path.exists(_PERSIST_PATH): return
    try:
        with open(_PERSIST_PATH) as f: data = json.load(f)
        _TASKS.update(data.get("tasks", {}))
        _GOALS.update(data.get("goals", {}))
        _AGENTS.update(data.get("agents", {}))
        _PROXIES.update(data.get("proxies", {}))
        _PEERS.update(data.get("peers", {}))
    except Exception:
        pass


_load()


async def _execute_action(action: dict) -> Any:
    """Action dict: {kind: 'service'|'ws'|'http', ...}."""
    kind = action.get("kind", "service")
    if kind == "service":
        return await get_ws().call("call_service", **action.get("payload", {}))
    if kind == "ws":
        cmd = action["command"]; payload = action.get("payload", {})
        return await get_ws().call(cmd, **payload)
    if kind == "http":
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.request(action.get("method", "GET"), action["url"],
                                 headers=action.get("headers"),
                                 json=action.get("json"))
            try: return r.json()
            except Exception: return r.text
    return {"error": f"unknown action kind {kind}"}


async def _scheduler_loop(task_id: str) -> None:
    while task_id in _TASKS:
        t = _TASKS[task_id]
        try:
            res = await _execute_action(t["action"])
            t["last_run"] = time.time(); t["last_result"] = str(res)[:500]
        except Exception as e:
            t["last_error"] = str(e)
        _persist()
        await asyncio.sleep(t.get("interval_seconds", 60))


async def _goal_loop(goal_id: str) -> None:
    while goal_id in _GOALS:
        g = _GOALS[goal_id]
        try:
            for step in g.get("steps", []):
                res = await _execute_action(step)
                g.setdefault("history", []).append(
                    {"ts": time.time(), "step": step, "result": str(res)[:200]})
                if len(g["history"]) > 200:
                    g["history"] = g["history"][-200:]
        except Exception as e:
            g["last_error"] = str(e)
        _persist()
        await asyncio.sleep(g.get("interval_seconds", 300))


def register(mcp) -> int:
    ws = get_ws

    # ---- Task scheduler ----
    @tool(mcp)
    async def schedule_task(name: str, action: dict, interval_seconds: int = 60) -> dict:
        """§59 Schedule a recurring action (kind=service|ws|http)."""
        task_id = f"t{next(_ids)}_{name}"
        _TASKS[task_id] = {"name": name, "action": action,
                             "interval_seconds": interval_seconds,
                             "created": time.time()}
        loop = asyncio.get_event_loop()
        _TASKS[task_id]["_handle"] = loop.create_task(_scheduler_loop(task_id))
        _persist()
        return {"task_id": task_id}

    @tool(mcp)
    async def list_scheduled_tasks() -> list:
        """§59 List recurring tasks."""
        return [{"task_id": k, "name": v["name"],
                  "interval": v.get("interval_seconds"),
                  "last_run": v.get("last_run"),
                  "last_error": v.get("last_error")}
                 for k, v in _TASKS.items()]

    @tool(mcp)
    async def cancel_scheduled_task(task_id: str) -> dict:
        """§59 Cancel a scheduled task."""
        t = _TASKS.pop(task_id, None)
        if not t: return {"error": "not found"}
        h = t.get("_handle")
        if h: h.cancel()
        _persist()
        return {"cancelled": task_id}

    # ---- Goal loop ----
    @tool(mcp)
    async def set_goal(name: str, description: str, steps: list,
                         interval_seconds: int = 300) -> dict:
        """§59 Persistent objective with periodic step execution."""
        goal_id = f"g{next(_ids)}_{name}"
        _GOALS[goal_id] = {"name": name, "description": description,
                             "steps": steps,
                             "interval_seconds": interval_seconds,
                             "created": time.time()}
        loop = asyncio.get_event_loop()
        loop.create_task(_goal_loop(goal_id))
        _persist()
        return {"goal_id": goal_id}

    @tool(mcp)
    async def list_goals() -> list:
        """§59 List active goals."""
        return [{"goal_id": k, "name": v["name"],
                  "description": v["description"],
                  "history_len": len(v.get("history", []))}
                 for k, v in _GOALS.items()]

    @tool(mcp)
    async def goal_history(goal_id: str, limit: int = 50) -> list:
        """§59 Recent step results for a goal."""
        g = _GOALS.get(goal_id)
        if not g: return []
        return g.get("history", [])[-limit:]

    @tool(mcp)
    async def cancel_goal(goal_id: str) -> dict:
        """§59 Stop a goal loop."""
        g = _GOALS.pop(goal_id, None)
        _persist()
        return {"cancelled": goal_id, "ok": g is not None}

    # ---- Multi-agent dispatch ----
    @tool(mcp)
    async def spawn_subagent(name: str, role: str, agent_id: str,
                                initial_prompt: str) -> dict:
        """§59 Register a sub-agent reference (delegates via conversation/process)."""
        sid = str(uuid.uuid4())
        _AGENTS[sid] = {"name": name, "role": role,
                          "agent_id": agent_id,
                          "initial_prompt": initial_prompt,
                          "messages": [],
                          "created": time.time()}
        _persist()
        return {"subagent_id": sid}

    @tool(mcp)
    async def dispatch_to_subagent(subagent_id: str, message: str) -> Any:
        """§59 Send a message to a sub-agent and capture the reply."""
        a = _AGENTS.get(subagent_id)
        if not a: return {"error": "unknown subagent"}
        res = await ws().call("conversation/process",
                                text=message,
                                agent_id=a["agent_id"])
        a["messages"].append({"ts": time.time(),
                                "in": message,
                                "out": str(res)[:1000]})
        _persist()
        return res

    @tool(mcp)
    async def list_subagents() -> list:
        """§59 List spawned sub-agents."""
        return [{"id": k, "name": v["name"], "role": v["role"],
                  "messages": len(v["messages"])}
                 for k, v in _AGENTS.items()]

    # ---- Human-in-loop optional ----
    @tool(mcp)
    async def request_human_approval(notify_service: str, message: str,
                                       timeout_seconds: int = 600,
                                       auto_approve_on_timeout: bool = True) -> dict:
        """§59 Push a confirmation prompt + wait. Resolves on response or timeout."""
        token = uuid.uuid4().hex[:8]
        await ws().call("call_service", domain="notify", service=notify_service,
                         service_data={"message": f"{message}\n[approval token: {token}]"})
        # Listen for input_text.approval = token, or timeout
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            try:
                from .. import hass
                s = await hass.get_entity_state("input_text.approval")
                if s and s.get("state") == token:
                    return {"approved": True, "token": token, "method": "human"}
            except Exception:
                pass
            await asyncio.sleep(2)
        return {"approved": auto_approve_on_timeout, "token": token,
                 "method": "timeout"}

    # ---- External MCP marketplace ----
    @tool(mcp)
    async def register_external_mcp(name: str, base_url: str,
                                       api_key: str | None = None) -> dict:
        """§59 Register another MCP server we will proxy tool calls to."""
        _PROXIES[name] = {"base_url": base_url, "api_key": api_key,
                           "added": time.time()}
        _persist()
        return {"name": name, "registered": True}

    @tool(mcp)
    async def proxy_external_mcp_call(name: str, method: str = "POST",
                                         path: str = "/mcp",
                                         json_body: dict | None = None) -> Any:
        """§59 Proxy a call to a registered external MCP server."""
        p = _PROXIES.get(name)
        if not p: return {"error": "unknown proxy"}
        async with httpx.AsyncClient(timeout=120.0) as c:
            h = {}
            if p.get("api_key"):
                h["Authorization"] = f"Bearer {p['api_key']}"
            r = await c.request(method, f"{p['base_url'].rstrip('/')}{path}",
                                 headers=h, json=json_body)
            try: return r.json()
            except Exception: return r.text

    @tool(mcp)
    async def list_external_mcp() -> list:
        """§59 List registered external MCP proxies."""
        return [{"name": k, "base_url": v["base_url"]}
                 for k, v in _PROXIES.items()]

    # ---- Inter-home federation ----
    @tool(mcp)
    async def register_peer_home(name: str, ha_url: str, token: str,
                                    mcp_url: str | None = None) -> dict:
        """§59 Register another household's HA + MCP for federated calls."""
        _PEERS[name] = {"ha_url": ha_url, "token": token,
                          "mcp_url": mcp_url, "added": time.time()}
        _persist()
        return {"name": name, "registered": True}

    @tool(mcp)
    async def peer_call_service(peer: str, domain: str, service: str,
                                  service_data: dict | None = None) -> Any:
        """§59 Call a service on a federated peer's HA."""
        p = _PEERS.get(peer)
        if not p: return {"error": "unknown peer"}
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.post(f"{p['ha_url']}/api/services/{domain}/{service}",
                              headers={"Authorization": f"Bearer {p['token']}"},
                              json=service_data or {})
            try: return r.json()
            except Exception: return r.text

    @tool(mcp)
    async def peer_get_state(peer: str, entity_id: str) -> Any:
        """§59 Read an entity state on a federated peer."""
        p = _PEERS.get(peer)
        if not p: return {"error": "unknown peer"}
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.get(f"{p['ha_url']}/api/states/{entity_id}",
                             headers={"Authorization": f"Bearer {p['token']}"})
            try: return r.json()
            except Exception: return r.text

    @tool(mcp)
    async def list_peers() -> list:
        """§59 List federated peers."""
        return [{"name": k, "ha_url": v["ha_url"]} for k, v in _PEERS.items()]

    return 17
