"""Rôle : Parsers environnement & énergie (météo, air/pollen, eau, baignade, électricité).
Entrées/Sorties : Reçoit des octets bruts (JSON/CSV) et produit des listes de dicts plats.
Hors-scope : Aucun appel réseau ; une valeur absente reste None (jamais de valeur par défaut).
"""

from __future__ import annotations

import csv
import io
from collections.abc import Callable

from openlux.core.parsers import _f, _j, _utc

# POURQUOI : variables Open-Meteo -> colonnes Gold (pression ramenée au niveau de la mer = QFF)
_OM_WEATHER = {
    "temperature_2m": "temperature_c",
    "relative_humidity_2m": "humidity_pct",
    "pressure_msl": "pressure_hpa",
    "wind_speed_10m": "wind_speed_kmh",
    "precipitation": "precipitation_mm",
    "weather_code": "weather_code",
}


def openmeteo_weather(raw: bytes) -> list[dict]:
    """Parse la grille horaire Open-Meteo (modèle, multi-points) ; ignore les heures sans valeur."""
    locs, out = (d if isinstance(d := _j(raw), list) else [d]), []
    for idx, loc in enumerate(locs):
        h, la, lo = loc.get("hourly", {}), loc.get("latitude"), loc.get("longitude")
        for i, t in enumerate(h.get("time", [])):
            vals = {c: h[k][i] for k, c in _OM_WEATHER.items() if k in h}
            if vals.get("temperature_c") is None:
                continue
            out.append(
                {
                    "station_id": f"OM_{la:.3f}_{lo:.3f}",
                    "station_name": "Point de grille Open-Meteo",
                    "data_origin": "model",
                    # POURQUOI : réponse dans l'ordre des points demandés (seed ref_model_points)
                    "location_index": idx,
                    "observed_at": _utc(t, local=False),
                    **vals,
                    "lat": la,
                    "lon": lo,
                }
            )
    return out


def meteolux_hvd(raw: bytes) -> list[dict]:
    """Parse l'observation officielle MeteoLux (station Findel ELLX, CC0) en une ligne."""
    d = _j(raw)
    v = {x["id"]: x["value"] for x in d.get("data", [])}
    ws = _f(v.get("s2ff_rwymd0"))
    return [
        {
            "station_id": "ELLX",
            "station_name": "Luxembourg-Findel (MeteoLux)",
            "data_origin": "station",
            "observed_at": _utc(d.get("timestamp")),
            "temperature_c": _f(v.get("st")),
            "humidity_pct": _f(v.get("su")),
            "pressure_hpa": _f(v.get("spsl")),
            # POURQUOI : MeteoLux publie le vent en m/s, la Gold est en km/h
            "wind_speed_kmh": round(ws * 3.6, 1) if ws is not None else None,
            "precipitation_mm": _f(v.get("srr")),
            "weather_code": None,
            "lat": 49.63258,
            "lon": 6.23301,
        }
    ]


def openmeteo_long(raw: bytes) -> list[dict]:
    """Parse toute variable horaire Open-Meteo (air, pollen) en format long avec son unité."""
    locs, out = (d if isinstance(d := _j(raw), list) else [d]), []
    for idx, loc in enumerate(locs):
        h, units = loc.get("hourly", {}), loc.get("hourly_units", {})
        la, lo = loc.get("latitude"), loc.get("longitude")
        for var in (k for k in h if k != "time"):
            for t, val in zip(h["time"], h[var], strict=False):
                if val is not None:
                    out.append(
                        {
                            "station_id": f"OM_{la:.3f}_{lo:.3f}",
                            "observed_at": _utc(t, local=False),
                            "location_index": idx,
                            "pollutant": var,
                            "value": float(val),
                            "unit": units.get(var),
                            "lat": la,
                            "lon": lo,
                        }
                    )
    return out


def water_levels_csv(raw: bytes) -> list[dict]:
    """Parse l'export AGE inondations.public.lu (CSV large, 15 min, heure locale)."""
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    head, out = rows[0], []
    for r in rows[1:]:
        for ts, val in zip(head[3:], r[3:], strict=False):
            if (v := _f(val)) is not None:
                out.append(
                    {
                        "station_name": r[0].removeprefix("SN_"),
                        "observed_at": _utc(ts, "%d.%m.%Y %H:%M"),
                        "water_level": v,
                        "unit": r[2],
                    }
                )
    return out


def bathing_sites(raw: bytes) -> list[dict]:
    """Parse les sites de baignade (OGC API Features geoportail, collections 656 ou 581)."""
    out = []
    for f in _j(raw).get("features", []):
        p, (lo, la) = f.get("properties", {}), f["geometry"]["coordinates"][:2]
        oid = p.get("OBJECTID") or p.get("messstationen_GISADMIN_Badegewaesser_OBJECTID")
        q = p.get("wasserrahmenrichtlinie_GISADMIN_Badegewaesser_Ergebnisse_RESULT")
        out.append(
            {
                "site_id": str(oid),
                "site_name": p.get("NAME"),
                "bathing_status": p.get("Baignade"),
                "quality_class": q,
                "profile_url": p.get("Hyperlinks"),
                "lat": la,
                "lon": lo,
            }
        )
    return out


def energy_charts_price(raw: bytes) -> list[dict]:
    """Parse les prix spot day-ahead DE-LU (energy-charts.info, données SMARD/BNetzA)."""
    d = _j(raw)
    return [
        {"observed_at": _utc(t), "price_eur_per_mwh": _f(p), "bidding_zone": "DE-LU"}
        for t, p in zip(d.get("unix_seconds", []), d.get("price", []), strict=False)
        if p is not None
    ]


ENV_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    f.__name__: f
    for f in (
        openmeteo_weather,
        meteolux_hvd,
        openmeteo_long,
        water_levels_csv,
        bathing_sites,
        energy_charts_price,
    )
}
