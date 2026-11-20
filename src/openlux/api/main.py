"""Rôle : API REST FastAPI exposant les Data Marts Gold en lecture seule.
Entrées/Sorties : Requêtes HTTP GET -> JSON standardisé (_meta), streaming CSV/GeoJSON, Parquet.
Hors-scope : N'effectue aucune écriture en base ni modification de données.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from openlux.config import load_sources_config
from openlux.core.gold import (
    get_gold_metadata,
    get_gold_table_path,
    list_gold_datasets,
    query_gold_table,
)
from openlux.core.quality import get_latest_source_health

app = FastAPI(
    title="OpenLux Hub API",
    description="API REST unifiée pour les données ouvertes du Luxembourg.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/v1/status")
def get_status() -> dict[str, Any]:
    """Retourne la santé globale et le statut de chaque source configurée."""
    sources = load_sources_config()
    db = Path("data/openlux.duckdb")
    con = duckdb.connect(str(db), read_only=True) if db.exists() else None
    health = get_latest_source_health(con) if con else {}
    if con:
        con.close()

    items = [
        {
            "source_id": s,
            "domain": src.domain,
            "status": (h := health.get(s, {})).get("status", "NOT_TESTED"),
            "trust_score": float(h.get("trust_score", 100.0)),
            "row_count": int(h.get("row_count", 0)),
            "last_checked_utc": h.get("last_checked_utc"),
            "last_changed_utc": h.get("last_changed_utc"),
        }
        for s, src in sources.items()
    ]
    st = [i["status"] for i in items]
    overall = "DEGRADED" if "ERROR" in st else ("ATTENTION" if "ATTENTION" in st else "HEALTHY")
    return {"status": overall, "checked_at_utc": datetime.now(UTC).isoformat(), "sources": items}


@app.get("/v1/datasets")
def list_datasets() -> dict[str, Any]:
    """Catalogue dynamique des tables Gold disponibles."""
    sources, res = load_sources_config(), []
    for name in list_gold_datasets():
        path = Path("data/gold") / f"{name}.parquet"
        con, p = duckdb.connect(":memory:"), path.as_posix()
        cols = [
            {"name": c[0], "type": c[1]}
            for c in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [p]).fetchall()
        ]
        cnt = con.execute("SELECT count(*) FROM read_parquet(?)", [p]).fetchone()[0]
        s_id = (
            con.execute("SELECT DISTINCT source_id FROM read_parquet(?) LIMIT 1", [p]).fetchall()
            if any(c["name"] == "source_id" for c in cols)
            else []
        )
        con.close()
        src = sources.get(s_id[0][0]) if (s_id and s_id[0][0]) else None
        res.append(
            {
                "dataset": name,
                "description": src.description if src else "",
                "semantic_summary": src.semantic_summary if src else "",
                "known_limitations": src.known_limitations if src else "",
                "license_spdx": src.license_spdx if src else "CC0-1.0",
                "commercial_use_safe": src.commercial_use_safe if src else True,
                "row_count": cnt,
                "columns": cols,
            }
        )
    return {"datasets": res}


@app.get("/v1/data/{dataset}")
def get_data(
    dataset: str,
    commune: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Requête paramétrée sécurisée sur un dataset Gold avec filtrage et enveloppe _meta."""
    # POURQUOI : Validation stricte contre la whitelist Gold pour prévenir l'injection SQL.
    if not (path := get_gold_table_path(dataset)):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset}' non autorisé ou inconnu.")
    con, _, rows, total = query_gold_table(
        path,
        commune,
        date_from,
        date_to,
        lat,
        lon,
        radius_km,
        max(1, min(limit, 1000)),
        max(0, offset),
    )
    con.close()
    meta = get_gold_metadata(path, row_count=len(rows))
    meta["total_matched"] = total
    return {"_meta": meta, "data": rows}


@app.get("/v1/exports/{dataset}.parquet")
def export_parquet(dataset: str) -> FileResponse:
    """Téléchargement direct du fichier Parquet ZSTD officiel."""
    if not (path := get_gold_table_path(dataset)):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset}' non autorisé.")
    return FileResponse(
        path, media_type="application/vnd.apache.parquet", filename=f"{path.stem}.parquet"
    )


def _stream_export(path: Path, is_geojson: bool):
    # POURQUOI : Streaming à la volée depuis DuckDB in-memory sans copie disque.
    con, p = duckdb.connect(":memory:"), path.as_posix()
    cols = [c[0] for c in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [p]).fetchall()]
    cur = con.execute("SELECT * FROM read_parquet(?)", [p])
    if not is_geojson:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(cols)
        yield buf.getvalue()
        while chunk := cur.fetchmany(500):
            buf.seek(0)
            buf.truncate(0)
            for r in chunk:
                writer.writerow([x.isoformat() if hasattr(x, "isoformat") else x for x in r])
            yield buf.getvalue()
    else:
        lat_i, lon_i = (
            (cols.index("lat") if "lat" in cols else -1),
            (cols.index("lon") if "lon" in cols else -1),
        )
        yield '{"type": "FeatureCollection", "features": [\n'
        first = True
        while chunk := cur.fetchmany(500):
            for r in chunk:
                geom = (
                    {"type": "Point", "coordinates": [r[lon_i], r[lat_i]]}
                    if (lat_i >= 0 and lon_i >= 0 and r[lat_i] is not None and r[lon_i] is not None)
                    else None
                )
                props = {
                    cols[i]: (r[i].isoformat() if hasattr(r[i], "isoformat") else r[i])
                    for i in range(len(cols))
                    if i not in (lat_i, lon_i)
                }
                feat = json.dumps({"type": "Feature", "geometry": geom, "properties": props})
                yield f"{'' if first else ',\n'}{feat}"
                first = False
        yield "\n]}"
    con.close()


@app.get("/v1/exports/{dataset}.csv")
def export_csv(dataset: str) -> StreamingResponse:
    """Export CSV streamé à la volée depuis DuckDB."""
    if not (path := get_gold_table_path(dataset)):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset}' non autorisé.")
    return StreamingResponse(
        _stream_export(path, False),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{path.stem}.csv"'},
    )


@app.get("/v1/exports/{dataset}.geojson")
def export_geojson(dataset: str) -> StreamingResponse:
    """Export GeoJSON streamé à la volée depuis DuckDB."""
    if not (path := get_gold_table_path(dataset)):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset}' non autorisé.")
    return StreamingResponse(
        _stream_export(path, True),
        media_type="application/geo+json",
        headers={"Content-Disposition": f'attachment; filename="{path.stem}.geojson"'},
    )
