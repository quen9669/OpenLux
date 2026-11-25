"""Rôle : Calcul du Trust Score (0-100) et persistance MLOps dans obs_runs (DuckDB).
Entrées/Sorties : Évalue fraîcheur, complétude, validité et source ; enregistre dans DuckDB.
Hors-scope : N'effectue aucun appel réseau ni modification de fichiers Bronze/Gold.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

from openlux.config import SourceConfig


@dataclass
class QualityMetrics:
    trust_score: float
    status: str
    score_freshness: float
    score_completeness: float
    score_validity: float
    score_source: float


def init_obs_runs_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS obs_runs (
            run_id VARCHAR, source_id VARCHAR, pipeline_git_sha VARCHAR, run_outcome VARCHAR,
            last_checked_utc VARCHAR, last_changed_utc VARCHAR, trust_score DOUBLE,
            score_freshness DOUBLE, score_completeness DOUBLE, score_validity DOUBLE,
            score_source DOUBLE, row_count BIGINT, sha256 VARCHAR, error_message VARCHAR,
            recorded_at_utc VARCHAR
        )
    """)


def get_dbt_validity_score(
    source_id: str, run_results_path: Path | str = "dbt_project/target/run_results.json"
) -> float:
    path = Path(run_results_path)
    if not path.exists():
        return 100.0
    try:
        results = json.loads(path.read_text(encoding="utf-8")).get("results", [])
        tests = [
            r
            for r in results
            if r.get("unique_id", "").startswith("test.") and source_id in r.get("unique_id", "")
        ]
        passed = sum(1 for t in tests if t.get("status") in ("pass", "success"))
        return 100.0 if not tests else round((passed / len(tests)) * 100.0, 1)
    except Exception:
        return 100.0


def calculate_trust_score(
    source: SourceConfig,
    collector_status: str,
    source_used: str,
    row_count: int,
    last_checked_utc: str,
    dbt_validity: float = 100.0,
    has_required_fields: bool = True,
) -> QualityMetrics:
    if collector_status == "NOT_TESTED":
        return QualityMetrics(0.0, "NOT_TESTED", 0.0, 0.0, 0.0, 0.0)
    try:
        age_min = max(
            0.0,
            (datetime.now(UTC) - datetime.fromisoformat(last_checked_utc)).total_seconds() / 60.0,
        )
    except Exception:
        age_min = 0.0
    sla = float(source.sla_minutes)
    s_fresh = (
        100.0
        if age_min <= sla
        else (
            0.0 if age_min >= 3.0 * sla else max(0.0, 100.0 * (1.0 - (age_min - sla) / (2.0 * sla)))
        )
    )
    min_r = source.quality.min_rows
    s_comp = round(
        (1.0 if min_r <= 0 else min(1.0, row_count / float(min_r)))
        * (1.0 if has_required_fields else 0.5)
        * 100.0,
        1,
    )
    s_val = 0.0 if collector_status == "ERROR" else dbt_validity
    s_src = 100.0 if source_used == "primary" else (80.0 if source_used == "backup" else 0.0)
    score = round(0.35 * s_fresh + 0.25 * s_comp + 0.20 * s_val + 0.20 * s_src, 1)
    # POURQUOI : une collecte en échec (primaire et backup) ne peut jamais être affichée saine
    status = (
        "ERROR"
        if collector_status == "ERROR"
        else "ATTENTION"
        if (source_used == "backup" or collector_status == "ATTENTION")
        else ("GOOD" if score >= 85.0 else ("ATTENTION" if score >= 60.0 else "ERROR"))
    )
    if source_used == "backup" or collector_status == "ATTENTION":
        score = min(score, 84.0)
    score = min(score, 59.0) if collector_status == "ERROR" else score
    return QualityMetrics(score, status, s_fresh, s_comp, s_val, s_src)


def record_run(
    con: duckdb.DuckDBPyConnection,
    run_id: str,
    source_id: str,
    pipeline_git_sha: str,
    metrics: QualityMetrics,
    row_count: int,
    last_checked_utc: str,
    last_changed_utc: str,
    sha256: str,
    error_message: str | None = None,
) -> None:
    vals = [
        run_id,
        source_id,
        pipeline_git_sha,
        metrics.status,
        last_checked_utc,
        last_changed_utc,
        metrics.trust_score,
        metrics.score_freshness,
        metrics.score_completeness,
        metrics.score_validity,
        metrics.score_source,
        row_count,
        sha256,
        error_message or "",
        datetime.now(UTC).isoformat(),
    ]
    con.execute("INSERT INTO obs_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", vals)


def get_latest_source_health(con: duckdb.DuckDBPyConnection) -> dict[str, dict[str, Any]]:
    sql = """
        SELECT source_id, run_outcome, trust_score, row_count, last_checked_utc, last_changed_utc,
               error_message, run_id, pipeline_git_sha, score_freshness, score_completeness,
               score_validity, score_source, sha256
        FROM (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY source_id ORDER BY recorded_at_utc DESC) as rn
            FROM obs_runs
        ) WHERE rn = 1
    """
    rows = con.execute(sql).fetchall()
    return {
        r[0]: {
            "status": r[1],
            "trust_score": r[2],
            "row_count": r[3],
            "last_checked_utc": r[4],
            "last_changed_utc": r[5],
            "error_message": r[6],
            "run_id": r[7] if len(r) > 7 and r[7] else "default",
            "pipeline_git_sha": r[8] if len(r) > 8 and r[8] else "git_v1",
            "score_freshness": r[9] if len(r) > 9 and r[9] is not None else 100.0,
            "score_completeness": r[10] if len(r) > 10 and r[10] is not None else 100.0,
            "score_validity": r[11] if len(r) > 11 and r[11] is not None else 100.0,
            "score_source": r[12] if len(r) > 12 and r[12] is not None else 100.0,
            "sha256": r[13] if len(r) > 13 and r[13] else "",
        }
        for r in rows
    }


def get_source_run_history(
    con: duckdb.DuckDBPyConnection, limit_per_source: int = 10
) -> dict[str, list[dict[str, Any]]]:
    try:
        sql = """
            SELECT source_id, run_outcome, trust_score, row_count, last_checked_utc, error_message
            FROM (
                SELECT source_id, run_outcome, trust_score, row_count,
                       last_checked_utc, error_message,
                       ROW_NUMBER() OVER(PARTITION BY source_id ORDER BY recorded_at_utc DESC) as rn
                FROM obs_runs
            ) WHERE rn <= ?
            ORDER BY source_id, last_checked_utc ASC
        """
        res: dict[str, list[dict[str, Any]]] = {}
        for r in con.execute(sql, [limit_per_source]).fetchall():
            res.setdefault(r[0], []).append(
                {
                    "status": r[1],
                    "trust_score": r[2],
                    "row_count": r[3],
                    "checked_at": r[4],
                    "error": r[5],
                }
            )
        return res
    except Exception:
        return {}
