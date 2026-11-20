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
    """Composantes unitaires et score global de confiance d'une source."""

    trust_score: float
    status: str  # GOOD, ATTENTION, ERROR, NOT_TESTED
    score_freshness: float
    score_completeness: float
    score_validity: float
    score_source: float


def init_obs_runs_table(con: duckdb.DuckDBPyConnection) -> None:
    """Initialise la table MLOps obs_runs dans DuckDB si elle n'existe pas."""
    # POURQUOI : Traçabilité MLOps conforme aux contrats API (_meta) et monitoring zéro-infra.
    con.execute("""
        CREATE TABLE IF NOT EXISTS obs_runs (
            run_id VARCHAR,
            source_id VARCHAR,
            pipeline_git_sha VARCHAR,
            run_outcome VARCHAR,
            last_checked_utc VARCHAR,
            last_changed_utc VARCHAR,
            trust_score DOUBLE,
            score_freshness DOUBLE,
            score_completeness DOUBLE,
            score_validity DOUBLE,
            score_source DOUBLE,
            row_count BIGINT,
            sha256 VARCHAR,
            error_message VARCHAR,
            recorded_at_utc VARCHAR
        )
    """)


def get_dbt_validity_score(
    source_id: str, run_results_path: Path | str = "dbt_project/target/run_results.json"
) -> float:
    """Lit run_results.json de dbt pour déterminer le taux de tests réussis sans duplication."""
    path = Path(run_results_path)
    if not path.exists():
        return 100.0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        results = data.get("results", [])
        source_tests = [
            r
            for r in results
            if r.get("unique_id", "").startswith("test.") and source_id in r.get("unique_id", "")
        ]
        if not source_tests:
            return 100.0
        passed = sum(1 for t in source_tests if t.get("status") in ("pass", "success"))
        return round((passed / len(source_tests)) * 100.0, 1)
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
    """Calcule le Trust Score selon la formule normalisée à 4 composantes."""
    if collector_status == "NOT_TESTED":
        return QualityMetrics(0.0, "NOT_TESTED", 0.0, 0.0, 0.0, 0.0)

    # 1. Fraîcheur (35 %) : basé sur last_checked_utc pour ne pas pénaliser UNCHANGED
    try:
        checked_dt = datetime.fromisoformat(last_checked_utc)
        age_minutes = max(0.0, (datetime.now(UTC) - checked_dt).total_seconds() / 60.0)
    except Exception:
        age_minutes = 0.0
    sla = float(source.sla_minutes)
    if age_minutes <= sla:
        s_freshness = 100.0
    elif age_minutes >= 3.0 * sla:
        s_freshness = 0.0
    else:
        s_freshness = max(0.0, 100.0 * (1.0 - (age_minutes - sla) / (2.0 * sla)))

    # 2. Complétude (25 %) : présence des champs obligatoires et seuil min de lignes
    min_rows = source.quality.min_rows
    row_ratio = 1.0 if min_rows <= 0 else min(1.0, row_count / float(min_rows))
    field_ratio = 1.0 if has_required_fields else 0.5
    s_completeness = round(row_ratio * field_ratio * 100.0, 1)

    # 3. Validité (20 %) : résultat dbt ou test d'intégrité
    s_validity = 0.0 if collector_status == "ERROR" else dbt_validity

    # 4. Source (20 %) : 100 si primaire officielle, 80 si backup, 0 si échec
    s_source = 100.0 if source_used == "primary" else (80.0 if source_used == "backup" else 0.0)

    score = round(
        0.35 * s_freshness + 0.25 * s_completeness + 0.20 * s_validity + 0.20 * s_source, 1
    )
    # POURQUOI : Si la source de secours est active, l'état bascule en ATTENTION (score <= 84).
    if source_used == "backup" or collector_status == "ATTENTION":
        status = "ATTENTION"
        score = min(score, 84.0)
    else:
        status = "GOOD" if score >= 85.0 else ("ATTENTION" if score >= 60.0 else "ERROR")
    return QualityMetrics(score, status, s_freshness, s_completeness, s_validity, s_source)


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
    """Insère un run unitaire dans obs_runs de façon déterministe."""
    now_iso = datetime.now(UTC).isoformat()
    # POURQUOI : Paramétrage '?' strict contre toute tentative d'injection SQL.
    con.execute(
        """
        INSERT INTO obs_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
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
            now_iso,
        ],
    )


def get_latest_source_health(con: duckdb.DuckDBPyConnection) -> dict[str, dict[str, Any]]:
    """Récupère l'état de santé le plus récent pour chaque source connue."""
    rows = con.execute("""
        SELECT source_id, run_outcome, trust_score, row_count,
               last_checked_utc, last_changed_utc, error_message
        FROM (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY source_id ORDER BY recorded_at_utc DESC) as rn
            FROM obs_runs
        ) WHERE rn = 1
    """).fetchall()
    return {
        row[0]: {
            "status": row[1],
            "trust_score": row[2],
            "row_count": row[3],
            "last_checked_utc": row[4],
            "last_changed_utc": row[5],
            "error_message": row[6],
        }
        for row in rows
    }
