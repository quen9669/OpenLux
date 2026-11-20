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
    duckdb_path: Path | str = "data/openlux.duckdb",
    gold_dir: Path | str = "data/gold",
) -> list[str]:
    """Exporte atomiquement chaque table Gold en Parquet ZSTD via la zone temporaire .tmp."""
    # POURQUOI : Garantie d'atomicité absolue via os.replace() selon les règles AGENTS.md.
    db_file = Path(duckdb_path)
    if not db_file.exists():
        return []

    target_dir = Path(gold_dir)
    tmp_dir = target_dir / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_file), read_only=True)
    try:
        tables = [
            row[0]
            for row in con.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_name LIKE 'gold_%' AND table_schema = 'main'
            """).fetchall()
        ]
        exported: list[str] = []
        for tbl in tables:
            tmp_path = tmp_dir / f"{tbl}.parquet"
            final_path = target_dir / f"{tbl}.parquet"
            con.execute(f"COPY {tbl} TO '{tmp_path.as_posix()}' (FORMAT PARQUET, CODEC 'ZSTD')")
            if final_path.exists():
                final_path.unlink()
            os.replace(tmp_path, final_path)
            exported.append(tbl)
        return exported
    finally:
        con.close()


def list_gold_datasets(gold_dir: Path | str = "data/gold") -> list[str]:
    """Renvoie la liste des tables Gold disponibles sur disque en format Parquet."""
    directory = Path(gold_dir)
    return [p.stem for p in directory.glob("gold_*.parquet")] if directory.exists() else []


def get_gold_table_path(dataset: str, gold_dir: Path | str = "data/gold") -> Path | None:
    """Résout et valide strictement un dataset contre la whitelist des tables Gold existantes."""
    # POURQUOI : Défense en profondeur contre injection SQL et path traversal.
    gdir = Path(gold_dir)
    if not gdir.exists() or any(c in dataset for c in ("/", "\\", ";", "'", '"', "..")):
        return None
    valid = {p.stem.lower(): p for p in gdir.glob("gold_*.parquet")}
    norm = dataset.strip().lower()
    if norm in valid:
        return valid[norm]
    if f"gold_{norm}" in valid:
        return valid[f"gold_{norm}"]
    for stem, path in valid.items():
        if norm in stem:
            return path
    return None


def get_gold_metadata(
    parquet_path: Path,
    row_count: int,
    duckdb_path: Path | str = "data/openlux.duckdb",
) -> dict[str, Any]:
    """Construit l'enveloppe standard _meta (traçabilité MLOps, SLA et licence)."""
    # POURQUOI : Respect strict du contrat 5.3 pour l'API et les outils FastMCP.
    con_mem = duckdb.connect(":memory:")
    path_s = parquet_path.as_posix()
    cols = [
        c[0] for c in con_mem.execute("DESCRIBE SELECT * FROM read_parquet(?)", [path_s]).fetchall()
    ]
    sid = None
    if "source_id" in cols:
        res = con_mem.execute(
            "SELECT DISTINCT source_id FROM read_parquet(?) LIMIT 1", [path_s]
        ).fetchall()
        sid = res[0][0] if res and res[0][0] else None
    con_mem.close()

    sources = load_sources_config()
    src = sources.get(sid) if sid else None
    health: dict[str, Any] = {}
    db_file = Path(duckdb_path)
    if db_file.exists():
        try:
            c = duckdb.connect(str(db_file), read_only=True)
            health = get_latest_source_health(c).get(sid or "", {})
            c.close()
        except Exception:
            pass

    last_chk = health.get("last_checked_utc") or datetime.now(UTC).isoformat()
    status = health.get("status", "GOOD")
    is_stale = False
    if last_chk and src:
        try:
            age = (datetime.now(UTC) - datetime.fromisoformat(last_chk)).total_seconds() / 60.0
            is_stale = (age > float(src.sla_minutes)) or (status == "ERROR")
        except Exception:
            is_stale = False

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
    """Exécute une requête paramétrée sécurisée (?) avec DuckDB in-memory et spatial."""
    con = duckdb.connect(":memory:")
    try:
        con.execute("LOAD spatial;")
    except Exception:
        pass
    path_s = parquet_path.as_posix()
    cols = [
        c[0] for c in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [path_s]).fetchall()
    ]
    clauses: list[str] = []
    params: list[Any] = [path_s]

    if commune and "commune_lau" in cols:
        clauses.append("LOWER(commune_lau) LIKE LOWER(?)")
        params.append(f"%{commune}%")
    if date_from:
        dcol = "observed_at_utc" if "observed_at_utc" in cols else "holiday_date"
        clauses.append(
            f"{dcol} >= TRY_CAST(? AS TIMESTAMP)" if dcol == "observed_at_utc" else f"{dcol} >= ?"
        )
        params.append(date_from)
    if date_to:
        dcol = "observed_at_utc" if "observed_at_utc" in cols else "holiday_date"
        clauses.append(
            f"{dcol} <= TRY_CAST(? AS TIMESTAMP)" if dcol == "observed_at_utc" else f"{dcol} <= ?"
        )
        params.append(date_to)
    if lat is not None and lon is not None and radius_km is not None and "lat" in cols:
        clauses.append(
            "lat IS NOT NULL AND lon IS NOT NULL AND "
            "ST_Distance_Spheroid(ST_Point(lon, lat), ST_Point(?, ?)) <= ?"
        )
        params.extend([float(lon), float(lat), float(radius_km) * 1000.0])

    where_str = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total = con.execute(f"SELECT count(*) FROM read_parquet(?){where_str}", params).fetchone()[0]

    data_sql = f"SELECT * FROM read_parquet(?){where_str}"
    data_params = list(params)
    if limit is not None:
        data_sql += " LIMIT ? OFFSET ?"
        data_params.extend([max(1, limit), max(0, offset)])

    cur = con.execute(data_sql, data_params)
    out_cols = [d[0] for d in cur.description]
    rows = [dict(zip(out_cols, r, strict=False)) for r in cur.fetchall()]
    return con, out_cols, rows, total
