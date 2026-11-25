"""Rôle : Helpers communs + parsers trafic & transports (DATEX II, Autobahn, SIRI, bus VdL).
Entrées/Sorties : Reçoit des octets bruts (XML/JSON) et produit des listes de dicts plats.
Hors-scope : Aucun appel réseau, aucun accès disque, aucune valeur inventée (champ absent = None).
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import UTC, datetime
from functools import partial
from zoneinfo import ZoneInfo

_LU_TZ = ZoneInfo("Europe/Luxembourg")
_XSI = "{http://www.w3.org/2001/XMLSchema-instance}type"


def _j(raw: bytes):
    return json.loads(raw.decode("utf-8-sig"))


def _utc(val, fmt: str | None = None, local: bool = True) -> str | None:
    """Normalise ISO, epoch (s/ms) ou date locale (fmt) en ISO-8601 UTC ; None si illisible."""
    if val in (None, ""):
        return None
    try:
        if isinstance(val, int | float) or str(val).isdigit():
            f = float(val)
            return datetime.fromtimestamp(f / 1000 if f > 1e11 else f, UTC).isoformat()
        s = str(val).strip()
        d = datetime.strptime(s, fmt) if fmt else datetime.fromisoformat(s.replace("Z", "+00:00"))
        # POURQUOI : les flux luxembourgeois sans fuseau sont en heure locale (CET/CEST)
        d = d if d.tzinfo else d.replace(tzinfo=_LU_TZ if local else UTC)
        return d.astimezone(UTC).isoformat()
    except (ValueError, OverflowError, OSError):
        return None


def _f(v) -> float | None:
    try:
        return float(str(v).replace(",", ".")) if v not in (None, "") else None
    except ValueError:
        return None


def _x(el: ET.Element, suffix: str) -> str | None:
    """Texte du premier descendant dont le tag finit par `suffix` (indépendant du namespace)."""
    n = next((e for e in el.iter() if e.tag.split("}")[-1] == suffix and e.text), None)
    return n.text.strip() if n is not None else None


def _texts(el: ET.Element) -> list[str]:
    return [t for e in el.iter() if e.tag.endswith("}value") and (t := (e.text or "").strip())]


def _datex_road(rec: ET.Element) -> str | None:
    if road := _x(rec, "roadNumber"):
        return road
    for nm in (e for e in rec.iter() if e.tag.endswith("}name")):
        if _x(nm, "tpegOtherPointDescriptorType") == "linkName":
            return _x(nm, "value")
    return None


def _datex_rec(rec: ET.Element, country: str) -> dict:
    vals = [v for c in rec.iter() if c.tag.endswith("generalPublicComment") for v in _texts(c)]
    vals = [v for v in dict.fromkeys(vals) if v]
    sub = next((c.text for c in rec if c.tag.endswith("Type") and c.text), None)
    return {
        "event_id": rec.attrib.get("id"),
        "country_code": country,
        "road_name": _datex_road(rec),
        "situation_type": rec.attrib.get(_XSI, "").split(":")[-1],
        "situation_subtype": sub,
        "validity_status": _x(rec, "validityStatus"),
        "start_time_utc": _utc(_x(rec, "overallStartTime")),
        "end_time_utc": _utc(_x(rec, "overallEndTime")),
        "observed_at": _utc(_x(rec, "situationRecordVersionTime")),
        "description": " | ".join(vals)[:300] or None,
        "lat": _f(_x(rec, "latitude")),
        "lon": _f(_x(rec, "longitude")),
    }


def datex2_situations(raw: bytes, country: str = "LU", bbox: tuple | None = None) -> list[dict]:
    """Parse une publication DATEX II v2/v3 (situationRecord), filtrée optionnellement par bbox."""
    recs = [_datex_rec(e, country) for e in ET.fromstring(raw).iter() if e.tag.endswith("Record")]
    recs = [r for r in recs if r["event_id"] and (r["lat"] is not None or not bbox)]
    if bbox:
        la0, lo0, la1, lo1 = bbox
        recs = [r for r in recs if la0 <= r["lat"] <= la1 and lo0 <= r["lon"] <= lo1]
    return recs


def autobahn_events(raw: bytes, bbox: tuple = (49.3, 6.0, 50.1, 7.2)) -> list[dict]:
    """Parse l'API Autobahn GmbH (warning/closure/roadworks) autour de la frontière LU."""
    d, out = _j(raw), []
    for svc, items in d.items():
        for it in items or []:
            la, lo = _f(it["coordinate"]["lat"]), _f(it["coordinate"]["long"])
            if la is None or not (bbox[0] <= la <= bbox[2] and bbox[1] <= lo <= bbox[3]):
                continue
            out.append(
                {
                    "event_id": it.get("identifier"),
                    "country_code": "DE",
                    "road_name": (it.get("title") or "").split("|")[0].strip() or None,
                    "situation_type": it.get("display_type") or svc,
                    "situation_subtype": it.get("abnormalTrafficType"),
                    "validity_status": "planned" if it.get("future") else "active",
                    "start_time_utc": _utc(it.get("startTimestamp")),
                    "end_time_utc": None,
                    "observed_at": _utc(it.get("startTimestamp")),
                    "description": f"{it.get('title', '')} ({(it.get('subtitle') or '').strip()})",
                    "lat": la,
                    "lon": lo,
                }
            )
    return out


def vdl_traffic_info(raw: bytes) -> list[dict]:
    """Parse les infos trafic ArcGIS de la Ville de Luxembourg (couche TRAFIC_INFO/0)."""
    out = []
    for ft in _j(raw).get("features", []):
        a, g = ft.get("attributes", {}), ft.get("geometry") or {}
        out.append(
            {
                "event_id": f"VDL-{a.get('TRAF_INFO_ID') or a.get('OBJECTID')}",
                "country_code": "LU",
                "road_name": a.get("STREET_TYPICAL_NAME"),
                "situation_type": a.get("INFO_TYPE_LABEL"),
                "situation_subtype": None,
                "validity_status": None,
                "start_time_utc": _utc(a.get("START_DATE")),
                "end_time_utc": _utc(a.get("END_DATE")),
                "observed_at": _utc(a.get("PUBLICATION_DATE")),
                "description": (a.get("OBJECTIVE") or "")[:300] or None,
                "lat": _f(g.get("y")),
                "lon": _f(g.get("x")),
            }
        )
    return out


# POURQUOI : bbox Lorraine nord (Metz–Thionville–frontière) pour ne garder que l'A31/A30 utile
_FR_BBOX = (48.85, 5.6, 49.6, 6.7)

TRAFFIC_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    "datex2_lu": datex2_situations,
    "datex2_fr_lorraine": partial(datex2_situations, country="FR", bbox=_FR_BBOX),
    "autobahn_events": autobahn_events,
    "vdl_traffic_info": vdl_traffic_info,
}
