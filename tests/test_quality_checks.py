"""Contrôles qualité P1 : validité dbt par source, chute de volume, champs requis (offline)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from openlux.config import EndpointConfig, QualityConfig, SourceConfig
from openlux.core.checks import dbt_validity_by_source, missing_required, run_checks, volume_drop
from openlux.core.quality import calculate_trust_score


def test_volume_drop_needs_history_and_flags_halving() -> None:
    assert volume_drop(10, [100, 100]) is None  # moins de 3 runs : pas de référence
    assert volume_drop(40, [0, 100, 100, 100]) == 100.0  # les runs vides sont ignorés
    assert volume_drop(60, [100, 100, 100]) is None
    # changement de périmètre voulu : la médiane suit après 3 runs au nouveau niveau
    assert volume_drop(10, [100, 100, 10, 10, 10]) is None


def test_missing_required_lists_empty_fields() -> None:
    payload = json.dumps([{"id": "a", "t": "x"}, {"id": "", "t": "y"}]).encode()
    assert missing_required(["id", "t"], payload) == ["id"]
    assert missing_required(["id"], b"[]") == []
    assert missing_required([], payload) == []


def test_dbt_validity_maps_failed_tests_to_sources(tmp_path: Path) -> None:
    con = duckdb.connect()
    con.execute("CREATE TABLE gold_x AS SELECT * FROM (VALUES ('s1'), ('s2')) t(source_id)")
    con.execute("CREATE TABLE gold_y AS SELECT 's3' AS source_id")
    model = "model.p.gold_{}"
    nodes = {
        "test.p.t_ok": {"name": "t_ok", "depends_on": {"nodes": [model.format("x")]}},
        "test.p.t_ko": {"name": "t_ko", "depends_on": {"nodes": [model.format("x")]}},
        "test.p.t_y": {"name": "t_y", "depends_on": {"nodes": [model.format("y")]}},
    }
    results = [
        {"unique_id": "test.p.t_ok", "status": "pass"},
        {"unique_id": "test.p.t_ko", "status": "warn"},
        {"unique_id": "test.p.t_y", "status": "pass"},
    ]
    (tmp_path / "manifest.json").write_text(json.dumps({"nodes": nodes}), encoding="utf-8")
    (tmp_path / "run_results.json").write_text(json.dumps({"results": results}), encoding="utf-8")
    v = dbt_validity_by_source(con, tmp_path)
    assert v == {"s1": (50.0, ["t_ko"]), "s2": (50.0, ["t_ko"]), "s3": (100.0, [])}
    assert dbt_validity_by_source(con, tmp_path / "absent") == {}


def test_failed_dbt_or_required_field_forbids_good() -> None:
    src = SourceConfig(
        id="s", domain="d", description="", parser="p", cadence_minutes=10, sla_minutes=30,
        primary=EndpointConfig(url="https://x.lu"), quality=QualityConfig(min_rows=1),
    )  # fmt: skip
    now = datetime.now(UTC).isoformat()
    assert calculate_trust_score(src, "SUCCESS", "primary", 5, now).status == "GOOD"
    assert calculate_trust_score(src, "SUCCESS", "primary", 5, now, 50.0).status == "ATTENTION"
    m = calculate_trust_score(src, "SUCCESS", "primary", 5, now, 100.0, False)
    assert m.status == "ATTENTION" and m.trust_score <= 84.0


def test_run_checks_downgrades_volume_drop_and_reports() -> None:
    from openlux.core.collector import CollectorResult

    res = CollectorResult("s", "SUCCESS", "primary", "h", 1, b'[{"id": null}]', None, "t", "t")
    q = QualityConfig(min_rows=1, required_fields=["id"])
    v, req_ok, notes = run_checks(res, q, [100, 100, 100], {"s": (50.0, ["t_ko"])})
    assert (res.status, v, req_ok) == ("ATTENTION", 50.0, False)
    assert notes == [
        "Volume en chute : 1 lignes (médiane 100)",
        "Champs requis vides : id",
        "Tests dbt en échec : t_ko",
    ]


def test_event_sources_skip_volume_check() -> None:
    from openlux.core.collector import CollectorResult

    res = CollectorResult("s", "SUCCESS", "primary", "h", 2, b"[]", None, "t", "t")
    run_checks(res, QualityConfig(min_rows=0), [6, 6, 6], {})
    assert res.status == "SUCCESS"  # alertes ou bouchons : volume variable par nature
