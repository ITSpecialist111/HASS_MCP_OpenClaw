"""§56 Observability & forensics (pcap, DNS tap, CV inference, vector memory, anomaly)."""
from __future__ import annotations

import json
import math
import os
import sqlite3
import time
from typing import Any

from .. import hass
from .. import shell as _shell
from ._helpers import tool

_VEC_DB = "/data/vector_memory.sqlite"


def _vec_init() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_VEC_DB), exist_ok=True)
    c = sqlite3.connect(_VEC_DB)
    c.execute("""CREATE TABLE IF NOT EXISTS memories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL NOT NULL,
        kind TEXT NOT NULL,
        text TEXT NOT NULL,
        meta TEXT,
        embedding BLOB
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_kind ON memories(kind)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ts ON memories(ts)")
    c.commit()
    return c


def _hash_embed(text: str, dim: int = 256) -> bytes:
    """Cheap deterministic hashing-trick embedding (no model dep)."""
    import hashlib, struct
    vec = [0.0] * dim
    for token in text.lower().split():
        h = int.from_bytes(hashlib.md5(token.encode()).digest()[:8], "little")
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    vec = [v / norm for v in vec]
    return struct.pack(f"{dim}f", *vec)


def _cosine(a: bytes, b: bytes, dim: int = 256) -> float:
    import struct
    av = struct.unpack(f"{dim}f", a); bv = struct.unpack(f"{dim}f", b)
    return sum(x * y for x, y in zip(av, bv))


def register(mcp) -> int:

    @tool(mcp)
    async def packet_capture(interface: str = "eth0", duration: int = 30,
                                filter_expr: str = "",
                                output_path: str = "/share/capture.pcap") -> Any:
        """§56 tcpdump capture for N seconds → pcap file."""
        cmd = (f"timeout {duration} tcpdump -i {interface} "
                f"-w {output_path} {filter_expr}")
        r = await _shell.shell_exec(cmd, timeout=duration + 30)
        size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        return {**r, "output_path": output_path, "bytes": size}

    @tool(mcp)
    async def packet_capture_summary(pcap_path: str, count: int = 100) -> Any:
        """§56 tshark summary of a pcap."""
        return await _shell.shell_exec(
            f"tshark -r {pcap_path} -c {count}", timeout=60.0)

    @tool(mcp)
    async def dns_log_tap(adguard_url: str, username: str, password: str,
                            limit: int = 200) -> Any:
        """§56 Pull recent DNS queries from AdGuard Home."""
        import httpx
        async with httpx.AsyncClient(timeout=30.0, verify=False) as c:
            r = await c.get(f"{adguard_url}/control/querylog",
                             params={"limit": limit},
                             auth=(username, password))
            try: return r.json()
            except Exception: return r.text

    @tool(mcp)
    async def flow_logs_pull(collector_url: str, limit: int = 100) -> Any:
        """§56 Pull NetFlow/sFlow records from a generic collector REST endpoint."""
        import httpx
        async with httpx.AsyncClient(timeout=30.0, verify=False) as c:
            r = await c.get(collector_url, params={"limit": limit})
            try: return r.json()
            except Exception: return r.text

    @tool(mcp)
    async def camera_inference(camera_entity: str, prompt: str = "describe the scene",
                                  vision_agent_id: str | None = None) -> Any:
        """§56 Snapshot a camera and run a vision LLM agent over it."""
        from ..ws_client import get_ws
        img = await hass.get_camera_image(camera_entity)
        import base64
        b64 = base64.b64encode(img).decode()
        # Hand off to a configured vision agent via conversation/process
        kwargs = {"text": prompt + f"\n[image_b64:{b64[:64]}...]"}
        if vision_agent_id: kwargs["agent_id"] = vision_agent_id
        return await get_ws().call("conversation/process", **kwargs)

    @tool(mcp)
    async def memory_remember(text: str, kind: str = "note",
                                meta: dict | None = None) -> dict:
        """§56 Store a memory with hashing-trick embedding."""
        c = _vec_init()
        c.execute("INSERT INTO memories(ts, kind, text, meta, embedding) "
                   "VALUES(?, ?, ?, ?, ?)",
                   (time.time(), kind, text,
                    json.dumps(meta or {}), _hash_embed(text)))
        c.commit()
        rid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        c.close()
        return {"id": rid, "kind": kind}

    @tool(mcp)
    async def memory_recall(query: str, kind: str | None = None,
                              limit: int = 10) -> list:
        """§56 Cosine-similarity recall across memories."""
        c = _vec_init()
        q_emb = _hash_embed(query)
        sql = "SELECT id, ts, kind, text, meta, embedding FROM memories"
        params: tuple = ()
        if kind: sql += " WHERE kind=?"; params = (kind,)
        rows = c.execute(sql, params).fetchall()
        scored = [(_cosine(q_emb, r[5]), r) for r in rows]
        scored.sort(key=lambda x: x[0], reverse=True)
        c.close()
        return [{"id": r[0], "ts": r[1], "kind": r[2],
                  "text": r[3], "meta": json.loads(r[4] or "{}"),
                  "score": round(s, 4)} for s, r in scored[:limit]]

    @tool(mcp)
    async def memory_forget(memory_id: int) -> dict:
        """§56 Delete a memory."""
        c = _vec_init()
        c.execute("DELETE FROM memories WHERE id=?", (memory_id,))
        c.commit(); c.close()
        return {"deleted": memory_id}

    @tool(mcp)
    async def memory_stats() -> dict:
        """§56 Count + size of memory store."""
        c = _vec_init()
        n = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        c.close()
        size = os.path.getsize(_VEC_DB) if os.path.exists(_VEC_DB) else 0
        return {"count": n, "db_bytes": size}

    @tool(mcp)
    async def behaviour_anomaly(entity_id: str, lookback_days: int = 14,
                                   z_threshold: float = 3.0) -> dict:
        """§56 Naive z-score anomaly on numeric history."""
        from .. import sql as _sql
        rows = _sql.query(
            "SELECT s.last_updated_ts AS ts, s.state AS v "
            "FROM states s JOIN states_meta sm ON s.metadata_id=sm.metadata_id "
            f"WHERE sm.entity_id={entity_id!r} AND s.last_updated_ts > "
            f"strftime('%s','now')-{lookback_days*86400} "
            "ORDER BY s.last_updated_ts DESC LIMIT 5000")["rows"]
        vals = []
        for r in rows:
            try: vals.append(float(r["v"]))
            except Exception: pass
        if len(vals) < 10:
            return {"error": "insufficient numeric history"}
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        std = math.sqrt(var) or 1.0
        latest = vals[0]
        z = (latest - mean) / std
        return {"latest": latest, "mean": mean, "std": std,
                 "z_score": z, "anomaly": abs(z) >= z_threshold}

    @tool(mcp)
    async def presence_fusion() -> dict:
        """§56 Aggregate person/device_tracker entities into a per-person view."""
        states = await hass.get_all_states()
        persons: dict[str, dict] = {}
        for s in states:
            if s["entity_id"].startswith("person."):
                persons[s["entity_id"]] = {"state": s.get("state"),
                                             "trackers": []}
        for s in states:
            eid = s["entity_id"]
            if not eid.startswith("device_tracker."):
                continue
            owner = s.get("attributes", {}).get("user_id")
            for p, info in persons.items():
                a = (await hass.get_entity_state(p)).get("attributes", {})
                if owner and owner == a.get("user_id"):
                    info["trackers"].append({"id": eid,
                                                "state": s.get("state"),
                                                "lat": s.get("attributes", {}).get("latitude"),
                                                "lon": s.get("attributes", {}).get("longitude")})
        return persons

    return 11
