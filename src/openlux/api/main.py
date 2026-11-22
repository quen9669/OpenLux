"""Rôle : API REST FastAPI exposant les Data Marts Gold en lecture seule et monitoring.
Entrées/Sorties : Requêtes HTTP GET -> JSON standardisé (_meta), streaming CSV/GeoJSON, Parquet.
Hors-scope : N'effectue aucune écriture en base ni modification de données.
"""

from __future__ import annotations

import asyncio
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import duckdb
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse, StreamingResponse
from starlette.staticfiles import StaticFiles

from openlux.config import load_sources_config
from openlux.core.gold import (
    get_gold_metadata,
    get_gold_table_path,
    list_gold_datasets,
    query_gold_table,
    stream_gold_export,
)
from openlux.core.monitoring import build_monitoring_payload, format_prometheus_metrics
from openlux.core.quality import get_latest_source_health, get_source_run_history

_cached_health: dict[str, Any] = {}
_cached_history: dict[str, Any] = {}


def _get_health_and_history() -> tuple[dict[str, Any], dict[str, Any]]:
    global _cached_health, _cached_history
    if (db := Path("data/openlux.duckdb")).exists():
        for _ in range(3):
            try:
                with duckdb.connect(str(db), read_only=True) as con:
                    _cached_health = get_latest_source_health(con)
                    _cached_history = get_source_run_history(con)
                break
            except Exception:
                time.sleep(0.05)
    return _cached_health, _cached_history


async def _bg_scheduler_loop() -> None:
    try:
        from openlux.cli import run_pipeline

        await asyncio.to_thread(run_pipeline, due_only=True)
    except Exception:
        pass
    while True:
        try:
            await asyncio.sleep(60)
            from openlux.cli import run_pipeline

            await asyncio.to_thread(run_pipeline, due_only=True)
        except (asyncio.CancelledError, KeyboardInterrupt):
            break
        except Exception:
            pass


@asynccontextmanager
async def lifespan(_app: FastAPI):
    sync = os.environ.get("OPENLUX_AUTO_SYNC") == "1"
    task = asyncio.create_task(_bg_scheduler_loop()) if sync else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="OpenLux Hub API", version="0.1.0", docs_url="/docs", lifespan=lifespan)


def _get_path_or_404(dataset: str) -> Path:
    if not (path := get_gold_table_path(dataset)):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset}' inconnu.")
    return path


@app.get("/v1/status")
def get_status() -> dict[str, Any]:
    sources = load_sources_config()
    health, history = _get_health_and_history()
    return build_monitoring_payload(sources, health, history)


@app.get("/metrics")
def get_prometheus_metrics() -> PlainTextResponse:
    sources = load_sources_config()
    health, _ = _get_health_and_history()
    return PlainTextResponse(format_prometheus_metrics(sources, health))


@app.get("/v1/datasets")
def list_datasets() -> dict[str, Any]:
    sources, res = load_sources_config(), []
    for name in list_gold_datasets():
        p = (Path("data/gold") / f"{name}.parquet").as_posix()
        with duckdb.connect(":memory:") as con:
            cols = [
                {"name": c[0], "type": c[1]}
                for c in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [p]).fetchall()
            ]
            cnt = con.execute("SELECT count(*) FROM read_parquet(?)", [p]).fetchone()[0]
            s_id = (
                con.execute(
                    "SELECT DISTINCT source_id FROM read_parquet(?) LIMIT 1", [p]
                ).fetchone()
                if any(c["name"] == "source_id" for c in cols)
                else None
            )
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
    return {
        "_meta": get_gold_metadata(path, row_count=len(rows)) | {"total_matched": total},
        "data": rows,
    }


@app.get("/v1/exports/{dataset}.parquet")
def export_parquet(dataset: str) -> FileResponse:
    p = _get_path_or_404(dataset)
    return FileResponse(p, media_type="application/vnd.apache.parquet", filename=p.name)


@app.get("/v1/exports/{dataset}.csv")
def export_csv(dataset: str) -> StreamingResponse:
    p = _get_path_or_404(dataset)
    return StreamingResponse(
        stream_gold_export(p, False),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{p.stem}.csv"'},
    )


@app.get("/v1/exports/{dataset}.geojson")
def export_geojson(dataset: str) -> StreamingResponse:
    p = _get_path_or_404(dataset)
    return StreamingResponse(
        stream_gold_export(p, True),
        media_type="application/geo+json",
        headers={"Content-Disposition": f'attachment; filename="{p.stem}.geojson"'},
    )


@app.get("/v2")
def v2_portal() -> RedirectResponse:
    return RedirectResponse(url="/v2/")


for p, r, n in [("web_v2", "/v2", "web_v2"), ("web", "/", "web")]:
    if Path(p).exists():
        app.mount(r, StaticFiles(directory=p, html=True), name=n)
