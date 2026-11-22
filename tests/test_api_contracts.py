"""Tests des contrats d'API FastAPI et du serveur FastMCP en mode 100 % offline."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient

from openlux.api.main import app
from openlux.mcp.server import (
    get_luxembourg_day_context,
    get_platform_health,
    query_dataset,
    search_luxembourg_events_and_works,
)


@pytest.fixture
def client() -> TestClient:
    """Fixture de client de test FastAPI."""
    return TestClient(app)


def test_web_portal_serving(client: TestClient) -> None:
    """Vérifie que la racine '/' sert le portail web V1 et que '/v2/' sert la version V2."""
    res = client.get("/")
    assert res.status_code == 200
    assert "OpenLux Hub" in res.text
    assert client.get("/css/style.css").status_code == 200
    assert client.get("/js/app.js").status_code == 200

    res_v2 = client.get("/v2/", follow_redirects=True)
    assert res_v2.status_code == 200
    assert "V2 GOUV" in res_v2.text
    assert client.get("/v2/css/style.css").status_code == 200
    assert client.get("/v2/js/app.js").status_code == 200


def test_api_status(client: TestClient) -> None:
    """Vérifie que /v1/status expose la santé globale, KPIs et métriques riches des sources."""
    res = client.get("/v1/status")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "checked_at_utc" in data
    assert "kpis" in data
    assert "total_sources" in data["kpis"]
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) >= 3
    first = data["sources"][0]
    for key in ("source_id", "trust_score", "row_count", "adapter", "min_rows_passed"):
        assert key in first


def test_api_prometheus_metrics(client: TestClient) -> None:
    """Vérifie que /metrics expose les métriques au format texte Prometheus."""
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "openlux_flow_status" in res.text
    assert "openlux_flow_trust_score" in res.text
    assert "openlux_flow_rows_collected" in res.text


def test_api_datasets_catalog(client: TestClient) -> None:
    """Vérifie le catalogue dynamique des tables Gold (/v1/datasets)."""
    res = client.get("/v1/datasets")
    assert res.status_code == 200
    catalog = res.json().get("datasets", [])
    assert len(catalog) >= 3
    names = [d["dataset"] for d in catalog]
    assert "gold_weather_observations" in names
    assert "gold_traffic_events" in names
    assert "gold_holidays" in names
    for entry in catalog:
        assert "columns" in entry
        assert "license_spdx" in entry
        assert "row_count" in entry


def test_api_meta_contract_and_filters(client: TestClient) -> None:
    """Vérifie le respect strict du contrat _meta (Section 5.3) et le filtrage paramétré."""
    res = client.get("/v1/data/gold_weather_observations?limit=2")
    assert res.status_code == 200
    body = res.json()
    assert "_meta" in body
    meta = body["_meta"]
    required_keys = [
        "dataset",
        "trust_score",
        "status",
        "is_stale",
        "last_checked_utc",
        "last_changed_utc",
        "source_used",
        "source_url",
        "license_spdx",
        "commercial_use_safe",
        "known_limitations",
        "run_id",
        "pipeline_git_sha",
        "row_count",
    ]
    for key in required_keys:
        assert key in meta, f"Clé manquante dans _meta: {key}"

    assert isinstance(meta["trust_score"], float)
    assert isinstance(meta["commercial_use_safe"], bool)
    assert len(body["data"]) <= 2

    # Test avec alias sans préfixe gold_
    res_alias = client.get("/v1/data/weather_observations?limit=1")
    assert res_alias.status_code == 200
    assert len(res_alias.json()["data"]) == 1

    # Test de filtrage géospatial
    res_geo = client.get("/v1/data/gold_weather_observations?lat=49.62&lon=6.20&radius_km=15")
    assert res_geo.status_code == 200
    assert len(res_geo.json()["data"]) >= 1


def test_api_sql_injection_and_path_traversal_rejected(client: TestClient) -> None:
    """Vérifie le rejet systématique (HTTP 404) de toute injection SQL ou path traversal."""
    # POURQUOI : Garantie de sécurité absolue anti-injection SQL selon AGENTS.md.
    attacks = [
        "/v1/data/gold_weather_observations' OR 1=1;--",
        "/v1/data/;' DROP TABLE gold_weather_observations;--",
        "/v1/data/../../etc/passwd",
        "/v1/data/..\\..\\windows\\system32",
        "/v1/data/nonexistent_table",
        "/v1/exports/secret' OR 1=1;--.csv",
        "/v1/exports/../../data/openlux.duckdb.parquet",
    ]
    for url in attacks:
        res = client.get(url)
        assert res.status_code == 404


def test_api_streaming_exports(client: TestClient) -> None:
    """Vérifie le streaming à la volée du CSV et du GeoJSON (zéro duplication disque)."""
    # 1. Export CSV
    res_csv = client.get("/v1/exports/gold_weather_observations.csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert (
        'attachment; filename="gold_weather_observations.csv"'
        in res_csv.headers["content-disposition"]
    )
    lines = res_csv.text.strip().splitlines()
    assert len(lines) >= 2  # Entête + au moins une ligne
    assert "station_id" in lines[0]
    assert "temperature" in lines[0]

    # 2. Export GeoJSON
    res_geo = client.get("/v1/exports/gold_weather_observations.geojson")
    assert res_geo.status_code == 200
    assert "application/geo+json" in res_geo.headers["content-type"]
    geo_data = json.loads(res_geo.text)
    assert geo_data["type"] == "FeatureCollection"
    assert "features" in geo_data
    assert len(geo_data["features"]) >= 1
    first_feat = geo_data["features"][0]
    assert first_feat["type"] == "Feature"
    assert "geometry" in first_feat
    assert "properties" in first_feat

    # 3. Export Parquet
    res_parquet = client.get("/v1/exports/gold_weather_observations.parquet")
    assert res_parquet.status_code == 200
    assert "application/vnd.apache.parquet" in res_parquet.headers["content-type"]
    assert len(res_parquet.content) > 0


def test_api_docs_endpoints(client: TestClient) -> None:
    """Vérifie l'accès à la documentation interactive OpenAPI."""
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_mcp_semantic_tools_offline() -> None:
    """Vérifie l'exécution 100 % déterministe et offline des 4 outils FastMCP."""
    # 1. get_platform_health
    h = get_platform_health()
    assert "_meta" in h
    assert h["_meta"]["dataset"] == "platform_health"
    assert "sources" in h
    assert len(h["sources"]) >= 3

    # Filtrage par domaine
    h_w = get_platform_health(domain="weather")
    assert len(h_w["sources"]) == 1
    assert h_w["sources"][0]["domain"] == "weather"

    # 2. get_luxembourg_day_context
    ctx = get_luxembourg_day_context(date="2026-11-20", commune="Luxembourg")
    assert "_meta" in ctx
    assert ctx["_meta"]["dataset"] == "gold_luxembourg_daily_context"
    assert "context" in ctx
    assert ctx["context"]["commune"] == "Luxembourg"

    # 3. search_luxembourg_events_and_works
    sw = search_luxembourg_events_and_works(
        query="A", date_from="2026-01-01", date_to="2026-12-31", lat=49.61, lon=6.13, radius_km=25.0
    )
    assert "_meta" in sw
    assert sw["_meta"]["dataset"] == "events_and_works"
    assert "results" in sw

    # 4. query_dataset (succès & rejet sécurisé)
    qd = query_dataset("gold_weather_observations", limit=2)
    assert "_meta" in qd
    assert len(qd["data"]) <= 2

    # Rejet sur dataset invalide
    bad = query_dataset("'; DROP TABLE test;--")
    assert bad["_meta"]["status"] == "ERROR"
    assert len(bad["data"]) == 0


