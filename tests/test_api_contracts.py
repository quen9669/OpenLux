"""Tests des contrats d'API FastAPI et du serveur FastMCP en mode 100 % offline."""

from __future__ import annotations

import json

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


def test_api_status(client: TestClient) -> None:
    """Vérifie que /v1/status expose la santé globale et le statut des sources."""
    res = client.get("/v1/status")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "checked_at_utc" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) >= 3


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
