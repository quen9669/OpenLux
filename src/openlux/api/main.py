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
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from starlette.staticfiles import StaticFiles

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


def _get_path_or_404(dataset: str) -> Path:
    if not (path := get_gold_table_path(dataset)):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset}' non autorisé ou inconnu.")
    return path


@app.get("/v1/status")
def get_status() -> dict[str, Any]:
    sources, db, health = load_sources_config(), Path("data/openlux.duckdb"), {}
    if db.exists():
        try:
            with duckdb.connect(str(db), read_only=True) as con:
                health = get_latest_source_health(con)
        except Exception:
            pass
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
    st = {i["status"] for i in items}
    overall = "DEGRADED" if "ERROR" in st else ("ATTENTION" if "ATTENTION" in st else "HEALTHY")
    return {"status": overall, "checked_at_utc": datetime.now(UTC).isoformat(), "sources": items}


@app.get("/v1/datasets")
def list_datasets() -> dict[str, Any]:
    sources, res = load_sources_config(), []
    for name in list_gold_datasets():
        p = (Path("data/gold") / f"{name}.parquet").as_posix()
        con = duckdb.connect(":memory:")
        cols = [
            {"name": c[0], "type": c[1]}
            for c in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [p]).fetchall()
        ]
        cnt = con.execute("SELECT count(*) FROM read_parquet(?)", [p]).fetchone()[0]
        s_id = (
            con.execute("SELECT DISTINCT source_id FROM read_parquet(?) LIMIT 1", [p]).fetchone()
            if any(c["name"] == "source_id" for c in cols)
            else None
        )
        con.close()
        src = sources.get(s_id[0]) if s_id else None
        res.append(
            {
                "dataset": name,
                "row_count": cnt,
                "columns": cols,
                "description": getattr(src, "description", ""),
                "semantic_summary": getattr(src, "semantic_summary", ""),
                "known_limitations": getattr(src, "known_limitations", ""),
                "license_spdx": getattr(src, "license_spdx", "CC0-1.0"),
                "commercial_use_safe": getattr(src, "commercial_use_safe", True),
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
    path = _get_path_or_404(dataset)
    p = (path, commune, date_from, date_to, lat, lon, radius_km)
    con, _, rows, total = query_gold_table(*p, max(1, min(limit, 1000)), max(0, offset))
    con.close()
    return {
        "_meta": get_gold_metadata(path, row_count=len(rows)) | {"total_matched": total},
        "data": rows,
    }


@app.get("/v1/exports/{dataset}.parquet")
def export_parquet(dataset: str) -> FileResponse:
    p = _get_path_or_404(dataset)
    return FileResponse(p, media_type="application/vnd.apache.parquet", filename=p.name)


def _stream_export(path: Path, is_geojson: bool):
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
            cols.index("lat") if "lat" in cols else -1,
            cols.index("lon") if "lon" in cols else -1,
        )
        yield '{"type": "FeatureCollection", "features": [\n'
        first = True
        while chunk := cur.fetchmany(500):
            for r in chunk:
                valid = lat_i >= 0 and lon_i >= 0 and r[lat_i] is not None and r[lon_i] is not None
                geom = {"type": "Point", "coordinates": [r[lon_i], r[lat_i]]} if valid else None
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
    p = _get_path_or_404(dataset)
    h = {"Content-Disposition": f'attachment; filename="{p.stem}.csv"'}
    return StreamingResponse(_stream_export(p, False), media_type="text/csv", headers=h)


@app.get("/v1/exports/{dataset}.geojson")
def export_geojson(dataset: str) -> StreamingResponse:
    p = _get_path_or_404(dataset)
    h = {"Content-Disposition": f'attachment; filename="{p.stem}.geojson"'}
    return StreamingResponse(_stream_export(p, True), media_type="application/geo+json", headers=h)


@app.get("/v2")
def v2_portal() -> RedirectResponse:
    return RedirectResponse(url="/v2/")


for p, r, n in [("web_v2", "/v2", "web_v2"), ("web", "/", "web")]:
    if Path(p).exists():
        app.mount(r, StaticFiles(directory=p, html=True), name=n)
