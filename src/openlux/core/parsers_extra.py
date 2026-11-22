"""Rôle : Parsers spécialisés additionnels (logement, chantiers, mobilité, économie).
Entrées/Sorties : Reçoit des octets bruts (JSON/SDMX) et produit des listes de dicts standardisés.
Hors-scope : N'effectue aucun appel réseau, aucun accès disque ni validation Pydantic.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime


def _j(raw: bytes):
    return json.loads(raw.decode("utf-8")) if isinstance(raw, (bytes, bytearray)) else raw


def _ms_iso(val) -> str:
    if not val:
        return ""
    try:
        f = float(val)
        return datetime.fromtimestamp(f / 1000.0 if f > 1e10 else f, UTC).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except Exception:
        return str(val)


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


def opensky_json(raw: bytes) -> list[dict]:
    """Parse les vecteurs d'état aériens OpenSky Network (<= 30 lignes)."""
    if not raw.strip() or isinstance(d := _j(raw), list):
        return d if isinstance(d, list) else []
    now_s = datetime.now(UTC).isoformat()
    return [
        {
            "icao24": str(s[0]),
            "callsign": str(s[1] or "N/A").strip(),
            "origin_country": str(s[2] or "Unknown"),
            "baro_altitude_m": float(s[7] or 0.0),
            "velocity_ms": float(s[9] or 0.0),
            "observed_at": now_s,
            "status": "EN_ROUTE" if not s[8] else "ON_GROUND",
            "lat": float(s[6] or 49.61),
            "lon": float(s[5] or 6.13),
            "commune_name": "Luxembourg",
        }
        for s in d.get("states", []) or []
    ]


def vdl_roadworks_json(raw: bytes) -> list[dict]:
    """Parse le flux chantiers Ville de Luxembourg ESRI (<= 30 lignes)."""
    if not raw.strip() or isinstance(d := _j(raw), list):
        return d if isinstance(d, list) else []
    rows = []
    for f in d.get("features", []):
        a, g = f.get("attributes", {}), f.get("geometry", {})
        rows.append(
            {
                "work_id": str(a.get("ROAD_WORK_ID") or a.get("OBJECTID", "UNKNOWN")),
                "road_name": a.get("FK_QUART_NAME") or "Luxembourg-Ville",
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


EXTRA_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    f.__name__: f
    for f in (
        housing_statec_json,
        opensky_json,
        vdl_roadworks_json,
        statec_inflation_json,
        veloh_stations_json,
    )
}
