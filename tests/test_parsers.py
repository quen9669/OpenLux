"""Tests unitaires offline pour le module core/parsers.py (XML DATEX II)."""

from __future__ import annotations

from pathlib import Path

from openlux.core.parsers import PARSERS, cita_datex2, strikes_rss


def test_cita_datex2_parses_sample_xml() -> None:
    fixture_path = Path("tests/fixtures/cita_datex2_sample.xml")
    assert fixture_path.exists()
    raw = fixture_path.read_bytes()

    records = cita_datex2(raw)
    assert len(records) == 2

    # Vérification du 1er événement (bouchon sur A1)
    rec1 = records[0]
    assert rec1["event_id"] == "REC_2026_01"
    assert rec1["road_name"] == "A1"
    assert rec1["situation_type"] == "AbnormalTraffic"
    assert rec1["lat"] == 49.6385
    assert rec1["lon"] == 6.2155
    assert "Bouchon de 3 km" in rec1["comment"]

    # Vérification du 2e événement (travaux sur A3)
    rec2 = records[1]
    assert rec2["event_id"] == "REC_2026_02"
    assert rec2["road_name"] == "A3"
    assert rec2["lat"] == 49.5280
    assert rec2["lon"] == 6.1120


def test_cita_datex2_empty_or_malformed() -> None:
    assert cita_datex2(b"") == []
    assert cita_datex2(b"   ") == []


def test_parsers_registry_contains_cita_datex2() -> None:
    assert "cita_datex2" in PARSERS
    assert callable(PARSERS["cita_datex2"])


def test_strikes_rss_filters_and_extracts() -> None:
    fixture_path = Path("tests/fixtures/strikes_rss_sample.xml")
    assert fixture_path.exists()
    raw = fixture_path.read_bytes()

    records = strikes_rss(raw)
    assert len(records) == 3  # Le 2e article (inauguration) doit être ignoré

    rec1 = records[0]
    assert rec1["strike_id"] == "STRIKE_2026_RGTR_01"
    assert "grève" in rec1["title"].lower()
    assert rec1["sector"] == "TRANSPORT"
    assert rec1["country_code"] == "LU"
    assert rec1["country_name"] == "Luxembourg"
    assert "news.openlux.lu" in rec1["source_url"]

    rec2 = records[1]
    assert rec2["strike_id"] == "STRIKE_2026_FP_03"
    assert "manifestation" in rec2["title"].lower()
    assert rec2["sector"] == "PUBLIC"
    assert rec2["country_code"] == "LU"
    assert rec2["country_name"] == "Luxembourg"

    rec3 = records[2]
    assert rec3["strike_id"] == "STRIKE_2026_SNCF_04"
    assert rec3["sector"] == "TRANSPORT"
    assert rec3["country_code"] == "FR"
    assert rec3["country_name"] == "France"


def test_strikes_rss_empty() -> None:
    assert strikes_rss(b"") == []
    assert strikes_rss(b"   ") == []
