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


def air_quality_openmeteo_json(raw: bytes) -> list[dict]:
    """Parse la qualité de l'air Open-Meteo temps réel et historique (<= 30 lignes)."""
    if not raw.strip():
        return []
    items = _j(raw) if isinstance(_j(raw), list) else [_j(raw)]
    if items and "station_id" in items[0]:
        return items
    res, pols = (
        [],
        [("PM10", "pm10"), ("PM2.5", "pm2_5"), ("NO2", "nitrogen_dioxide"), ("O3", "ozone")],
    )
    for loc in items:
        lat, lon = float(loc.get("latitude", 49.61)), float(loc.get("longitude", 6.13))
        comm = _commune_for(lat, lon)
        c, h = loc.get("current", {}), loc.get("hourly", {})
        times = h.get("time", []) or [c.get("time", datetime.now(UTC).isoformat())]
        for i, obs in enumerate(times):
            for p, k in pols:
                vals = h.get(k)
                raw_v = vals[i] if vals and i < len(vals) else c.get(k)
                if raw_v is not None:
                    v = float(raw_v)
                    res.append(
                        {
                            "station_id": f"LU_AQ_{comm.upper()}",
                            "station_name": f"Air {comm}",
                            "commune_lau": comm,
                            "lat": lat,
                            "lon": lon,
                            "observed_at": obs,
                            "pollutant": p,
                            "value": v,
                            "unit": "ug/m3",
                            "aqi_index": "GOOD" if v < 50 else "MODERATE",
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
    for loc in items:
        lat, lon = float(loc.get("latitude", 49.61)), float(loc.get("longitude", 6.13))
        comm, c, h = _commune_for(lat, lon), loc.get("current", {}), loc.get("hourly", {})
        times = h.get("time", []) or [c.get("time", "")]
        t_s, p_s = h.get("temperature_2m", []), h.get("precipitation", [])
        w_s, rh_s = h.get("wind_speed_10m", []), h.get("relative_humidity_2m", [])
        pr_s, wc_s = h.get("surface_pressure", []), h.get("weather_code", [])
        for i, obs in enumerate(times):
            t = float(t_s[i] if t_s and i < len(t_s) else c.get("temperature_2m", 0.0))
            p = float(p_s[i] if p_s and i < len(p_s) else c.get("precipitation", 0.0))
            w = float(w_s[i] if w_s and i < len(w_s) else c.get("wind_speed_10m", 0.0))
            rh = float(rh_s[i] if rh_s and i < len(rh_s) else c.get("relative_humidity_2m", 80.0))
            pr = float(pr_s[i] if pr_s and i < len(pr_s) else c.get("surface_pressure", 1013.2))
            wc = int(wc_s[i] if wc_s and i < len(wc_s) else c.get("weather_code", 0))
            cond = "Rain" if p > 0.5 or wc >= 50 else ("Clear" if wc in (0, 1) else "Clouds")
            res.append(
                {
                    "station_id": f"LU_METEO_{comm.upper()}",
                    "station_name": f"Station {comm}",
                    "timestamp": obs,
                    "temperature": t,
                    "humidity": rh,
                    "pressure_hpa": pr,
                    "wind_speed_kmh": w,
                    "precipitation_mm": p,
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


ENV_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    f.__name__: f
    for f in (
        air_quality_openmeteo_json,
        pollen_openmeteo_json,
        meteo_openmeteo_json,
        electricity_smard_json,
    )
}
