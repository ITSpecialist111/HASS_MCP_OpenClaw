"""§26 Recorder DB direct access."""
from __future__ import annotations

from .. import sql as _sql
from ..ws_client import get_ws
from ._helpers import tool


def register(mcp) -> int:

    @tool(mcp)
    async def sql_query(sql: str, params: dict | None = None, limit: int = 1000) -> dict:
        """§26 SELECT against the recorder DB."""
        return _sql.query(sql, params=params, limit=limit)

    @tool(mcp)
    async def sql_exec(sql: str, params: dict | None = None) -> dict:
        """§26 INSERT/UPDATE/DELETE/DDL against the recorder DB."""
        return _sql.execute(sql, params=params)

    @tool(mcp)
    async def sql_schema() -> dict:
        """§26 List tables and columns in the recorder DB."""
        return _sql.schema()

    @tool(mcp)
    async def db_repack() -> dict:
        """§26 VACUUM the SQLite recorder DB."""
        return _sql.vacuum()

    @tool(mcp)
    async def db_size_breakdown(top_n: int = 30) -> dict:
        """§26 Top entities by row count in the states table."""
        rows = _sql.query(
            "SELECT entity_id, COUNT(*) as n FROM states_meta sm "
            "JOIN states s ON s.metadata_id = sm.metadata_id "
            "GROUP BY entity_id ORDER BY n DESC LIMIT :lim",
            {"lim": top_n})
        return {"size": _sql.db_size(), "top_entities": rows.get("rows", [])}

    @tool(mcp)
    async def recorder_purge_orphans() -> dict:
        """§26 Find entity_ids in states_meta not in entity_registry; delete them."""
        # Get registry entity_ids
        entries = await get_ws().call("config/entity_registry/list")
        registered = {e["entity_id"] for e in entries}
        meta = _sql.query("SELECT metadata_id, entity_id FROM states_meta", limit=100000)
        orphan_ids = [r["entity_id"] for r in meta["rows"]
                       if r["entity_id"] not in registered]
        deleted = 0
        for eid in orphan_ids:
            _sql.execute("DELETE FROM states WHERE metadata_id IN "
                         "(SELECT metadata_id FROM states_meta WHERE entity_id=:e)",
                         {"e": eid})
            _sql.execute("DELETE FROM states_meta WHERE entity_id=:e", {"e": eid})
            deleted += 1
        return {"orphans_removed": deleted, "entity_ids": orphan_ids}

    return 6
