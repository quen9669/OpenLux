"""Rôle : Registre de fonctions pures (sans I/O, <= 30 lignes) pour formats structurés complexes.
Entrées/Sorties : Reçoit des octets bruts (XML, RSS, iCal) et produit une liste de dictionnaires.
Hors-scope : N'effectue aucun appel réseau, aucun accès disque ni validation Pydantic.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Callable

_FR_KW = re.compile(r"\b(sncf|ter|a31|lorraine|metz|thionville|france)\b")
_BE_KW = re.compile(r"\b(sncb|belgique|e411|arlon|bruxelles|wallonie)\b")
_DE_KW = re.compile(r"\b(bahn|db|allemagne|trier|saarbrücken)\b")


def cita_datex2(raw: bytes) -> list[dict]:
    """Parse le flux XML DATEX II du CITA en événements autoroutiers atomiques (<= 30 lignes)."""
    # POURQUOI : Parsing pur sans I/O via ElementTree natif et résistant aux namespaces XML.
    records: list[dict] = []
    if not raw.strip():
        return records
    root = ET.fromstring(raw)
    for elem in root.iter():
        if elem.tag.endswith("situationRecord"):
            rec_id = elem.attrib.get("id") or "UNKNOWN"
            road_el = next((e for e in elem.iter() if e.tag.endswith("roadName")), None)
            lat_el = next((e for e in elem.iter() if e.tag.endswith("latitude")), None)
            lon_el = next((e for e in elem.iter() if e.tag.endswith("longitude")), None)
            time_el = next((e for e in elem.iter() if "CreationTime" in e.tag), None)
            val_el = next((e for e in elem.iter() if e.tag.endswith("value")), None)
            r_name = road_el.text.strip() if road_el is not None and road_el.text else "A"
            s_type = elem.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type", "situation")
            s_time = time_el.text.strip() if time_el is not None and time_el.text else ""
            r_lat = float(lat_el.text.strip()) if lat_el is not None and lat_el.text else None
            r_lon = float(lon_el.text.strip()) if lon_el is not None and lon_el.text else None
            r_comm = val_el.text.strip() if val_el is not None and val_el.text else ""
            records.append(
                {
                    "event_id": rec_id,
                    "road_name": r_name,
                    "situation_type": s_type,
                    "start_time": s_time,
                    "lat": r_lat,
                    "lon": r_lon,
                    "comment": r_comm,
                }
            )
    return records


def strikes_rss(raw: bytes) -> list[dict]:
    """Parse et filtre les avis de grèves et manifestations depuis un flux RSS (<= 30 lignes)."""
    # POURQUOI : Filtrage sans I/O garantissant Zero-PII et identification du pays (LU/FR/BE/DE).
    kws = {"grève", "greve", "streik", "strike", "manifestation", "débrayage", "protest"}
    records: list[dict] = []
    if not raw.strip():
        return records
    for item in ET.fromstring(raw).iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or link or title).strip()
        full = f"{title.lower()} {(item.findtext('description') or '').lower()}"
        if any(kw in full for kw in kws):
            is_tr = any(
                w in full for w in ["cfl", "bus", "tram", "train", "vol", "sncf", "ter", "db"]
            )
            cc, cn = "LU", "Luxembourg"
            if _FR_KW.search(full):
                cc, cn = "FR", "France"
            elif _BE_KW.search(full):
                cc, cn = "BE", "Belgique"
            elif _DE_KW.search(full):
                cc, cn = "DE", "Allemagne"
            records.append(
                {
                    "strike_id": guid,
                    "title": title[:140],
                    "published_at": (item.findtext("pubDate") or "").strip(),
                    "source_url": link,
                    "sector": "TRANSPORT" if is_tr else "PUBLIC",
                    "country_code": cc,
                    "country_name": cn,
                }
            )
    return records


PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    "cita_datex2": cita_datex2,
    "strikes_rss": strikes_rss,
}
