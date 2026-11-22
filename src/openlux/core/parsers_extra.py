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
    now_s = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    return [
        {
            "work_id": str(a.get("ROAD_WORK_ID") or a.get("OBJECTID", "UNKNOWN")),
            "road_name": a.get("STREET_TYPICAL_NAME_LIST")
            or a.get("FK_QUART_NAME")
            or "Luxembourg-Ville",
            "start_date": _ms_iso(a.get("START_DATE")),
            "end_date": _ms_iso(a.get("END_DATE")),
            "impact_level": a.get("ENTREPRISE_TRAVAUX") or "Chantier",
            "title": a.get("OBJECTIVE") or "Chantier VDL",
            "observed_at": _ms_iso(a.get("PUBLICATION_DATE")) or now_s,
            "lat": round(sum(p[1] for p in pts) / len(pts), 5)
            if (pts := (f.get("geometry", {}).get("rings", [[]])[0]))
            else float(f.get("geometry", {}).get("y", 49.6116)),
            "lon": round(sum(p[0] for p in pts) / len(pts), 5)
            if pts
            else float(f.get("geometry", {}).get("x", 6.1319)),
            "commune_name": "Luxembourg",
        }
        for f in d.get("features", [])
        if (a := f.get("attributes", {})) is not None
    ]


_COM = {
    "Walferdange": ("walferdange", "bereler"),
    "Mamer": ("mamer", "capellen", "holzem"),
    "Strassen": ("strassen", "stroossen", "pescher"),
    "Bertrange": ("bertrange", "bartreng", "bourmicht"),
    "Hesperange": ("hesperange", "fentange", "itzig", "howald"),
    "Leudelange": ("leudelange", "edeleck", "foyer"),
    "Niederanven": ("niederanven", "senningerberg", "schommesch"),
}


def _veloh_commune(name: str, addr: str, lat: float | None, lon: float | None) -> str:
    t = f"{name} {addr}".lower()
    for c, kws in _COM.items():
        if any(k in t for k in kws):
            return c
    if lat and lat > 49.65:
        return "Walferdange"
    if lon and lon < 6.04:
        return "Mamer"
    if lon and lon > 6.22:
        return "Niederanven"
    if lon and lon < 6.08 and lat and lat < 49.62:
        return "Bertrange"
    if lon and lon < 6.09 and lat and lat >= 49.62:
        return "Strassen"
    if lat and lat < 49.58 and lon and lon >= 6.13:
        return "Hesperange"
    return "Leudelange" if (lat and lat < 49.57 and lon and lon < 6.1) else "Luxembourg"


def _veloh_item(it: dict, i: int) -> dict:
    raw_id = it.get("facility_id") or it.get("station_id") or it.get("number") or i
    num = it.get("number") or it.get("station_number") or i
    pos, ts = it.get("position") or {}, it.get("totalStands") or {}
    la = pos.get("latitude", it.get("latitude", it.get("lat")))
    lo = pos.get("longitude", it.get("longitude", it.get("lon")))
    av = ts.get("availabilities") or {}
    cap = int(ts.get("capacity", it.get("bike_stands", it.get("total_capacity", 15))))
    bk = int(av.get("bikes", it.get("available_bikes", it.get("num_bikes_available", 0))))
    st = int(
        av.get(
            "stands",
            it.get(
                "available_bike_stands",
                it.get("available_stands", it.get("num_docks_available", 0)),
            ),
        )
    )
    stat = it.get("status", "OPEN" if it.get("is_renting", True) else "CLOSED")
    conn, nm = (
        bool(it.get("connected", it.get("is_installed", True))),
        it.get("name", it.get("facility_name", f"Veloh {num}")),
    )
    fla, flo = (float(la) if la is not None else None), (float(lo) if lo is not None else None)
    elec = int(av.get("electricalBikes", it.get("available_electrical_bikes", bk)))
    mech = int(av.get("mechanicalBikes", it.get("available_mechanical_bikes", 0)))
    obs = it.get("lastUpdate") or it.get("observed_at") or _ms_iso(it.get("last_update")) or ""
    comm = it.get("commune_name") or _veloh_commune(nm, it.get("address", ""), fla, flo)
    broken = int(it.get("broken_stands", max(0, cap - (bk + st))))
    return {
        "facility_id": raw_id if str(raw_id).startswith("VELOH_") else f"VELOH_{raw_id}",
        "station_number": int(num) if str(num).isdigit() else i,
        "facility_name": nm,
        "address": it.get("address", ""),
        "available_bikes": bk,
        "available_electrical_bikes": elec,
        "available_mechanical_bikes": mech,
        "available_stands": st,
        "broken_stands": broken,
        "total_capacity": cap,
        "status": stat,
        "is_connected": conn,
        "is_installed": stat != "CLOSED",
        "is_renting": stat == "OPEN" and conn,
        "has_banking": bool(it.get("banking", it.get("has_banking", False))),
        "is_bonus": bool(it.get("bonus", it.get("is_bonus", False))),
        "lat": fla,
        "lon": flo,
        "observed_at": obs,
        "commune_name": comm,
    }


def veloh_stations_json(raw: bytes) -> list[dict]:
    """Parse les stations Vel'oH depuis JCDecaux v3/v1 ou GBFS (<= 30 lignes)."""
    if not raw.strip():
        return []
    data = _j(raw)
    items = (
        data.get("data", {}).get("stations", [])
        if isinstance(data, dict)
        else (data if isinstance(data, list) else [])
    )
    if (
        items
        and isinstance(items[0], dict)
        and "facility_id" in items[0]
        and "available_electrical_bikes" in items[0]
    ):
        return items
    return [_veloh_item(it, i) for i, it in enumerate(items) if isinstance(it, dict)]


EXTRA_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    f.__name__: f
    for f in (
        opensky_json,
        vdl_roadworks_json,
        veloh_stations_json,
    )
}
