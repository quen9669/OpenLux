"""Tests unitaires offline pour le module core/parsers.py (XML DATEX II)."""

from __future__ import annotations

from pathlib import Path

from openlux.core.parsers import PARSERS, cita_datex2, fuel_prices_csv, strikes_rss, vdl_parking
from openlux.core.parsers_extra import vdl_roadworks_json


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


def test_cita_datex2_validity_time_specification() -> None:
    xml = b"""<?xml version="1.0" encoding="utf-8"?>
<d2LogicalModel xmlns="http://datex2.eu/schema/2/2_0">
  <payloadPublication>
    <situation id="SIT_01">
      <situationRecord id="REC_01" xsi:type="MaintenanceWorks" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <situationRecordCreationTime>2026-11-20T22:00:00Z</situationRecordCreationTime>
        <validity>
          <validityTimeSpecification>
            <overallStartTime>2026-11-22T08:00:00Z</overallStartTime>
            <overallEndTime>2026-11-22T18:00:00Z</overallEndTime>
          </validityTimeSpecification>
        </validity>
      </situationRecord>
    </situation>
  </payloadPublication>
</d2LogicalModel>"""
    recs = cita_datex2(xml)
    assert len(recs) == 1
    assert recs[0]["start_date"] == "2026-11-22T08:00:00Z"
    assert recs[0]["end_date"] == "2026-11-22T18:00:00Z"


def test_vdl_parking_rfc2822_conversion() -> None:
    raw = b"""{
        "last_build_date": "Sun, 22 Nov 2026 13:16:00 +0100",
        "parking": {
            "glacis": {"titre": "Glacis", "actuel": 400, "total": 1200}
        }
    }"""
    parks = vdl_parking(raw)
    assert len(parks) == 1
    assert "2026-11-22" in parks[0]["observed_at"]


def test_fuel_prices_csv_intervalle_conversion() -> None:
    raw = b"Intervalle,Diesel_B7,Essence_E10\nJan-26,1.45,1.55\n"
    rows = fuel_prices_csv(raw)
    assert len(rows) == 2
    assert rows[0]["observed_at"] == "2026-01-01 00:00:00"


def test_vdl_roadworks_epoch_ms_conversion() -> None:
    raw = b"""{
        "features": [
            {
                "attributes": {
                    "OBJECTID": 101,
                    "START_DATE": 1750024800000,
                    "END_DATE": 1750111200000,
                    "OBJECTIVE": "Chantier Royal"
                },
                "geometry": {"x": 6.13, "y": 49.61}
            }
        ]
    }"""
    works = vdl_roadworks_json(raw)
    assert len(works) == 1
    assert works[0]["start_date"].startswith("2025-") or works[0]["start_date"].startswith("2026-")
    assert works[0]["end_date"].startswith("2025-") or works[0]["end_date"].startswith("2026-")
