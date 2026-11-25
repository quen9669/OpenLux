"""Rôle : Parsers perturbations transports publics (SNCF SIRI SX, SNCB iRail, bus VdL).
Entrées/Sorties : Reçoit des octets bruts (XML/JSON) et produit des listes de dicts plats.
Hors-scope : Aucun appel réseau ; filtrage par mots-clés sur l'axe Luxembourg uniquement.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Callable

from openlux.core.parsers import _j, _utc, _x

_RAIL_LU = re.compile(r"luxemb|thionville|bettembourg|hettange|longwy|metz|arlon|trier", re.I)


def _fr(el: ET.Element, tag: str) -> str:
    lang = "{http://www.w3.org/XML/1998/namespace}lang"
    return next((c.text or "" for c in el if c.tag.endswith(tag) and c.get(lang) == "FR"), "")


def sncf_siri_sx(raw: bytes) -> list[dict]:
    """Parse le SIRI Lite Situation Exchange SNCF, filtré sur l'axe Metz–Thionville–Luxembourg."""
    out = []
    for el in (e for e in ET.fromstring(raw).iter() if e.tag.endswith("PtSituationElement")):
        fr, desc = _fr(el, "Summary"), _fr(el, "Description")
        if not _RAIL_LU.search(f"{fr} {desc}"):
            continue
        out.append(
            {
                "disruption_id": _x(el, "SituationNumber"),
                "operator": "SNCF",
                "mode": "rail",
                "title": (fr or "")[:140],
                "severity": _x(el, "Severity"),
                "category": None,
                "start_time_utc": _utc(_x(el, "StartTime")),
                "end_time_utc": _utc(_x(el, "EndTime")),
                "observed_at": _utc(_x(el, "CreationTime")),
                "detail": re.sub(r"\s+", " ", desc or "")[:300] or None,
            }
        )
    return out


def irail_disturbances(raw: bytes) -> list[dict]:
    """Parse les perturbations SNCB (iRail), filtrées sur Arlon / Luxembourg."""
    out = []
    for it in _j(raw).get("disturbance", []):
        if not _RAIL_LU.search(f"{it.get('title', '')} {it.get('description', '')}"):
            continue
        out.append(
            {
                "disruption_id": it.get("id"),
                "operator": "SNCB",
                "mode": "rail",
                "title": (it.get("title") or "")[:140],
                "severity": None,
                "category": it.get("type"),
                "start_time_utc": _utc(it.get("timestamp")),
                "end_time_utc": None,
                "observed_at": _utc(it.get("timestamp")),
                "detail": (it.get("description") or "")[:300] or None,
            }
        )
    return out


def vdl_bus_messages(raw: bytes) -> list[dict]:
    """Parse les messages AVL des autobus de la Ville de Luxembourg (titre factuel seulement)."""
    fmt = "%Y-%m-%d %H:%M"
    return [
        {
            "disruption_id": _x(m, "MessageID"),
            "operator": "AVL (Ville de Luxembourg)",
            "mode": "bus",
            "title": (_x(m, "Titre") or "")[:140],
            "severity": "urgent" if _x(m, "Urgent") == "true" else "normal",
            "category": _x(m, "Categorie"),
            "start_time_utc": _utc(_x(m, "DateDebut"), fmt),
            "end_time_utc": _utc(_x(m, "DateFin"), fmt),
            "observed_at": None,
            "detail": None,
        }
        for m in ET.fromstring(raw).iter("Message")
    ]


TRANSIT_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    f.__name__: f for f in (sncf_siri_sx, irail_disturbances, vdl_bus_messages)
}
