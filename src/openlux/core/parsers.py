"""Rôle : Registre de fonctions pures (sans I/O, <= 30 lignes) pour formats structurés complexes.
Entrées/Sorties : Reçoit des octets bruts (XML, RSS, iCal) et produit une liste de dictionnaires.
Hors-scope : N'effectue aucun appel réseau, aucun accès disque ni validation Pydantic.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Callable


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
            records.append(
                {
                    "event_id": rec_id,
                    "road_name": road_el.text.strip()
                    if road_el is not None and road_el.text
                    else "A",
                    "situation_type": elem.attrib.get(
                        "{http://www.w3.org/2001/XMLSchema-instance}type", "situation"
                    ),
                    "start_time": time_el.text.strip()
                    if time_el is not None and time_el.text
                    else "",
                    "lat": float(lat_el.text.strip())
                    if lat_el is not None and lat_el.text
                    else None,
                    "lon": float(lon_el.text.strip())
                    if lon_el is not None and lon_el.text
                    else None,
                    "comment": val_el.text.strip() if val_el is not None and val_el.text else "",
                }
            )
    return records


PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    "cita_datex2": cita_datex2,
}
