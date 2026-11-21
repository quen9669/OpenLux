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
    if "traffic-fr-a31" in url_str or "bison-fute" in url_str:
        raw = Path("tests/fixtures/traffic_fr_bisonfute_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "traffic-de-a64" in url_str or "autobahn" in url_str:
        raw = Path("tests/fixtures/traffic_de_autobahn_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "traffic-be-e411" in url_str or "trafiroutes" in url_str:
        raw = Path("tests/fixtures/traffic_be_trafiroutes_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "rail-crossborder" in url_str or "crossborder-lu" in url_str:
        raw = Path("tests/fixtures/rail_crossborder_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "mobiliteit-transit" in url_str or "mobiliteit" in url_str:
        raw = Path("tests/fixtures/transit_mobiliteit_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "avl-bus" in url_str or "avl/realtime" in url_str:
        raw = Path("tests/fixtures/transit_avl_rt_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "veloh-live" in url_str or "jcdecaux" in url_str:
        raw = Path("tests/fixtures/veloh_stations_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "parkings-vdl" in url_str or "parkings/occupancy" in url_str:
        raw = Path("tests/fixtures/parkings_vdl_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "chargy-live" in url_str or "chargy" in url_str:
        raw = Path("tests/fixtures/chargy_stations_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "aviation-opensky" in url_str or "opensky-network" in url_str:
        raw = Path("tests/fixtures/aviation_opensky_lu_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "noise-zones" in url_str or "strategic_noise_maps" in url_str:
        raw = Path("tests/fixtures/noise_zones_lu_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "roadworks-cita" in url_str or "roadworks" in url_str:
        raw = Path("tests/fixtures/roadworks_cita_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "roadworks-vdl" in url_str or "vdl.lu/v1/travaux" in url_str:
        raw = Path("tests/fixtures/roadworks_vdl_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "housing-observatoire" in url_str or "observatoire_prix" in url_str:
        raw = Path("tests/fixtures/housing_observatoire_sample.csv").read_bytes()
        return httpx.Response(200, content=raw)
    if "housing-statec" in url_str or "data/permits" in url_str:
        raw = Path("tests/fixtures/housing_statec_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "pistes-cyclables" in url_str or "pistes_cyclables" in url_str:
        raw = Path("tests/fixtures/bike_lanes_lu_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "ouvertures-dominicales" in url_str or "open-sundays" in url_str:
        raw = Path("tests/fixtures/open_sundays_vdl_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    if "centres-recyclage" in url_str or "recycling_centers" in url_str:
        raw = Path("tests/fixtures/recycling_centers_sample.json").read_bytes()
        return httpx.Response(200, content=raw)
    return httpx.Response(404, text="Not Found")


def test_vertical_slice_end_to_end(tmp_path: Path) -> None:
    # 1. Chargement des sources configurées
    sources = load_sources_config()
    assert len(sources) >= 28

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
        "gold_crossborder_traffic",
        "gold_public_transit",
        "gold_mobility_parkings",
        "gold_aviation_noise",
        "gold_roadworks",
        "gold_housing",
        "gold_daily_life",
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
    count_roadworks = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_roadworks.parquet'"
    ).fetchone()[0]
    count_housing = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_housing.parquet'"
    ).fetchone()[0]
    count_daily = con_gold.execute(
        "SELECT count(*) FROM 'data/gold/gold_daily_life.parquet'"
    ).fetchone()[0]
    con_gold.close()

    assert count_weather >= 3
    assert count_roadworks >= 3
    assert count_housing >= 6
    assert count_daily >= 5

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
