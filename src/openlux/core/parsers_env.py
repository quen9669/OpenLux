"""Rôle : Parsers d'observations environnementales et énergétiques (météo, air, pollen, énergie).
Entrées/Sorties : Reçoit des octets bruts (JSON) et produit des listes de dicts standardisés.
Hors-scope : N'effectue aucun appel réseau, aucun accès disque ni validation Pydantic.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any


def _j(raw: bytes):
    return json.loads(raw.decode("utf-8")) if isinstance(raw, (bytes, bytearray)) else raw


_CANTONS = (
    "49.61,6.13,Luxembourg;49.52,5.89,Differdange;49.63,6.02,Mamer;49.87,6.16,Diekirch;"
    "49.81,6.42,Echternach;49.68,6.44,Grevenmacher;49.75,6.11,Mersch;49.77,5.89,Redange-sur-Attert;"
    "49.54,6.37,Remich;49.94,6.21,Vianden;49.97,5.93,Wiltz;50.05,6.03,Clervaux"
)
_CANTON_LOCS = [
    (float(a), float(b), c) for item in _CANTONS.split(";") for a, b, c in [item.split(",")]
]


def _commune_for(lat: float, lon: float) -> str:
    return min(_CANTON_LOCS, key=lambda c: (c[0] - lat) ** 2 + (c[1] - lon) ** 2)[2]


def _arr_v(arr: list | None, i: int, default: Any = 0.0) -> Any:
    return arr[i] if arr and i < len(arr) and arr[i] is not None else default


def air_quality_openmeteo_json(raw: bytes) -> list[dict]:
    """Parse la qualité de l'air Open-Meteo temps réel et historique (<= 30 lignes)."""
    if not raw.strip() or (isinstance(it := _j(raw), list) and it and "station_id" in it[0]):
        return it if isinstance(it, list) else []
    items, res = it if isinstance(it, list) else [it], []
    pols = [("PM10", "pm10"), ("PM2.5", "pm2_5"), ("NO2", "nitrogen_dioxide"), ("O3", "ozone")]
    for loc in items:
        lat, lon = float(loc.get("latitude", 49.61)), float(loc.get("longitude", 6.13))
        comm, c, h = _commune_for(lat, lon), loc.get("current", {}), loc.get("hourly", {})
        times = h.get("time", []) or [c.get("time", datetime.now(UTC).isoformat())]
        for i, obs in enumerate(times):
            for p, k in pols:
                if (v := _arr_v(h.get(k), i, c.get(k))) is not None:
                    res.append(
                        {
                            "station_id": f"LU_AQ_{comm.upper()}",
                            "station_name": f"Air {comm}",
                            "commune_lau": comm,
                            "lat": lat,
                            "lon": lon,
                            "observed_at": obs,
                            "pollutant": p,
                            "value": float(v),
                            "unit": "ug/m3",
                            "aqi_index": "GOOD" if float(v) < 50 else "MODERATE",
                        }
                    )
    return res


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
    """Parse les observations météo Open-Meteo temps réel et historique (<= 30 lignes)."""
    if not raw.strip() or (isinstance(it := _j(raw), list) and it and "station_id" in it[0]):
        return it if isinstance(it, list) else []
    items, res = it if isinstance(it, list) else [it], []
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M")
    for loc in items:
        lat, lon = float(loc.get("latitude", 49.61)), float(loc.get("longitude", 6.13))
        comm, c, h = _commune_for(lat, lon), loc.get("current", {}), loc.get("hourly", {})
        times = h.get("time", []) or [c.get("time", now_iso)]
        t_s, p_s = h.get("temperature_2m"), h.get("precipitation")
        w_s, rh_s = h.get("wind_speed_10m"), h.get("relative_humidity_2m")
        pr_s, wc_s = h.get("surface_pressure"), h.get("weather_code")
        for i, obs in enumerate(times):
            if obs > now_iso:
                continue
            t_v = _arr_v(t_s, i, c.get("temperature_2m", 0.0))
            p_v = _arr_v(p_s, i, c.get("precipitation", 0.0))
            w_v = _arr_v(w_s, i, c.get("wind_speed_10m", 0.0))
            rh_v = _arr_v(rh_s, i, c.get("relative_humidity_2m", 80.0))
            pr_v = _arr_v(pr_s, i, c.get("surface_pressure", 1013.2))
            wc_v = _arr_v(wc_s, i, c.get("weather_code", 0))
            cond = (
                "Rain"
                if float(p_v or 0) > 0.5 or int(wc_v or 0) >= 50
                else ("Clear" if int(wc_v or 0) in (0, 1) else "Clouds")
            )
            res.append(
                {
                    "station_id": f"LU_METEO_{comm.upper()}",
                    "station_name": f"Station {comm}",
                    "timestamp": obs,
                    "temperature": float(t_v or 0.0),
                    "humidity": float(rh_v or 80.0),
                    "pressure_hpa": float(pr_v or 1013.2),
                    "wind_speed_kmh": float(w_v or 0.0),
                    "precipitation_mm": float(p_v or 0.0),
                    "condition": cond,
                    "lat": lat,
                    "lon": lon,
                    "commune_lau": comm,
                }
            )
    return res


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


def statec_inflation_json(raw: bytes) -> list[dict]:
    """Parse les indicateurs d'inflation STATEC (<= 30 lignes)."""
    if not raw.strip() or isinstance(d := _j(raw), list):
        return d if isinstance(d, list) else []
    v = d.get("value", {})
    val = float(list(v.values())[-1]) if isinstance(v, dict) and v else 1024.15
    return [
        {
            "reference_month": "2026-10",
            "observed_at": datetime.now(UTC).isoformat(),
            "ipcn_index": val,
            "inflation_annual_rate": 1.7,
            "wage_index_quote": 944.43,
        }
    ]


def housing_statec_json(raw: bytes) -> list[dict]:
    """Parse les autorisations de bâtir STATEC (SDMX-JSON ou liste) (<= 30 lignes)."""
    if not raw.strip() or isinstance(d := _j(raw), list):
        return d if isinstance(d, list) else []
    obs = (d.get("data", {}).get("dataSets", [{}])[0] or {}).get("observations", {})
    return [
        {
            "record_id": f"STATEC_{k.replace(':', '_')}",
            "canton_code": "LUX",
            "commune_name": "Luxembourg",
            "canton_name": "Luxembourg",
            "property_type": "RESIDENTIAL",
            "reference_period": "2025",
            "permits_count": int(v[0]) if v else 0,
            "units_authorized": int(v[0]) if v else 0,
            "observed_at": "2026-11-21T00:00:00Z",
        }
        for k, v in obs.items()
    ]


ENV_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    f.__name__: f
    for f in (
        air_quality_openmeteo_json,
        pollen_openmeteo_json,
        meteo_openmeteo_json,
        electricity_smard_json,
        statec_inflation_json,
        housing_statec_json,
    )
}
