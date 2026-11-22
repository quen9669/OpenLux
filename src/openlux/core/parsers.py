"""Rôle : Registre central de fonctions pures (sans I/O, <= 30 lignes) pour formats complexes.
Entrées/Sorties : Reçoit des octets bruts (XML, RSS, JSON) et produit des listes de dicts.
Hors-scope : N'effectue aucun appel réseau, aucun accès disque ni validation Pydantic.
"""

from __future__ import annotations

import csv
import io
import json
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import UTC
from email.utils import parsedate_to_datetime

from openlux.core.parsers_env import ENV_PARSERS
from openlux.core.parsers_extra import EXTRA_PARSERS

_KW = {
    "FR": re.compile(r"\b(sncf|ter|a31|lorraine|metz|france)\b"),
    "BE": re.compile(r"\b(sncb|belgique|e411|arlon)\b"),
    "DE": re.compile(r"\b(bahn|db|allemagne|trier)\b"),
}


def _tag(elem: ET.Element, suffix: str) -> ET.Element | None:
    return next((x for x in elem.iter() if x.tag.endswith(suffix)), None)


def _j(raw: bytes):
    return json.loads(raw.decode("utf-8")) if isinstance(raw, (bytes, bytearray)) else raw


def cita_datex2(raw: bytes) -> list[dict]:
    """Parse le flux XML DATEX II du CITA (trafic et chantiers) en dicts (<= 30 lignes)."""
    if not raw.strip():
        return []
    if raw.strip().startswith((b"[", b"{")):
        return d if isinstance((d := json.loads(raw.decode("utf-8"))), list) else [d]
    records = []
    for el in ET.fromstring(raw).iter():
        if el.tag.endswith("situationRecord"):
            rd, lat, lon = _tag(el, "roadName"), _tag(el, "latitude"), _tag(el, "longitude")
            tm = next((x for x in el.iter() if "CreationTime" in x.tag), None)
            st_t = next((x for x in el.iter() if x.tag.endswith("overallStartTime")), None)
            end_t = next((x for x in el.iter() if x.tag.endswith("overallEndTime")), None)
            rn = rd.text.strip() if rd is not None and rd.text else "A"
            st = el.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type", "situation")
            eid = el.attrib.get("id", "UNKNOWN")
            tm_s = tm.text.strip() if tm is not None and tm.text else ""
            st_s = st_t.text.strip() if st_t is not None and st_t.text else tm_s
            end_s = end_t.text.strip() if end_t is not None and end_t.text else None
            vs = val.text.strip() if (val := _tag(el, "value")) is not None and val.text else ""
            fla = float(lat.text.strip()) if lat is not None and lat.text else None
            flo = float(lon.text.strip()) if lon is not None and lon.text else None
            records.append(
                {
                    "event_id": eid,
                    "work_id": eid,
                    "road_name": rn,
                    "situation_type": st,
                    "impact_level": st,
                    "start_time": st_s,
                    "start_date": st_s,
                    "end_date": end_s,
                    "observed_at": tm_s,
                    "title": vs or "CITA",
                    "lat": fla,
                    "lon": flo,
                    "comment": vs,
                    "commune_name": "Luxembourg",
                }
            )
    return records


def strikes_rss(raw: bytes) -> list[dict]:
    """Parse et filtre les avis de grèves depuis un flux RSS (<= 30 lignes)."""
    kws = {"grève", "greve", "streik", "strike", "manifestation", "débrayage", "protest"}
    if not raw.strip():
        return []
    records = []
    for it in ET.fromstring(raw).iter("item"):
        t, lnk = (it.findtext("title") or "").strip(), (it.findtext("link") or "").strip()
        full = f"{t.lower()} {(it.findtext('description') or '').lower()}"
        if not any(k in full for k in kws):
            continue
        is_tr = any(w in full for w in ["cfl", "bus", "tram", "train", "vol", "sncf", "ter", "db"])
        cc = next((c for c, rx in _KW.items() if rx.search(full)), "LU")
        cn = {"FR": "France", "BE": "Belgique", "DE": "Allemagne"}.get(cc, "Luxembourg")
        records.append(
            {
                "strike_id": (it.findtext("guid") or lnk or t).strip(),
                "title": t[:140],
                "published_at": (it.findtext("pubDate") or "").strip(),
                "source_url": lnk,
                "sector": "TRANSPORT" if is_tr else "PUBLIC",
                "country_code": cc,
                "country_name": cn,
            }
        )
    return records


def vdl_parking(raw: bytes) -> list[dict]:
    """Parse le feed JSON des parkings VDL en liste d'équipements (<= 30 lignes)."""
    if not raw.strip() or isinstance(d := _j(raw), list):
        return d if isinstance(d, list) else []
    obs = d.get("last_build_date", "")
    if obs and (not obs[:4].isdigit() or len(obs) < 10):
        try:
            obs = parsedate_to_datetime(obs).astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    return [
        {
            "facility_id": f"PARKING_{p}",
            "facility_name": v.get("titre", f"P_{p}"),
            "available_spaces": int(v.get("actuel", 0) or 0),
            "total_capacity": int(v.get("total", 0) or 0),
            "lat": v.get("localisation", {}).get("latitude"),
            "lon": v.get("localisation", {}).get("longitude"),
            "observed_at": obs,
            "commune_name": "Luxembourg",
        }
        for p, v in d.get("parking", {}).items()
    ]


def fuel_prices_csv(raw: bytes) -> list[dict]:
    """Parse le CSV officiel des prix carburants du Ministère (<= 30 lignes)."""
    if not raw.strip() or raw.strip().startswith(b"["):
        return json.loads(raw.decode("utf-8")) if raw.strip().startswith(b"[") else []
    types = (
        "Essence_E10 Diesel_B7 Hydrogene LPG Electricie_Fournisseur Recharge_AC Recharge_DC".split()
    )
    records, text = [], raw.decode("utf-8", errors="replace").lstrip("\ufeff")
    _M = (
        "jan feb mar apr may jun jul aug sep oct nov dec janv fevr févr mars avri juin juil"
        " aout août sept".split()
    )
    _V = "01 02 03 04 05 06 07 08 09 10 11 12 01 02 02 03 04 06 07 08 08 09".split()
    m_map = dict(zip(_M, _V, strict=False))
    for r in csv.DictReader(io.StringIO(text)):
        dt = r.get("Intervalle", "").strip()
        if m := re.match(r"^([A-Za-z]{3,4})[-/ ]+(\d{2,4})$", dt):
            yr = f"20{m.group(2)}" if len(m.group(2)) == 2 else m.group(2)
            dt = f"{yr}-{m_map.get(m.group(1).lower()[:4], '01')}-01 00:00:00"
        for ft in types:
            if v := r.get(ft):
                try:
                    records.append(
                        {
                            "fuel_type": ft,
                            "price_eur_per_litre": float(v.replace(",", ".")),
                            "observed_at": dt,
                            "price_change_eur": 0.0,
                        }
                    )
                except ValueError:
                    pass
    return records


PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    "cita_datex2": cita_datex2,
    "strikes_rss": strikes_rss,
    "vdl_parking": vdl_parking,
    "fuel_prices_csv": fuel_prices_csv,
    **EXTRA_PARSERS,
    **ENV_PARSERS,
}
