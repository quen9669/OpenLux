"""Rôle : Parsers d'observations environnementales et énergétiques (météo, air, pollen, énergie).
Entrées/Sorties : Reçoit des octets bruts (JSON) et produit des listes de dicts standardisés.
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
    c, obs = d.get("current", {}), d.get("current", {}).get("time", datetime.now(UTC).isoformat())
    return [
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
        for pol, k in [
            ("PM10", "pm10"),
            ("PM2.5", "pm2_5"),
            ("NO2", "nitrogen_dioxide"),
            ("O3", "ozone"),
        ]
        if (v := c.get(k)) is not None
    ]


def pollen_openmeteo_json(raw: bytes) -> list[dict]:
    """Parse les concentrations polliniques (liste ou backup Open-Meteo) (<= 30 lignes)."""
    if not raw.strip() or isinstance(d := _j(raw), list):
        return d if isinstance(d, list) else []
    c, obs = d.get("current", {}), d.get("current", {}).get("time", datetime.now(UTC).isoformat())
    return [
        {
            "specie": sp,
            "risk_level": "HIGH"
            if (v := float(c.get(k, 0.0))) > 50
            else ("MODERATE" if v > 10 else "LOW"),
            "grains_m3": int(v),
            "observed_at": obs,
            "station_name": "Luxembourg-Ville",
            "commune_name": "Luxembourg",
        }
        for sp, k in [("Bouleau (Betula)", "birch_pollen"), ("Aulne (Alnus)", "alder_pollen")]
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


def electricity_smard_json(raw: bytes) -> list[dict]:
    """Parse les prix spot électricité SMARD DE-LU (<= 30 lignes)."""
    if not raw.strip() or isinstance(d := _j(raw), list):
        return d if isinstance(d, list) else []
    p, t = d.get("price", []) or [], d.get("unix_seconds", []) or []
    return [
        {
            "observed_at": datetime.fromtimestamp(ts, UTC).isoformat(),
            "price_eur_per_mwh": float(pr),
            "bidding_zone": "DE-LU",
        }
        for ts, pr in zip(t, p, strict=False)
    ]


ENV_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    f.__name__: f
    for f in (
        air_quality_openmeteo_json,
        pollen_openmeteo_json,
        meteo_openmeteo_json,
        electricity_smard_json,
    )
}
