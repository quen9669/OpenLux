"""Rôle : Export atomique, registre sécurisé, requêtes et streaming de la couche Gold Parquet.
Entrées/Sorties : Lit/écrit les tables Gold dans data/gold/ et DuckDB en mémoire.
Hors-scope : N'effectue pas d'appels réseau ni de transformation Silver dbt.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

from openlux.config import load_sources_config
from openlux.core.quality import get_latest_source_health


def _export_one(
    con: duckdb.DuckDBPyConnection, tbl: str, tmp: Path, target: Path
) -> tuple[Path, Path] | None:
    t, f = tmp / f"{tbl}.parquet", target / f"{tbl}.parquet"
    cols = [c[0] for c in con.execute(f"DESCRIBE SELECT * FROM {tbl}").fetchall()]
    cols_s, cp = ", ".join(cols), f"TO '{t.as_posix()}' (FORMAT PARQUET, CODEC 'ZSTD')"
    fb = f"COPY (SELECT * FROM {tbl} WHERE {cols[0]} IS NOT NULL) {cp}"
    if not (f.exists() and f.stat().st_size > 0):
        con.execute(fb)
        return (t, f)
    try:
        p, tp = f.as_posix(), t.as_posix()
        u = f"SELECT * FROM read_parquet('{p}') UNION ALL BY NAME SELECT * FROM {tbl}"
        con.execute(f"COPY (SELECT DISTINCT {cols_s} FROM ({u}) WHERE {cols[0]} IS NOT NULL) {cp}")
        s1, s2 = f"SELECT * FROM read_parquet('{p}')", f"SELECT * FROM read_parquet('{tp}')"
        dq = f"SELECT count(*) FROM (({s1} EXCEPT {s2}) UNION ALL ({s2} EXCEPT {s1}))"
        if con.execute(dq).fetchone()[0] == 0:
            t.unlink(missing_ok=True)
            return None
    except Exception:
        con.execute(fb)
    return (t, f)


def export_gold_parquets(
    duckdb_path: Path | str = "data/openlux.duckdb", gold_dir: Path | str = "data/gold"
) -> list[str]:
    """Exporte de façon incrémentale et atomique chaque table Gold en Parquet ZSTD."""
    if not Path(duckdb_path).exists():
        return []
    target, tmp = Path(gold_dir), Path(gold_dir) / ".tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    con = None
    for _ in range(10):
        with contextlib.suppress(Exception):
            if con := duckdb.connect(str(duckdb_path), read_only=True):
                break
        time.sleep(0.2)
    if not con:
        return []
    try:
        q = "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'gold_%'"
        tables = [r[0] for r in con.execute(q).fetchall()]
        replaces = [r for tbl in tables if (r := _export_one(con, tbl, tmp, target))]
    finally:
        con.close()
    for t, f in replaces:
        for _ in range(5):
            with contextlib.suppress(PermissionError):
                os.replace(t, f)
                break
            time.sleep(0.05)
        with contextlib.suppress(Exception), duckdb.connect(str(duckdb_path)) as rw:
            p_pos = f.as_posix()
            rw.execute(f"CREATE OR REPLACE TABLE {t.stem} AS SELECT * FROM read_parquet('{p_pos}')")
    return tables


def list_gold_datasets(gold_dir: Path | str = "data/gold") -> list[str]:
    return [p.stem for p in Path(gold_dir).glob("gold_*.parquet")]


def get_gold_table_path(dataset: str, gold_dir: Path | str = "data/gold") -> Path | None:
    if any(c in dataset for c in ("/", "\\", ";", "'", '"', "..")):
        return None
    valid = {p.stem.lower(): p for p in Path(gold_dir).glob("gold_*.parquet")}
    return valid.get(n := dataset.strip().lower()) or valid.get(f"gold_{n}")


def get_gold_metadata(
    parquet_path: Path, row_count: int, duckdb_path: Path | str = "data/openlux.duckdb"
) -> dict[str, Any]:
    sid = ""
    with duckdb.connect(":memory:") as con, contextlib.suppress(Exception):
        q = "SELECT DISTINCT source_id FROM read_parquet(?) LIMIT 1"
        if r := con.execute(q, [parquet_path.as_posix()]).fetchone():
            sid = str(r[0]) if r[0] else ""
    src, health = load_sources_config().get(sid) if sid else None, {}
    if Path(duckdb_path).exists():
        with contextlib.suppress(Exception), duckdb.connect(str(duckdb_path), read_only=True) as c:
            health = get_latest_source_health(c).get(sid, {})
    chk = health.get("last_checked_utc") or datetime.now(UTC).isoformat()
    st, stale = health.get("status", "GOOD"), False
    with contextlib.suppress(Exception):
        age = (datetime.now(UTC) - datetime.fromisoformat(chk)).total_seconds() / 60.0
        stale = (age > float(src.sla_minutes)) or (st == "ERROR")
    return {
        "dataset": parquet_path.stem,
        "trust_score": float(health.get("trust_score", 100.0)),
        "status": st,
        "is_stale": stale,
        "last_checked_utc": chk,
        "last_changed_utc": health.get("last_changed_utc") or chk,
        "source_used": "primary",
        "source_url": src.primary.url if src and src.primary else "",
        "license_spdx": src.license_spdx if src else "CC0-1.0",
        "commercial_use_safe": src.commercial_use_safe if src else True,
        "known_limitations": src.known_limitations if src else "",
        "run_id": str(health.get("run_id", "default")),
        "pipeline_git_sha": str(health.get("pipeline_git_sha", "git_v1")),
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
    with contextlib.suppress(Exception):
        con.execute("LOAD spatial;")
    cols = [c[0] for c in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [p_s]).fetchall()]
    clauses, params = [], [p_s]
    if commune and "commune_lau" in cols:
        clauses.append("LOWER(commune_lau) LIKE LOWER(?)")
        params.append(f"%{commune}%")
    dc = next((c for c in ("observed_at_utc", "holiday_date") if c in cols), None)
    if dc:
        cst = "TRY_CAST(? AS TIMESTAMP)" if dc == "observed_at_utc" else "?"
        for d, op in [(date_from, ">="), (date_to, "<=")]:
            if d:
                clauses.append(f"{dc} {op} {cst}")
                params.append(d)
    if None not in (lat, lon, radius_km) and "lat" in cols:
        clauses.append(
            "lat IS NOT NULL AND lon IS NOT NULL AND "
            "ST_Distance_Spheroid(ST_Point(lon, lat), ST_Point(?, ?)) <= ?"
        )
        params.extend([float(lon), float(lat), float(radius_km) * 1000.0])
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total = con.execute(f"SELECT count(*) FROM read_parquet(?){where}", params).fetchone()[0]
    p_lim = list(params) + ([max(1, limit), max(0, offset)] if limit is not None else [])
    s_lim = " LIMIT ? OFFSET ?" if limit is not None else ""
    cur = con.execute(f"SELECT * FROM read_parquet(?){where}{s_lim}", p_lim)
    out_cols = [d[0] for d in cur.description]
    return con, out_cols, [dict(zip(out_cols, r, strict=False)) for r in cur.fetchall()], total


def stream_gold_export(path: Path, is_geojson: bool):
    """Générateur de flux CSV ou GeoJSON depuis un fichier Parquet Gold."""
    fmt = lambda v: v.isoformat() if hasattr(v, "isoformat") else v  # noqa: E731
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
                g = {"type": "Point", "coordinates": [r[lo], r[la]]} if valid else None
                props = {cols[i]: fmt(r[i]) for i in range(len(cols)) if i not in (la, lo)}
                yield f"{sep}{json.dumps({'type': 'Feature', 'geometry': g, 'properties': props})}"
                sep = ",\n"
        yield "\n]}"