def test_housing_split_contracts(client: TestClient) -> None:
    """Vérifie les contrats de service des tables scindées (listings et stats)."""
    # 1. gold_housing_listings
    res_list = client.get("/v1/data/gold_housing_listings?limit=5")
    assert res_list.status_code == 200
    b_list = res_list.json()
    assert "_meta" in b_list
    assert len(b_list["data"]) > 0
    first_l = b_list["data"][0]
    for k in ("record_id", "property_type", "price_eur", "surface_m2", "energy_class"):
        assert k in first_l

    # 2. gold_housing_stats
    res_stats = client.get("/v1/data/gold_housing_stats?limit=5")
    assert res_stats.status_code == 200
    b_stats = res_stats.json()
    assert "_meta" in b_stats
    assert len(b_stats["data"]) > 0
    first_s = b_stats["data"][0]
    for k in ("record_id", "record_type", "reference_period", "units_count"):
        assert k in first_s

    # 3. Alias sans préfixe gold_
    assert client.get("/v1/data/housing_listings?limit=1").status_code == 200
    assert client.get("/v1/data/housing_stats?limit=1").status_code == 200

    # 4. Exports Parquet
    assert client.get("/v1/exports/gold_housing_listings.parquet").status_code == 200
    assert client.get("/v1/exports/gold_housing_stats.parquet").status_code == 200


