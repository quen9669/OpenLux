"""Tests unitaires du calcul du Trust Score (formule, fraîcheur vs mutation, bornes)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from openlux.config import EndpointConfig, QualityConfig, SourceConfig
from openlux.core.quality import calculate_trust_score


def _create_source(cadence: int = 15, sla: int = 30) -> SourceConfig:
    return SourceConfig(
        id="test_score_source",
        domain="weather",
        description="Source de test",
        adapter="http_json",
        cadence_minutes=cadence,
        sla_minutes=sla,
        primary=EndpointConfig(url="https://mock.primary.lu"),
        quality=QualityConfig(min_rows=10, required_fields=["temp"]),
    )


def test_trust_score_nominal_is_good() -> None:
    src = _create_source()
    now_iso = datetime.now(UTC).isoformat()
    # Cas parfait : primaire, récent, 100% lignes, tests dbt 100%
    metrics = calculate_trust_score(
        src,
        collector_status="SUCCESS",
        source_used="primary",
        row_count=15,
        last_checked_utc=now_iso,
        dbt_validity=100.0,
    )
    assert metrics.status == "GOOD"
    assert metrics.trust_score >= 85.0
    assert metrics.score_freshness == 100.0
    assert metrics.score_source == 100.0


def test_trust_score_freshness_vs_mutation_distinction() -> None:
    src = _create_source(sla=60)
    now = datetime.now(UTC)
    # last_checked_utc est récent (il y a 5 min) alors que les données sont stables (UNCHANGED)
    recent_checked_iso = (now - timedelta(minutes=5)).isoformat()

    metrics = calculate_trust_score(
        src,
        collector_status="UNCHANGED",
        source_used="primary",
        row_count=10,
        last_checked_utc=recent_checked_iso,
    )
    # La fraîcheur DOIT être à 100 car checked <= SLA, même si le payload n'a pas muté
    assert metrics.score_freshness == 100.0
    assert metrics.trust_score >= 85.0
    assert metrics.status == "GOOD"


def test_trust_score_backup_active_falls_in_attention() -> None:
    src = _create_source(sla=60)
    now_iso = datetime.now(UTC).isoformat()
    # Source de secours active : source = 80
    metrics = calculate_trust_score(
        src,
        collector_status="ATTENTION",
        source_used="backup",
        row_count=8,  # Légèrement sous min_rows (10)
        last_checked_utc=now_iso,
    )
    assert metrics.status == "ATTENTION"
    assert 60.0 <= metrics.trust_score < 85.0
    assert metrics.score_source == 80.0


def test_trust_score_stale_and_broken_is_error() -> None:
    src = _create_source(sla=30)
    now = datetime.now(UTC)
    # Contrôle vieux de 4h (> 3 * SLA = 90 min)
    old_iso = (now - timedelta(hours=4)).isoformat()
    metrics = calculate_trust_score(
        src,
        collector_status="ERROR",
        source_used="none",
        row_count=0,
        last_checked_utc=old_iso,
        dbt_validity=0.0,
    )
    assert metrics.status == "ERROR"
    assert metrics.trust_score < 60.0
    assert metrics.score_freshness == 0.0
    assert metrics.score_source == 0.0


def test_trust_score_not_tested() -> None:
    src = _create_source()
    metrics = calculate_trust_score(
        src,
        collector_status="NOT_TESTED",
        source_used="none",
        row_count=0,
        last_checked_utc="",
    )
    assert metrics.status == "NOT_TESTED"
    assert metrics.trust_score == 0.0
