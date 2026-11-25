"""Rôle : Lecture sécurisée de la couche Gold (métadonnées mesurées, requêtes, streaming).
Entrées/Sorties : Lit data/gold/*.parquet et l'état obs_runs ; renvoie lignes, CSV ou GeoJSON.
Hors-scope : N'écrit rien ; toute entrée utilisateur passe par des paramètres liés '?'.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb

from openlux.config import load_sources_config
from openlux.core.quality import get_latest_source_health

HAVERSINE_KM = (
    "12742 * ASIN(SQRT(POWER(SIN(RADIANS(lat - ?) / 2), 2) + "
    "COS(RADIANS(?)) * COS(RADIANS(lat)) * POWER(SIN(RADIANS(lon - ?) / 2), 2)))"
)


def _source_meta(sid: str, h: dict[str, Any], src: Any) -> dict[str, Any]:
    return {
        "source_id": sid,
        "status": h.get("status", "NOT_TESTED"),
        "trust_score": float(h.get("trust_score", 0.0)),
        "last_checked_utc": h.get("last_checked_utc"),
        "last_changed_utc": h.get("last_changed_utc"),
        "source_url": src.primary.url.split("?")[0] if src else None,
        "license_spdx": src.license_spdx if src else None,
        "data_origin": src.data_origin if src else None,
        "known_limitations": src.known_limitations if src else None,
    }


def get_gold_metadata(
    parquet_path: Path, row_count: int, duckdb_path: Path | str = "data/openlux.duckdb"
) -> dict[str, Any]:
    """Métadonnées mesurées : sources réelles de la table et leur dernier état de collecte."""
    with duckdb.connect(":memory:") as con:
        try:
            q = "SELECT DISTINCT source_id FROM read_parquet(?) ORDER BY 1"
            sids = [r[0] for r in con.execute(q, [parquet_path.as_posix()]).fetchall() if r[0]]
        except duckdb.Error:
            sids = []
    cfg, health = load_sources_config(), {}
    if Path(duckdb_path).exists():
        with (
            contextlib.suppress(duckdb.Error),
            duckdb.connect(str(duckdb_path), read_only=True) as c,
        ):
            health = get_latest_source_health(c)
    srcs = [_source_meta(sid, health.get(sid, {}), cfg.get(sid)) for sid in sids]
    order = ["ERROR", "NOT_TESTED", "ATTENTION", "UNCHANGED", "GOOD"]
    worst = min((s["status"] for s in srcs), key=order.index, default="NOT_TESTED")
    return {
        "dataset": parquet_path.stem,
        "status": worst,
        "trust_score": min((s["trust_score"] for s in srcs), default=0.0),
        "commercial_use_safe": all(cfg[s].commercial_use_safe for s in sids if s in cfg),
        "sources": srcs,
        "row_count": row_count,
    }


def query_gold_table(
    parquet_path: Path,
    commune: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
    limit: int | None = 100,
    offset: int = 0,
) -> tuple[duckdb.DuckDBPyConnection, list[str], list[dict[str, Any]], int]:
    con, p_s = duckdb.connect(":memory:"), parquet_path.as_posix()
    cols = [c[0] for c in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [p_s]).fetchall()]
    clauses, params = [], [p_s]
    if commune and (cc := [c for c in ("commune_lau", "commune_name", "canton") if c in cols]):
        clauses.append("(" + " OR ".join(f"LOWER({c}) LIKE LOWER(?)" for c in cc) + ")")
        params.extend([f"%{commune}%"] * len(cc))
    dates = ("observed_at_utc", "context_date", "holiday_date", "start_time_utc", "start_utc")
    dc = next((c for c in dates if c in cols), None)
    if dc:
        is_day = dc in ("context_date", "holiday_date")
        cst = "TRY_CAST(? AS DATE)" if is_day else "TRY_CAST(? AS TIMESTAMP)"
        for d, op in [(date_from, ">="), (date_to, "<=")]:
            if d:
                clauses.append(f"{dc} {op} {cst}")
                params.append(d)
    if None not in (lat, lon, radius_km) and "lat" in cols:
        # POURQUOI : haversine en SQL pur (pas d'extension spatial à télécharger hors ligne)
        clauses.append(f"lat IS NOT NULL AND lon IS NOT NULL AND {HAVERSINE_KM} <= ?")
        params.extend([float(lat), float(lat), float(lon), float(radius_km)])
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total = con.execute(f"SELECT count(*) FROM read_parquet(?){where}", params).fetchone()[0]
    p_lim = list(params) + ([max(1, limit), max(0, offset)] if limit is not None else [])
    s_lim = " LIMIT ? OFFSET ?" if limit is not None else ""
    cur = con.execute(f"SELECT * FROM read_parquet(?){where}{s_lim}", p_lim)
    out_cols = [d[0] for d in cur.description]
    return con, out_cols, [dict(zip(out_cols, r, strict=False)) for r in cur.fetchall()], total


def stream_gold_export(path: Path, is_geojson: bool):
    """Générateur de flux CSV ou GeoJSON depuis un fichier Parquet Gold."""

    def fmt(v: Any) -> Any:
        # POURQUOI : DECIMAL DuckDB et dates ne sont pas sérialisables tels quels en JSON
        return (
            v.isoformat()
            if hasattr(v, "isoformat")
            else (float(v) if isinstance(v, Decimal) else v)
        )

    with duckdb.connect(":memory:") as con:
        p = path.as_posix()
        cols = [c[0] for c in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [p]).fetchall()]
        cur = con.execute("SELECT * FROM read_parquet(?)", [p])
        if not is_geojson:
            yield ",".join(cols) + "\n"
            while chunk := cur.fetchmany(500):
                buf = io.StringIO()
                csv.writer(buf).writerows([[fmt(x) for x in r] for r in chunk])
                yield buf.getvalue()
            return
        la = cols.index("lat") if "lat" in cols else -1
        lo = cols.index("lon") if "lon" in cols else -1
        yield '{"type": "FeatureCollection", "features": [\n'
        sep = ""
        while chunk := cur.fetchmany(500):
            for r in chunk:
                valid = la >= 0 and lo >= 0 and r[la] is not None and r[lo] is not None
                g = {"type": "Point", "coordinates": [fmt(r[lo]), fmt(r[la])]} if valid else None
                props = {cols[i]: fmt(r[i]) for i in range(len(cols)) if i not in (la, lo)}
                yield f"{sep}{json.dumps({'type': 'Feature', 'geometry': g, 'properties': props})}"
                sep = ",\n"
        yield "\n]}"
