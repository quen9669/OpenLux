"""Test d'intégration vertical complet (Vertical Slice) des sources en mode offline."""

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
    if "metdata/weather" in url_str or "open-meteo.com/v1/forecast" in url_str:
        raw = Path("tests/fixtures/meteo_lux_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "datex2" in url_str:
        raw = Path("tests/fixtures/cita_datex2_sample.xml").read_bytes()
        return httpx.Response(200, content=raw)
    if "jours-feries" in url_str:
        raw = Path("tests/fixtures/holidays_lu_sample.csv").read_bytes()
        return httpx.Response(200, content=raw)
    if "qualite-de-lair" in url_str or "air-quality" in url_str:
        raw = Path("tests/fixtures/air_quality_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "niveaux-eau" in url_str or "inondations" in url_str:
        raw = Path("tests/fixtures/water_levels_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "prix-carburants" in url_str or "energy-prices" in url_str:
        raw = Path("tests/fixtures/fuel_prices_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "statec-inflation" in url_str or "prc_hicp_midx" in url_str:
        raw = Path("tests/fixtures/statec_inflation_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "electricity-spot" in url_str or "energy-charts" in url_str:
        raw = Path("tests/fixtures/electricity_spot_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "surveillance-radiologique" in url_str or "remap" in url_str:
        raw = Path("tests/fixtures/radioactivity_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "eaux-de-baignade" in url_str or "bathing_water" in url_str:
        raw = Path("tests/fixtures/bathing_water_sample.csv").read_bytes()
        return httpx.Response(200, content=raw)
    return httpx.Response(404, text="Not Found")


def test_vertical_slice_end_to_end(tmp_path: Path) -> None:
    # 1. Chargement des sources configurées
    sources = load_sources_config()
    assert "meteo_lux_obs" in sources
    assert "traffic_cita_datex2" in sources
    assert "holidays_lu" in sources
    assert "air_quality_lu" in sources
    assert "water_levels_lu" in sources
    assert "fuel_prices_lu" in sources
    assert "statec_inflation" in sources
    assert "electricity_spot_delu" in sources
    assert "radioactivity_lu" in sources
    assert "bathing_water_lu" in sources

    mock_client = httpx.Client(transport=httpx.MockTransport(_mock_handler))
    db_path = Path("data/openlux.duckdb")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    init_obs_runs_table(con)

    # 2. Collecte de toutes les sources
    for sid, src in sources.items():
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
    expected_tables = [
        "gold_weather_observations",
        "gold_traffic_events",
        "gold_holidays",
        "gold_air_quality",
        "gold_water_levels",
        "gold_fuel_prices",
        "gold_statec_inflation",
        "gold_electricity_spot",
        "gold_radioactivity",
        "gold_bathing_water",
    ]
    for tbl in expected_tables:
        assert tbl in exported

    gold_files = list_gold_datasets()
    for tbl in expected_tables:
        assert tbl in gold_files

    # Vérification que .tmp est bien vidé (atomicité)
    tmp_gold = Path("data/gold/.tmp")
    assert not any(tmp_gold.glob("*.parquet"))

    # Vérification lecture DuckDB directe sur les fichiers Parquet Gold
    con_gold = duckdb.connect()
    count_weather = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_weather_observations.parquet'"
    ).fetchone()[0]
    count_air = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_air_quality.parquet'"
    ).fetchone()[0]
    count_water = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_water_levels.parquet'"
    ).fetchone()[0]
    count_fuel = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_fuel_prices.parquet'"
    ).fetchone()[0]
    count_inflation = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_statec_inflation.parquet'"
    ).fetchone()[0]
    count_elec = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_electricity_spot.parquet'"
    ).fetchone()[0]
    count_rad = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_radioactivity.parquet'"
    ).fetchone()[0]
    count_bath = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_bathing_water.parquet'"
    ).fetchone()[0]
    con_gold.close()

    assert count_weather >= 3
    assert count_air >= 4
    assert count_water >= 4
    assert count_fuel >= 4
    assert count_inflation >= 3
    assert count_elec >= 4
    assert count_rad >= 4
    assert count_bath >= 4

    # 5. Test de la commande rebuild 100 % hors-ligne
    rebuild_rc = rebuild_pipeline()
    assert rebuild_rc == 0

    # 6. Vérification de STATUS.md généré
    con_final = duckdb.connect(str(db_path), read_only=True)
    generate_status_markdown(sources, get_latest_source_health(con_final))
    con_final.close()

    status_content = Path("STATUS.md").read_text(encoding="utf-8")
    for sid in sources:
        assert sid in status_content
    assert "🟢 `GOOD`" in status_content