def test_roadworks_vdl_and_cita_in_api(client: TestClient) -> None:
    """Vérifie la présence conjointe des chantiers VDL et CITA dans gold_roadworks."""
    res = client.get("/v1/data/gold_roadworks?limit=50")
    assert res.status_code == 200
    data = res.json()["data"]
    authorities = {r.get("authority") for r in data}
    assert "VDL" in authorities
    assert "CITA" in authorities


def test_fuel_prices_freshness_in_api(client: TestClient) -> None:
    """Vérifie l'actualisation et la validité des prix des carburants."""
    res = client.get("/v1/data/gold_fuel_prices?limit=20")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 4
    dates = {r.get("observed_at_utc", "")[:10] for r in data}
    assert any("2026-11-22" in d or "2026-11-23" in d for d in dates)
    for r in data:
        assert float(r["price_eur_per_litre"]) > 0.0


def test_gold_edge_cases(tmp_path: Path) -> None:
    """Vérifie la robustesse Gold sur coordonnées nulles, tables sans date et vides."""
    from openlux.core.gold import get_gold_metadata, query_gold_table, stream_gold_export

    # 1. Coordonnées zéro dans stream_gold_export
    p_zero = tmp_path / "test_zero.parquet"
    with duckdb.connect() as con:
        con.execute("CREATE TABLE tz (id INT, lat DOUBLE, lon DOUBLE)")
        con.execute("INSERT INTO tz VALUES (1, 0.0, 0.0), (2, 49.6, 6.1)")
        con.execute(f"COPY tz TO '{p_zero.as_posix()}' (FORMAT PARQUET)")
    geo = json.loads("".join(stream_gold_export(p_zero, is_geojson=True)))
    f0 = geo["features"][0]
    assert f0["geometry"] is not None
    assert f0["geometry"]["coordinates"] == [0.0, 0.0]

    # 2. Table sans colonnes temporelles interrogée avec filtre de date
    p_nodate = tmp_path / "test_nodate.parquet"
    with duckdb.connect() as con:
        con.execute("CREATE TABLE tn (id INT, name VARCHAR)")
        con.execute("INSERT INTO tn VALUES (1, 'val')")
        con.execute(f"COPY tn TO '{p_nodate.as_posix()}' (FORMAT PARQUET)")
    c, cols, rows, tot = query_gold_table(p_nodate, date_from="2026-01-01")
    c.close()
    assert tot == 1
    assert len(rows) == 1

    # 3. Table vide sans lignes pour get_gold_metadata
    p_empty = tmp_path / "test_empty.parquet"
    with duckdb.connect() as con:
        con.execute("CREATE TABLE te (source_id VARCHAR)")
        con.execute(f"COPY te TO '{p_empty.as_posix()}' (FORMAT PARQUET)")
    meta = get_gold_metadata(p_empty, row_count=0)
    assert meta["dataset"] == "test_empty"
