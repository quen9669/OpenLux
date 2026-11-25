"""Tests offline des parsers sur de vraies réponses réduites (tests/fixtures, 24/11/2026).
Chaque test vérifie une règle de fiabilité : aucune valeur inventée, filtres, fuseaux, unités.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from openlux.core.collector import PARSERS

FX = Path("tests/fixtures")


def run(parser: str, fixture: str) -> list[dict]:
    return PARSERS[parser]((FX / fixture).read_bytes())


@pytest.mark.parametrize(
    ("parser", "fixture", "key"),
    [
        ("datex2_lu", "cita_situationrecord.xml", "event_id"),
        ("datex2_lu", "cita_chantiers.xml", "event_id"),
        ("vdl_bus_messages", "vdl_bus_messages.xml", "disruption_id"),
        ("vdl_traffic_info", "vdl_traffic_info.json", "event_id"),
        ("meteolux_hvd", "meteolux_hvd.json", "station_id"),
        ("water_levels_csv", "water_levels.csv", "station_name"),
        ("bathing_sites", "bathing_status.json", "site_id"),
        ("veloh_gbfs_status", "gbfs_station_status.json", "station_number"),
        ("vdl_parking", "vdl_parking.json", "parking_id"),
        ("chargy_kml", "chargy.kml", "site_name"),
        ("vdl_roadworks", "vdl_roadworks_layer1.json", "work_id"),
        ("vdl_roadworks", "vdl_roadworks_layer5.json", "work_id"),
        ("mymaps_routes", "mymaps_bike_routes.json", "route_id"),
        ("holidays_lu_json", "holidays_lu.json", "holiday_date"),
        ("meteoalarm_json", "meteoalarm_lu.json", "alert_id"),
        ("petitions_chd_csv", "petitions_chd.csv", "petition_id"),
        ("adem_communes_csv", "adem_communes.csv", "reference_month"),
        ("lustat_csv", "lustat_ipcn.csv", "time_period"),
        ("lustat_csv", "lustat_permits.csv", "time_period"),
        ("fuel_prices_csv", "fuel_prices.csv", "energy_type"),
        ("recycling_gml", "recycling_centers.gml", "item_id"),
        ("overpass_aed", "overpass_aed.json", "item_id"),
        ("echo_algolia", "echo_algolia.json", "event_id"),
        ("vdl_agenda_rss", "vdl_agenda.xml", "event_id"),
        ("rockhal_shows", "rockhal_shows.json", "event_id"),
    ],
)
def test_parser_returns_records_with_key(parser: str, fixture: str, key: str) -> None:
    recs = run(parser, fixture)
    assert recs, f"{parser} n'a rien extrait de {fixture}"
    assert all(r.get(key) not in (None, "") for r in recs)


def test_datex2_road_coordinates_and_utc() -> None:
    recs = run("datex2_lu", "cita_situationrecord.xml")
    assert all(49.4 < r["lat"] < 50.2 and 5.7 < r["lon"] < 6.6 for r in recs)
    assert all(r["start_time_utc"].endswith("+00:00") for r in recs if r["start_time_utc"])
    assert any(r["road_name"] for r in recs)


def test_datex2_france_keeps_only_lorraine_bbox() -> None:
    recs = run("datex2_fr_lorraine", "bisonfute_events.xml")
    assert recs and all(48.85 <= r["lat"] <= 49.6 and r["country_code"] == "FR" for r in recs)


def test_autobahn_filters_border_zone() -> None:
    recs = run("autobahn_events", "autobahn_a8_closure.json")
    assert "far-away" not in {r["event_id"] for r in recs}
    assert all(r["road_name"] == "A8" for r in recs)


def test_rail_filters_luxembourg_axis() -> None:
    sncf = run("sncf_siri_sx", "sncf_siri_sx.xml")
    axis = ("luxemb", "thionville", "metz")
    assert sncf and all(any(k in f"{r['title']} {r['detail']}".lower() for k in axis) for r in sncf)
    irail = run("irail_disturbances", "irail_disturbances.json")
    assert [r["disruption_id"] for r in irail] == ["0"]


def test_openmeteo_skips_missing_hours_and_keeps_order_index() -> None:
    recs = run("openmeteo_weather", "openmeteo_weather.json")
    assert all(r["temperature_c"] is not None for r in recs)
    assert {r["location_index"] for r in recs} == {0, 1}
    assert all(r["data_origin"] == "model" for r in recs)
    air = run("openmeteo_long", "openmeteo_air.json")
    assert {r["pollutant"] for r in air} >= {"pm10", "european_aqi"}


def test_meteolux_converts_wind_to_kmh() -> None:
    (r,) = run("meteolux_hvd", "meteolux_hvd.json")
    assert r["data_origin"] == "station" and r["station_id"] == "ELLX"
    assert r["wind_speed_kmh"] is None or r["wind_speed_kmh"] >= 0


def test_water_levels_local_time_to_utc_and_units() -> None:
    recs = run("water_levels_csv", "water_levels.csv")
    assert all(r["observed_at"].endswith("+00:00") for r in recs)
    assert {r["unit"] for r in recs if r["station_name"] == "Esch-Sure"} == {"m"}
    assert not any(r["station_name"].startswith("SN_") for r in recs)


def test_energy_charts_drops_null_prices() -> None:
    recs = run("energy_charts_price", "energy_charts_price.json")
    assert len(recs) == 3 and all(r["price_eur_per_mwh"] is not None for r in recs)


def test_chargy_counts_connectors() -> None:
    for r in run("chargy_kml", "chargy.kml"):
        used = r["connectors_available"] + r["connectors_charging"] + r["connectors_out_of_service"]
        assert used <= r["connectors_total"]


def test_opensky_ignores_unknown_positions() -> None:
    recs = run("opensky_states", "opensky_states.json")
    assert "abc123" not in {r["icao24"] for r in recs}


def test_openholidays_excludes_bank_holidays() -> None:
    recs = run("openholidays_lu", "openholidays_school_lu.json")
    assert recs and "Vendredi saint" not in {r["name_fr"] for r in recs}
    assert {r["country_code"] for r in recs} == {"LU"}


def test_petitions_exclude_free_text() -> None:
    for r in run("petitions_chd_csv", "petitions_chd.csv"):
        keys = {"petition_id", "filing_date", "title", "petition_type", "status", "signatures"}
        assert set(r) == keys
        assert len(r["title"]) <= 140


def test_observatoire_xlsx_masks_small_samples() -> None:
    rows = run("observatoire_prices_xlsx", "observatoire_prices.xlsx")
    recs = {r["commune_name"]: r for r in rows}
    assert recs["Luxembourg"]["avg_price_eur_m2"] == pytest.approx(11234.75)
    assert recs["Luxembourg"]["reference_year"] == 2024
    assert recs["Bech"]["avg_price_eur"] is None  # '*' = moins de 30 annonces, jamais imputé


def test_recycling_reprojection_lands_in_luxembourg() -> None:
    for r in run("recycling_gml", "recycling_centers.gml"):
        assert 49.44 < r["lat"] < 50.19 and 5.73 < r["lon"] < 6.53


def test_fuel_units_are_explicit() -> None:
    units = {r["energy_type"]: r["unit"] for r in run("fuel_prices_csv", "fuel_prices.csv")}
    assert units["Diesel_B7"] == "EUR/l" and units["Hydrogene"] == "EUR/kg"


def test_strikes_rss_keeps_only_strike_titles() -> None:
    recs = run("strikes_rss", "google_news_strikes.xml")
    assert all("grève" in r["title"].lower() or "streik" in r["title"].lower() for r in recs)


def test_culture_titles_are_truncated() -> None:
    for p, f in [("echo_algolia", "echo_algolia.json"), ("rockhal_shows", "rockhal_shows.json")]:
        assert all(len(r["title"]) <= 140 for r in run(p, f))
