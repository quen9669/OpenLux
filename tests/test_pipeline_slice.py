"""Test d'intégration vertical complet (Vertical Slice) des 3 sources pilotes en mode offline."""

from __future__ import annotations

from pathlib import Path

import duckdb
import httpx

from openlux.cli import _run_dbt_command, rebuild_pipeline
from openlux.config import load_sources_config
from openlux.core.collector import collect_source
from openlux.core.gold import export_gold_parquets, list_gold_datasets
from openlux.core.monitoring import generate_status_markdown
from openlux.core.quality import (
    calculate_trust_score,
    get_dbt_validity_score,
    get_latest_source_health,
    init_obs_runs_table,
    record_run,
)


def _mock_handler(request: httpx.Request) -> httpx.Response:
    url_str = str(request.url)
    if "metdata/weather" in url_str or "open-meteo" in url_str:
        raw = Path("tests/fixtures/meteo_lux_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "datex2" in url_str:
        raw = Path("tests/fixtures/cita_datex2_sample.xml").read_bytes()
        return httpx.Response(200, content=raw)
    if "jours-feries" in url_str:
        raw = Path("tests/fixtures/holidays_lu_sample.csv").read_bytes()
        return httpx.Response(200, content=raw)
    return httpx.Response(404, text="Not Found")


def test_vertical_slice_end_to_end(tmp_path: Path) -> None:
    # 1. Chargement des sources pilotes officielles
    sources = load_sources_config()
    assert "meteo_lux_obs" in sources
    assert "traffic_cita_datex2" in sources
    assert "holidays_lu" in sources

    mock_client = httpx.Client(transport=httpx.MockTransport(_mock_handler))
    db_path = Path("data/openlux.duckdb")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    init_obs_runs_table(con)

    # 2. Collecte des 3 sources pilotes
    for sid in ["meteo_lux_obs", "traffic_cita_datex2", "holidays_lu"]:
        src = sources[sid]
        res = collect_source(src, client=mock_client)
        assert res.status in ("SUCCESS", "ATTENTION")
        assert res.row_count > 0

        # Vérification du stockage Bronze
        bronze_dir = Path("data/bronze") / sid
        assert (bronze_dir / f"latest.{'csv' if src.adapter == 'http_csv' else 'json'}.gz").exists()

        val = get_dbt_validity_score(sid)
        metrics = calculate_trust_score(
            src, res.status, res.source_used, res.row_count, res.checked_at_utc, val
        )
        record_run(
            con,
            "test_slice_run",
            sid,
            "git_test",
            metrics,
            res.row_count,
            res.checked_at_utc,
            res.changed_at_utc,
            res.sha256,
        )

    con.close()

    # 3. Exécution dbt (seed -> run -> test)
    for cmd in ["seed", "run", "test"]:
        assert _run_dbt_command(cmd), f"dbt {cmd} a échoué"

    # 4. Export atomique Parquet Gold
    exported = export_gold_parquets()
    assert len(exported) >= 3
    assert "gold_weather_observations" in exported
    assert "gold_traffic_events" in exported
    assert "gold_holidays" in exported

    gold_files = list_gold_datasets()
    assert "gold_weather_observations" in gold_files
    assert "gold_traffic_events" in gold_files
    assert "gold_holidays" in gold_files

    # Vérification que .tmp est bien vidé (atomicité)
    tmp_gold = Path("data/gold/.tmp")
    assert not any(tmp_gold.glob("*.parquet"))

    # Vérification lecture DuckDB directe sur les fichiers Parquet Gold
    con_gold = duckdb.connect()
    count_weather = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_weather_observations.parquet'"
    ).fetchone()[0]
    count_traffic = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_traffic_events.parquet'"
    ).fetchone()[0]
    count_holidays = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_holidays.parquet'"
    ).fetchone()[0]
    con_gold.close()

    assert count_weather >= 3
    assert count_traffic >= 2
    assert count_holidays >= 10

    # 5. Test de la commande rebuild 100 % hors-ligne
    rebuild_rc = rebuild_pipeline()
    assert rebuild_rc == 0

    # 6. Vérification de STATUS.md généré
    con_final = duckdb.connect(str(db_path), read_only=True)
    generate_status_markdown(sources, get_latest_source_health(con_final))
    con_final.close()

    status_content = Path("STATUS.md").read_text(encoding="utf-8")
    assert "meteo_lux_obs" in status_content
    assert "traffic_cita_datex2" in status_content
    assert "holidays_lu" in status_content
    assert "🟢 `GOOD`" in status_content
