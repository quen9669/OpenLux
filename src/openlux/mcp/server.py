"""Rôle : Serveur FastMCP exposant 4 outils sémantiques IA branchés sur Gold Parquet.
Entrées/Sorties : Requêtes JSON-RPC MCP -> lignes Gold + métadonnées mesurées (sources, statut).
Hors-scope : N'expose pas d'interface HTTP REST (délégué à api/main.py) ; aucun score par défaut.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
from fastmcp import FastMCP

from openlux.config import load_sources_config
from openlux.core.gold import get_gold_table_path
from openlux.core.gold_query import HAVERSINE_KM, get_gold_metadata, query_gold_table
from openlux.core.quality import get_latest_source_health

mcp = FastMCP("OpenLux Hub")


def _rows(dataset: str, **kw: Any) -> list[dict[str, Any]]:
    if not (p := get_gold_table_path(dataset)):
        return []
    con, _, rows, _ = query_gold_table(p, **kw)
    con.close()
    return rows


@mcp.tool()
def get_platform_health(domain: str | None = None) -> dict[str, Any]:
    """État de fraîcheur, Trust Score et anomalies par source ou domaine au Luxembourg."""
    sources, health = load_sources_config(), {}
    if Path("data/openlux.duckdb").exists():
        try:
            with duckdb.connect("data/openlux.duckdb", read_only=True) as con:
                health = get_latest_source_health(con)
        except duckdb.Error:
            health = {}
    items = [
        {
            "source_id": s,
            "domain": src.domain,
            "data_origin": src.data_origin,
            "status": (h := health.get(s, {})).get("status", "NOT_TESTED"),
            "trust_score": float(h.get("trust_score", 0.0)),
            "last_checked_utc": h.get("last_checked_utc"),
            "row_count": int(h.get("row_count", 0)),
        }
        for s, src in sources.items()
        if not domain or src.domain.lower() == domain.lower()
    ]
    return {"_meta": {"dataset": "platform_health", "row_count": len(items)}, "sources": items}


@mcp.tool()
def get_luxembourg_day_context(date: str, canton: str = "Luxembourg") -> dict[str, Any]:
    """Contexte d'un jour pour un canton : météo, qualité de l'air, fériés, trafic, chantiers."""
    rows = _rows(
        "gold_luxembourg_daily_context", commune=canton, date_from=date, date_to=date, limit=1
    )
    p = get_gold_table_path("gold_luxembourg_daily_context")
    meta = get_gold_metadata(p, len(rows)) if p else {"dataset": "gold_luxembourg_daily_context"}
    return {"_meta": meta, "context": rows[0] if rows else None, "date": date, "canton": canton}


@mcp.tool()
def search_luxembourg_events_and_works(
    query: str,
    date_from: str,
    date_to: str,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float = 10.0,
) -> dict[str, Any]:
    """Recherche textuelle et géographique dans les événements trafic et les chantiers routiers."""
    results: list[dict[str, Any]] = []
    for ds, txt in (("gold_traffic_events", "description"), ("gold_roadworks", "title")):
        if not (p := get_gold_table_path(ds)):
            continue
        sql = (
            f"SELECT '{ds}' AS dataset, source_id, road_name, {txt} AS text, start_time_utc, "
            "end_time_utc, lat, lon, commune_name, canton FROM read_parquet(?) "
            f"WHERE (LOWER(COALESCE(road_name, '')) LIKE LOWER(?) OR LOWER(COALESCE({txt}, '')) "
            "LIKE LOWER(?)) AND COALESCE(start_time_utc, TIMESTAMP '1900-01-01') <= "
            "TRY_CAST(? AS TIMESTAMP) AND COALESCE(end_time_utc, TIMESTAMP '2999-01-01') >= "
            "TRY_CAST(? AS TIMESTAMP)"
        )
        params: list[Any] = [p.as_posix(), f"%{query}%", f"%{query}%", date_to, date_from]
        if lat is not None and lon is not None:
            sql += f" AND lat IS NOT NULL AND {HAVERSINE_KM} <= ?"
            params += [float(lat), float(lat), float(lon), float(radius_km)]
        with duckdb.connect(":memory:") as con:
            cur = con.execute(sql + " LIMIT 50", params)
            cols = [d[0] for d in cur.description]
            results += [dict(zip(cols, r, strict=False)) for r in cur.fetchall()]
    return {"_meta": {"dataset": "events_and_works", "row_count": len(results)}, "results": results}


@mcp.tool()
def query_dataset(dataset: str, commune: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Accès structuré direct et sécurisé à n'importe quelle table Gold autorisée."""
    if not (path := get_gold_table_path(dataset)):
        return {
            "_meta": {"dataset": dataset, "status": "ERROR"},
            "error": "Dataset non autorisé",
            "data": [],
        }
    con, _, rows, _ = query_gold_table(path, commune=commune, limit=min(100, max(1, limit)))
    con.close()
    return {"_meta": get_gold_metadata(path, row_count=len(rows)), "data": rows}
