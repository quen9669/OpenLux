"""Contrats de l'API FastAPI et des outils FastMCP, sur un répertoire Gold isolé (offline)."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient

from openlux.api.main import app
from openlux.mcp.server import get_platform_health, query_dataset


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Gold isolé : une table réelle minimale, servie depuis un cwd temporaire."""
    root = Path.cwd()
    (tmp_path / "data" / "gold").mkdir(parents=True)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "sources.toml").write_text(
        (root / "config" / "sources.toml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    pq = (tmp_path / "data" / "gold" / "gold_mobility_parkings.parquet").as_posix()
    with duckdb.connect() as con:
        con.execute(
            "COPY (SELECT * FROM (VALUES ('20', 'Adenauer', 406, 49.630363, 6.157175, "
            "'Luxembourg', TIMESTAMP '2026-11-24 20:55:00', 'parkings_vdl'), "
            "('14', 'Auchan', 0, 49.633296, 6.159885, 'Luxembourg', "
            "TIMESTAMP '2026-11-24 20:55:00', 'parkings_vdl')) "
            "t(parking_id, parking_name, available_spaces, lat, lon, canton, observed_at_utc, "
            f"source_id)) TO '{pq}' (FORMAT PARQUET)"
        )
    monkeypatch.chdir(tmp_path)
    return TestClient(app)


def test_root_redirects_to_v2_portal(client: TestClient) -> None:
    res = client.get("/", follow_redirects=False)
    assert res.status_code in (302, 307) and res.headers["location"] == "/v2/"


def test_datasets_catalog_is_measured(client: TestClient) -> None:
    (d,) = client.get("/v1/datasets").json()["datasets"]
    assert d["dataset"] == "gold_mobility_parkings" and d["row_count"] == 2
    assert d["sources"][0]["source_id"] == "parkings_vdl"
    assert d["coverage"]["from"].startswith("2026-11-24")


def test_data_endpoint_filters_and_meta(client: TestClient) -> None:
    body = client.get("/v1/data/mobility_parkings?commune=luxemb&limit=1").json()
    assert body["_meta"]["total_matched"] == 2 and len(body["data"]) == 1
    # aucune collecte mesurée => aucun score inventé
    assert body["_meta"]["status"] == "NOT_TESTED"
    near = client.get("/v1/data/gold_mobility_parkings?lat=49.6303&lon=6.1572&radius_km=0.1")
    assert [r["parking_id"] for r in near.json()["data"]] == ["20"]


def test_injection_and_traversal_rejected(client: TestClient) -> None:
    for bad in ("'; DROP TABLE x;--", "..%2F..%2Fetc", "gold_inconnue"):
        assert client.get(f"/v1/data/{bad}").status_code == 404
    assert query_dataset("'; DROP TABLE test;--")["data"] == []


def test_exports_stream(client: TestClient) -> None:
    csv_txt = client.get("/v1/exports/gold_mobility_parkings.csv").text
    assert csv_txt.splitlines()[0].startswith("parking_id,parking_name")
    geo = json.loads(client.get("/v1/exports/gold_mobility_parkings.geojson").text)
    assert geo["features"][0]["geometry"]["coordinates"] == [6.157175, 49.630363]
    assert client.get("/v1/exports/gold_mobility_parkings.parquet").status_code == 200


def test_status_and_health_never_default_to_good(client: TestClient) -> None:
    data = client.get("/v1/status").json()
    assert data["kpis"]["total_sources"] == len(data["sources"]) >= 40
    health = get_platform_health(domain="weather")["sources"]
    assert health and all(s["status"] == "NOT_TESTED" and s["trust_score"] == 0 for s in health)
    assert client.get("/openapi.json").status_code == 200
