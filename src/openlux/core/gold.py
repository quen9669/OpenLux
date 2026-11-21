"""Rôle : Export atomique, registre sécurisé et requêtes sur la couche Gold Parquet.
Entrées/Sorties : Lit/écrit les tables Gold dans data/gold/ et DuckDB en mémoire.
Hors-scope : N'effectue pas d'appels réseau ni de transformation Silver dbt.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

from openlux.config import load_sources_config
from openlux.core.quality import get_latest_source_health


def export_gold_parquets(
    duckdb_path: Path | str = "data/openlux.duckdb", gold_dir: Path | str = "data/gold"
) -> list[str]:
    """Exporte atomiquement chaque table Gold en Parquet ZSTD via la zone temporaire .tmp."""
    if not Path(duckdb_path).exists():
        return []
    target, tmp = Path(gold_dir), Path(gold_dir) / ".tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(duckdb_path), read_only=True)
    try:
        sql = (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name LIKE 'gold_%' AND table_schema = 'main'"
        )
        tables = [r[0] for r in con.execute(sql).fetchall()]
        for tbl in tables:
            t_path, f_path = tmp / f"{tbl}.parquet", target / f"{tbl}.parquet"
            con.execute(f"COPY {tbl} TO '{t_path.as_posix()}' (FORMAT PARQUET, CODEC 'ZSTD')")
            if f_path.exists():
                f_path.unlink()
            os.replace(t_path, f_path)
        return tables
    finally:
        con.close()


def list_gold_datasets(gold_dir: Path | str = "data/gold") -> list[str]:
    d = Path(gold_dir)
    return [p.stem for p in d.glob("gold_*.parquet")] if d.exists() else []


def get_gold_table_path(dataset: str, gold_dir: Path | str = "data/gold") -> Path | None:
    d = Path(gold_dir)
    if not d.exists() or any(c in dataset for c in ("/", "\\", ";", "'", '"', "..")):
        return None
    valid = {p.stem.lower(): p for p in d.glob("gold_*.parquet")}
    norm = dataset.strip().lower()
    return (
        valid.get(norm)
        or valid.get(f"gold_{norm}")
        or next((p for s, p in valid.items() if norm in s), None)
    )


def get_gold_metadata(
    parquet_path: Path, row_count: int, duckdb_path: Path | str = "data/openlux.duckdb"
) -> dict[str, Any]:
    con, p_s = duckdb.connect(":memory:"), parquet_path.as_posix()
    cols = [c[0] for c in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [p_s]).fetchall()]
    sid = (
        con.execute("SELECT DISTINCT source_id FROM read_parquet(?) LIMIT 1", [p_s]).fetchone()
        if "source_id" in cols
        else None
    )
    con.close()
    sid = sid[0] if sid and sid[0] else None
    src = load_sources_config().get(sid) if sid else None
    health: dict[str, Any] = {}
    if Path(duckdb_path).exists():
        try:
            with duckdb.connect(str(duckdb_path), read_only=True) as c:
                health = get_latest_source_health(c).get(sid or "", {})
        except Exception:
            pass

    last_chk = health.get("last_checked_utc") or datetime.now(UTC).isoformat()
    status, is_stale = health.get("status", "GOOD"), False
    if last_chk and src:
        try:
            age = (datetime.now(UTC) - datetime.fromisoformat(last_chk)).total_seconds() / 60.0
            is_stale = (age > float(src.sla_minutes)) or (status == "ERROR")
        except Exception:
            pass

    return {
        "dataset": parquet_path.stem,
        "trust_score": float(health.get("trust_score", 100.0)),
        "status": status,
        "is_stale": is_stale,
        "last_checked_utc": last_chk,
        "last_changed_utc": health.get("last_changed_utc") or last_chk,
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
    try:
        con.execute("LOAD spatial;")
    except Exception:
        pass
    cols = [c[0] for c in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [p_s]).fetchall()]
    clauses, params = [], [p_s]

    if commune and "commune_lau" in cols:
        clauses.append("LOWER(commune_lau) LIKE LOWER(?)")
        params.append(f"%{commune}%")
    for d, op in [(date_from, ">="), (date_to, "<=")]:
        if d:
            dcol = "observed_at_utc" if "observed_at_utc" in cols else "holiday_date"
            cast = "TRY_CAST(? AS TIMESTAMP)" if dcol == "observed_at_utc" else "?"
            clauses.append(f"{dcol} {op} {cast}")
            params.append(d)
    if lat is not None and lon is not None and radius_km is not None and "lat" in cols:
        clauses.append(
            "lat IS NOT NULL AND lon IS NOT NULL AND "
            "ST_Distance_Spheroid(ST_Point(lon, lat), ST_Point(?, ?)) <= ?"
        )
        params.extend([float(lon), float(lat), float(radius_km) * 1000.0])

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total = con.execute(f"SELECT count(*) FROM read_parquet(?){where}", params).fetchone()[0]
    data_sql = f"SELECT * FROM read_parquet(?){where}"
    data_params = list(params)
    if limit is not None:
        data_sql += " LIMIT ? OFFSET ?"
        data_params.extend([max(1, limit), max(0, offset)])

    cur = con.execute(data_sql, data_params)
    out_cols = [d[0] for d in cur.description]
    rows = [dict(zip(out_cols, r, strict=False)) for r in cur.fetchall()]
    return con, out_cols, rows, total
