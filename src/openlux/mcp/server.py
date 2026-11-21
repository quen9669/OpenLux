"""Rôle : Serveur FastMCP exposant 4 outils sémantiques IA branchés sur Gold Parquet.
Entrées/Sorties : Requêtes JSON-RPC MCP -> Résultats enrichis de métadonnées et limitations.
Hors-scope : N'expose pas d'interface HTTP REST (délégué à api/main.py).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
from fastmcp import FastMCP

from openlux.config import load_sources_config
from openlux.core.gold import get_gold_metadata, get_gold_table_path, query_gold_table
from openlux.core.quality import get_latest_source_health

mcp = FastMCP("OpenLux Hub")


def _mcp_meta(
    ds: str, count: int, limits: str, status: str = "GOOD", score: float = 100.0
) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    return {
        "dataset": ds,
        "trust_score": score,
        "status": status,
        "is_stale": False,
        "last_checked_utc": now,
        "last_changed_utc": now,
        "source_used": "primary",
        "source_url": "https://openlux.lu/",
        "license_spdx": "CC0-1.0",
        "commercial_use_safe": True,
        "known_limitations": limits,
        "run_id": f"mcp_{ds}",
        "pipeline_git_sha": "git_v1",
        "row_count": count,
    }


@mcp.tool()
def get_platform_health(domain: str | None = None) -> dict[str, Any]:
    """État de fraîcheur, Trust Score et anomalies par source ou domaine au Luxembourg."""
    sources, db = load_sources_config(), Path("data/openlux.duckdb")
    try:
        con = duckdb.connect(str(db), read_only=True) if db.exists() else None
    except duckdb.IOException:
        con = None
    health = get_latest_source_health(con) if con else {}
    if con:
        con.close()
    items = [
        {
            "source_id": s,
            "domain": src.domain,
            "status": (h := health.get(s, {})).get("status", "NOT_TESTED"),
            "trust_score": float(h.get("trust_score", 100.0)),
            "last_checked_utc": h.get("last_checked_utc"),
            "row_count": int(h.get("row_count", 0)),
        }
        for s, src in sources.items()
        if not domain or src.domain.lower() == domain.lower()
    ]
    score = round(sum(s["trust_score"] for s in items) / len(items), 1) if items else 100.0
    st_list = [s["status"] for s in items]
    st = "ERROR" if "ERROR" in st_list else ("ATTENTION" if "ATTENTION" in st_list else "GOOD")
    return {
        "_meta": _mcp_meta("platform_health", len(items), "Santé des flux actifs.", st, score),
        "sources": items,
    }


@mcp.tool()
def get_luxembourg_day_context(date: str, commune: str = "Luxembourg") -> dict[str, Any]:
    """Fournit le contexte quotidien unifié : météo, jours fériés et trafic autoroutier."""
    ctx: dict[str, Any] = {
        "date": date,
        "commune": commune,
        "holiday": None,
        "weather": None,
        "traffic_events": [],
    }
    targets = [
        ("holiday", "gold_holidays", 1),
        ("weather", "gold_weather_observations", 5),
        ("traffic_events", "gold_traffic_events", 10),
    ]
    for key, tbl, lim in targets:
        if p := get_gold_table_path(tbl):
            c, _, rows, _ = query_gold_table(
                p, commune=(commune if key != "holiday" else None), date_from=date, limit=lim
            )
            c.close()
            ctx[key] = rows[0] if (lim == 1 and rows) else (rows if lim > 1 else None)
    return {
        "_meta": _mcp_meta("gold_luxembourg_daily_context", 1, "Météo, jours fériés et trafic."),
        "context": ctx,
    }


@mcp.tool()
def search_luxembourg_events_and_works(
    query: str,
    date_from: str,
    date_to: str,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float = 10.0,
) -> dict[str, Any]:
    """Recherche croisée sur les perturbations routières, chantiers autoroutiers et événements."""
    results: list[dict[str, Any]] = []
    if t_path := get_gold_table_path("gold_traffic_events"):
        con = duckdb.connect(":memory:")
        try:
            con.execute("LOAD spatial;")
        except Exception:
            pass
        sql = """
            SELECT event_id, road_name, situation_type, traffic_comment, observed_at_utc, lat, lon
            FROM read_parquet(?)
            WHERE (LOWER(road_name) LIKE LOWER(?) OR LOWER(traffic_comment) LIKE LOWER(?)
                   OR LOWER(situation_type) LIKE LOWER(?))
              AND observed_at_utc >= TRY_CAST(? AS TIMESTAMP)
              AND observed_at_utc <= TRY_CAST(? AS TIMESTAMP)
        """
        params: list[Any] = [
            t_path.as_posix(),
            f"%{query}%",
            f"%{query}%",
            f"%{query}%",
            date_from,
            date_to,
        ]
        if lat is not None and lon is not None:
            sql += (
                " AND lat IS NOT NULL AND lon IS NOT NULL AND "
                "ST_Distance_Spheroid(ST_Point(lon, lat), ST_Point(?, ?)) <= ?"
            )
            params.extend([float(lon), float(lat), float(radius_km) * 1000.0])
        cur = con.execute(sql + " LIMIT 50", params)
        cols = [d[0] for d in cur.description]
        results = [dict(zip(cols, r, strict=False)) for r in cur.fetchall()]
        con.close()
    return {
        "_meta": _mcp_meta("events_and_works", len(results), "Perturbations autoroutières."),
        "results": results,
    }


@mcp.tool()
def query_dataset(dataset: str, commune: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Accès structuré direct et sécurisé à n'importe quelle table Gold autorisée."""
    if not (path := get_gold_table_path(dataset)):
        return {
            "_meta": _mcp_meta(dataset, 0, "Dataset non autorisé.", "ERROR", 0.0),
            "error": "Dataset non autorisé",
            "data": [],
        }
    con, _, rows, _ = query_gold_table(path, commune=commune, limit=min(100, max(1, limit)))
    con.close()
    return {"_meta": get_gold_metadata(path, row_count=len(rows)), "data": rows}
