"""Rôle : Parsers mobilité urbaine (Vel'oh, parkings, Chargy, aérien, chantiers VdL, vélo).
Entrées/Sorties : Reçoit des octets bruts (JSON/KML/GBFS) et produit des listes de dicts plats.
Hors-scope : Aucun appel réseau ; le rattachement commune/canton est fait en SQL (dbt silver).
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections.abc import Callable

from openlux.core.parsers import _f, _j, _utc, _x


def veloh_jcdecaux_v3(raw: bytes) -> list[dict]:
    """Parse l'API JCDecaux v3 (clé requise) : disponibilités + position par station."""
    out = []
    for s in _j(raw):
        av, pos = s.get("totalStands", {}).get("availabilities", {}), s.get("position", {})
        out.append(
            {
                "station_number": s.get("number"),
                "observed_at": _utc(s.get("lastUpdate")),
                "available_bikes": av.get("bikes"),
                "available_electrical_bikes": av.get("electricalBikes"),
                "available_mechanical_bikes": av.get("mechanicalBikes"),
                "available_stands": av.get("stands"),
                "disabled_bikes": None,
                "disabled_stands": None,
                "is_renting": s.get("status") == "OPEN" and bool(s.get("connected")),
                "lat": _f(pos.get("latitude")),
                "lon": _f(pos.get("longitude")),
            }
        )
    return out


def veloh_gbfs_status(raw: bytes) -> list[dict]:
    """Parse le GBFS v2 station_status (sans clé) ; nom/position viennent du seed officiel GBFS."""
    out = []
    for s in _j(raw).get("data", {}).get("stations", []):
        vt = {v["vehicle_type_id"]: v["count"] for v in s.get("vehicle_types_available", [])}
        out.append(
            {
                "station_number": int(s["station_id"]),
                "observed_at": _utc(s.get("last_reported")),
                "available_bikes": s.get("num_bikes_available"),
                "available_electrical_bikes": vt.get("electrical"),
                "available_mechanical_bikes": vt.get("mechanical"),
                "available_stands": s.get("num_docks_available"),
                "disabled_bikes": s.get("num_bikes_disabled"),
                "disabled_stands": s.get("num_docks_disabled"),
                "is_renting": bool(s.get("is_renting")),
                "lat": None,
                "lon": None,
            }
        )
    return out


def vdl_parking(raw: bytes) -> list[dict]:
    """Parse le feed temps réel des parkings de la Ville de Luxembourg."""
    d = _j(raw)
    obs = _utc(d.get("last_build_date"), "%a, %d %b %Y %H:%M:%S %z")
    return [
        {
            "parking_id": str(p.get("id", k)),
            "parking_name": p.get("titre"),
            "observed_at": obs,
            "available_spaces": p.get("actuel"),
            "total_capacity": p.get("total"),
            "trend": p.get("tendance"),
            "is_open": p.get("ouvert"),
            "is_full": p.get("complet"),
            "is_out_of_order": p.get("panne"),
            "pricing_policy": (p.get("paiement") or {}).get("politique_tarifaire"),
            "district": ((p.get("localisation") or {}).get("quartier") or {}).get("fr"),
            "lat": _f((p.get("localisation") or {}).get("latitude")),
            "lon": _f((p.get("localisation") or {}).get("longitude")),
        }
        for k, p in d.get("parking", {}).items()
    ]


_OUT_OF_SERVICE = ("OFFLINE", "FAULT", "UNAVAILABLE")


def chargy_kml(raw: bytes) -> list[dict]:
    """Parse le KML Chargy : état live de chaque connecteur agrégé par site de recharge."""
    out = []
    for pm in (e for e in ET.fromstring(raw).iter() if e.tag.endswith("Placemark")):
        cons = [
            c
            for d in pm.iter()
            if d.tag.endswith("Data") and d.attrib.get("name") == "chargingdevice"
            for c in json.loads(_x(d, "value") or "{}").get("connectors", [])
        ]
        lo, la = ((_x(pm, "coordinates") or ",").split(",") + [None])[:2]
        st = [c.get("description") for c in cons]
        out.append(
            {
                "site_name": _x(pm, "name"),
                "address": _x(pm, "address"),
                "connectors_total": len(cons),
                "connectors_available": st.count("AVAILABLE"),
                "connectors_charging": st.count("CHARGING"),
                "connectors_out_of_service": sum(s in _OUT_OF_SERVICE for s in st),
                "max_power_kw": max((_f(c.get("maxchspeed")) or 0 for c in cons), default=None),
                "lat": _f(la),
                "lon": _f(lo),
            }
        )
    return out


def opensky_states(raw: bytes) -> list[dict]:
    """Parse les vecteurs d'état OpenSky (bbox Luxembourg) ; positions inconnues ignorées."""
    d = _j(raw)
    return [
        {
            "icao24": s[0],
            "callsign": (s[1] or "").strip() or None,
            "origin_country": s[2],
            "observed_at": _utc(s[4] or d.get("time")),
            "baro_altitude_m": _f(s[7]),
            "on_ground": bool(s[8]),
            "velocity_ms": _f(s[9]),
            "lat": _f(s[6]),
            "lon": _f(s[5]),
        }
        for s in d.get("states") or []
        if s[5] is not None and s[6] is not None
    ]


def _centroid(g: dict) -> tuple[float | None, float | None]:
    pts = [p for ring in g.get("rings", []) for p in ring] or (
        [(g["x"], g["y"])] if "x" in g else []
    )
    if not pts:
        return None, None
    return sum(p[1] for p in pts) / len(pts), sum(p[0] for p in pts) / len(pts)


def vdl_roadworks(raw: bytes) -> list[dict]:
    """Parse les chantiers ArcGIS de la Ville de Luxembourg (couches 1 polygones / 5 points)."""
    out = []
    for f in _j(raw).get("features", []):
        a, (la, lo) = f.get("attributes", {}), _centroid(f.get("geometry") or {})
        out.append(
            {
                "work_id": str(a.get("ROAD_WORK_ID") or a.get("ID") or a.get("OBJECTID")),
                "authority": "Ville de Luxembourg",
                "road_name": a.get("STREET_TYPICAL_NAME_LIST") or a.get("ADDRESS"),
                "title": (a.get("OBJECTIVE") or a.get("DESCRIPTION") or "")[:140] or None,
                "contractor": a.get("ENTREPRISE_TRAVAUX") or a.get("CONTRACTOR"),
                "start_time_utc": _utc(a.get("START_DATE") or a.get("DATE_START")),
                "end_time_utc": _utc(a.get("END_DATE") or a.get("DATE_END")),
                "lat": round(la, 6) if la else None,
                "lon": round(lo, 6) if lo else None,
            }
        )
    return out


CITY_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    f.__name__: f
    for f in (
        veloh_jcdecaux_v3,
        veloh_gbfs_status,
        vdl_parking,
        chargy_kml,
        opensky_states,
        vdl_roadworks,
    )
}
