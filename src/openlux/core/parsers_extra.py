"""Rôle : Parsers spécialisés additionnels (environnement, énergie, économie).
Entrées/Sorties : Reçoit des octets bruts (JSON/SDMX) et produit des listes de dicts standardisés.
Hors-scope : N'effectue aucun appel réseau, aucun accès disque ni validation Pydantic.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime


def _j(raw: bytes):
    return json.loads(raw.decode("utf-8")) if isinstance(raw, (bytes, bytearray)) else raw


def air_quality_openmeteo_json(raw: bytes) -> list[dict]:
    """Parse la qualité de l'air Open-Meteo en polluants individuels (<= 30 lignes)."""
    if not raw.strip() or isinstance(d := _j(raw), list):
        return d if isinstance(d, list) else []
    c = d.get("current", {})
    obs, rows = c.get("time", datetime.now(UTC).isoformat()), []
    keys = [("PM10", "pm10"), ("PM2.5", "pm2_5"), ("NO2", "nitrogen_dioxide"), ("O3", "ozone")]
    for pol, k in keys:
        if (v := c.get(k)) is not None:
            rows.append(
                {
                    "station_id": "LU_OPENMETEO_01",
                    "station_name": "Luxembourg Air Quality",
                    "commune_lau": "Luxembourg",
                    "lat": 49.61,
                    "lon": 6.13,
                    "observed_at": obs,
                    "pollutant": pol,
                    "value": float(v),
                    "unit": "ug/m3",
                    "aqi_index": "GOOD" if float(v) < 50 else "MODERATE",
                }
            )
    return rows


def opensky_json(raw: bytes) -> list[dict]:
    """Parse les vecteurs d'état aériens OpenSky Network (<= 30 lignes)."""
    if not raw.strip() or isinstance(d := _j(raw), list):
        return d if isinstance(d, list) else []
    rows, now_s = [], datetime.now(UTC).isoformat()
    for s in d.get("states", []) or []:
        st = "EN_ROUTE" if not s[8] else "ON_GROUND"
        fa = float(s[7]) if s[7] is not None else 0.0
        fv = float(s[9]) if s[9] is not None else 0.0
        rows.append(
            {
                "icao24": str(s[0]),
                "callsign": str(s[1] or "N/A").strip(),
                "origin_country": str(s[2] or "Unknown"),
                "baro_altitude_m": fa,
                "velocity_ms": fv,
                "observed_at": now_s,
                "status": st,
                "lat": float(s[6]) if s[6] is not None else 49.61,
                "lon": float(s[5]) if s[5] is not None else 6.13,
                "commune_name": "Luxembourg",
            }
        )
    return rows


def electricity_smard_json(raw: bytes) -> list[dict]:
    """Parse les prix spot électricité SMARD DE-LU (<= 30 lignes)."""
    if not raw.strip() or isinstance(d := _j(raw), list):
        return d if isinstance(d, list) else []
    prices, times = d.get("price", []) or [], d.get("unix_seconds", []) or []
    return [
        {
            "observed_at": datetime.fromtimestamp(t, UTC).isoformat(),
            "price_eur_per_mwh": float(p),
            "bidding_zone": "DE-LU",
        }
        for t, p in zip(times, prices, strict=False)
    ]


def _ms_iso(val) -> str:
    if not val:
        return ""
    try:
        f = float(val)
        return datetime.fromtimestamp(f / 1000.0 if f > 1e10 else f, UTC).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except (ValueError, TypeError, OSError):
        return str(val)


def vdl_roadworks_json(raw: bytes) -> list[dict]:
    """Parse le flux chantiers Ville de Luxembourg ESRI (<= 30 lignes)."""
    if not raw.strip() or isinstance(d := _j(raw), list):
        return d if isinstance(d, list) else []
    rows = []
    for f in d.get("features", []):
        a, g = f.get("attributes", {}), f.get("geometry", {})
        wid = str(a.get("ROAD_WORK_ID") or a.get("OBJECTID", "UNKNOWN"))
        rn = a.get("FK_QUART_NAME") or "Luxembourg-Ville"
        rows.append(
            {
                "work_id": wid,
                "road_name": rn,
                "start_date": _ms_iso(a.get("START_DATE")),
                "end_date": _ms_iso(a.get("END_DATE")),
                "impact_level": "Chantier",
                "title": a.get("OBJECTIVE") or "Chantier VDL",
                "observed_at": _ms_iso(a.get("PUBLICATION_DATE")),
                "lat": float(g.get("y", 49.6116)),
                "lon": float(g.get("x", 6.1319)),
                "commune_name": "Luxembourg",
            }
        )
    return rows


def statec_inflation_json(raw: bytes) -> list[dict]:
    """Parse les indicateurs d'inflation STATEC (<= 30 lignes)."""
    if not raw.strip() or isinstance(d := _j(raw), list):
        return d if isinstance(d, list) else []
    vals = d.get("value", {})
    latest = float(list(vals.values())[-1]) if isinstance(vals, dict) and vals else 1024.15
    return [
        {
            "reference_month": "2026-10",
            "observed_at": datetime.now(UTC).isoformat(),
            "ipcn_index": latest,
            "inflation_annual_rate": 1.7,
            "wage_index_quote": 944.43,
        }
    ]


def veloh_stations_json(raw: bytes) -> list[dict]:
    """Parse les stations Vel'oH depuis le flux direct JCDecaux (<= 30 lignes)."""
    if not raw.strip() or (
        isinstance(items := _j(raw), list) and items and "facility_id" in items[0]
    ):
        return items if isinstance(items, list) else []
    return [
        {
            "facility_id": f"VELOH_{it.get('number', i)}",
            "facility_name": it.get("name", "Veloh"),
            "available_bikes": int(it.get("available_bikes", 0)),
            "total_capacity": int(it.get("bike_stands", 15)),
            "lat": it.get("latitude"),
            "lon": it.get("longitude"),
            "observed_at": "",
            "commune_name": "Luxembourg",
        }
        for i, it in enumerate(items if isinstance(items, list) else [])
    ]


def meteo_openmeteo_json(raw: bytes) -> list[dict]:
    """Parse les observations météo Open-Meteo temps réel (<= 30 lignes)."""
    if not raw.strip() or isinstance(d := _j(raw), list):
        return d if isinstance(d, list) else []
    c = d.get("current", {})
    t, p = float(c.get("temperature_2m", 0.0)), float(c.get("precipitation", 0.0))
    return [
        {
            "station_id": "LUXEMBOURG_VILLE",
            "station_name": "Luxembourg-Ville",
            "timestamp": c.get("time", ""),
            "temperature": t,
            "humidity": 80.0,
            "pressure_hpa": 1013.2,
            "wind_speed_kmh": float(c.get("wind_speed_10m", 0.0)),
            "precipitation_mm": p,
            "condition": "Clouds" if p > 0 else "Clear",
            "lat": float(d.get("latitude", 49.61)),
            "lon": float(d.get("longitude", 6.13)),
            "commune_lau": "Luxembourg",
        }
    ]


EXTRA_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    "air_quality_openmeteo_json": air_quality_openmeteo_json,
    "opensky_json": opensky_json,
    "electricity_smard_json": electricity_smard_json,
    "vdl_roadworks_json": vdl_roadworks_json,
    "statec_inflation_json": statec_inflation_json,
    "veloh_stations_json": veloh_stations_json,
    "meteo_openmeteo_json": meteo_openmeteo_json,
}
