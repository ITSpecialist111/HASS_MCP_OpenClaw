"""§36 Telemetry / observability."""
from __future__ import annotations

from typing import Any

import httpx

from .. import shell as _shell
from ._helpers import tool


def register(mcp) -> int:

    @tool(mcp)
    async def prometheus_metrics_dump(url: str = "http://homeassistant.local:8123/api/prometheus") -> str:
        """§36 Pull Prometheus metrics (REST exporter)."""
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r.text

    @tool(mcp)
    async def influxdb_query(query: str, url: str, db: str | None = None,
                              token: str | None = None,
                              org: str | None = None) -> Any:
        """§36 Influx query (auto-detect v1 vs v2 by token presence)."""
        async with httpx.AsyncClient(timeout=60.0) as c:
            if token:  # v2
                headers = {"Authorization": f"Token {token}",
                            "Content-Type": "application/vnd.flux"}
                r = await c.post(f"{url}/api/v2/query",
                                  params={"org": org or ""},
                                  headers=headers, content=query)
            else:  # v1
                r = await c.get(f"{url}/query",
                                 params={"db": db or "", "q": query})
            r.raise_for_status()
            try: return r.json()
            except Exception: return r.text

    @tool(mcp)
    async def influxdb_write(line_protocol: str, url: str, db: str | None = None,
                              token: str | None = None, org: str | None = None,
                              bucket: str | None = None) -> dict:
        """§36 Write Influx line-protocol."""
        async with httpx.AsyncClient(timeout=30.0) as c:
            if token:
                r = await c.post(f"{url}/api/v2/write",
                                  params={"org": org, "bucket": bucket},
                                  headers={"Authorization": f"Token {token}"},
                                  content=line_protocol)
            else:
                r = await c.post(f"{url}/write", params={"db": db},
                                  content=line_protocol)
            r.raise_for_status()
            return {"status_code": r.status_code}

    @tool(mcp)
    async def grafana_create_dashboard(grafana_url: str, api_token: str,
                                         dashboard_json: dict) -> Any:
        """§36 Create or update a Grafana dashboard."""
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.post(f"{grafana_url}/api/dashboards/db",
                              headers={"Authorization": f"Bearer {api_token}"},
                              json={"dashboard": dashboard_json, "overwrite": True})
            r.raise_for_status()
            return r.json()

    @tool(mcp)
    async def grafana_render_panel_png(grafana_url: str, api_token: str,
                                        dashboard_uid: str, panel_id: int,
                                        from_: str = "now-6h", to: str = "now",
                                        width: int = 1000, height: int = 500) -> dict:
        """§36 Render a Grafana panel as PNG (returns base64)."""
        import base64
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.get(f"{grafana_url}/render/d-solo/{dashboard_uid}/panel",
                             params={"panelId": panel_id, "from": from_, "to": to,
                                      "width": width, "height": height},
                             headers={"Authorization": f"Bearer {api_token}"})
            r.raise_for_status()
            return {"mime": "image/png", "base64": base64.b64encode(r.content).decode()}

    return 5
