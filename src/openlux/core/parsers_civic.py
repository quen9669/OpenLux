"""Rôle : Parsers vie civique & économie (fériés, alertes, STATEC/ADEM, logement, équipements).
Entrées/Sorties : Reçoit des octets bruts (JSON/CSV/XLSX/GML) et produit des listes de dicts plats.
Hors-scope : Aucun appel réseau ; les champs éditoriaux (motivations, descriptions) sont exclus.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Callable
from functools import partial

from openlux.core.parsers import _f, _j, _utc


def _csv(raw: bytes, **kw) -> list[dict]:
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), **kw))


def holidays_lu_json(raw: bytes) -> list[dict]:
    """Parse les jours fériés légaux LU (data.public.lu, CC0, fr/de/lb/en)."""
    return [
        {
            "holiday_date": h["date"],
            "country_code": "LU",
            "region_code": None,
            "holiday_type": "public",
            "name_fr": h.get("fr"),
            "name_de": h.get("de"),
            "name_lb": h.get("lb"),
            "end_date": h["date"],
        }
        for h in _j(raw)
    ]


def openholidays(raw: bytes, country: str = "LU") -> list[dict]:
    """Parse OpenHolidays (fériés 'Public' ou vacances 'School'), régions incluses."""
    out = []
    for h in _j(raw):
        if h.get("type") not in ("Public", "School"):
            continue  # POURQUOI : 'Bank' (ex. Vendredi saint au LU) n'est pas un jour férié légal
        subs = [s["code"] for s in h.get("subdivisions") or []] or [None]
        name = next((n["text"] for n in h.get("name", [])), None)
        for sub in subs:
            out.append(
                {
                    "holiday_date": h["startDate"],
                    "country_code": country,
                    "region_code": sub,
                    "holiday_type": h["type"].lower(),
                    "name_fr": name,
                    "name_de": None,
                    "name_lb": None,
                    "end_date": h["endDate"],
                }
            )
    return out


def meteoalarm_json(raw: bytes) -> list[dict]:
    """Parse les vigilances MeteoAlarm Luxembourg (émetteur MeteoLux), une ligne par zone."""
    out = []
    for w in _j(raw).get("warnings", []):
        a = w.get("alert", {})
        for info in (i for i in a.get("info", []) if str(i.get("language", "")).startswith("fr")):
            par = {p["valueName"]: p["value"] for p in info.get("parameter", [])}
            for area in info.get("area", []) or [{}]:
                out.append(
                    {
                        "alert_id": a.get("identifier"),
                        "event": info.get("event"),
                        "severity": info.get("severity"),
                        "awareness_level": par.get("awareness_level"),
                        "area": area.get("areaDesc"),
                        "onset_utc": _utc(info.get("onset")),
                        "expires_utc": _utc(info.get("expires")),
                        "observed_at": _utc(a.get("sent")),
                    }
                )
    return out


def petitions_chd_csv(raw: bytes) -> list[dict]:
    """Parse les pétitions publiques de la Chambre des Députés (sans motivation ni personnes)."""
    return [
        {
            "petition_id": r["PETITION_NBR"],
            "filing_date": _utc(r["FILING_DATE"], "%d/%m/%Y"),
            "title": (r.get("OFFICIAL_TITLE") or "")[:140],
            "petition_type": r.get("TYPE"),
            "status": r.get("STATUS"),
            "signatures": (_f(r.get("SIGN_NBR_ELECTRONIC")) or 0)
            + (_f(r.get("SIGN_NBR_PAPER")) or 0),
        }
        for r in _csv(raw)
    ]


def adem_communes_csv(raw: bytes) -> list[dict]:
    """Parse les demandeurs d'emploi ADEM par commune et sexe (mensuel depuis 2012)."""
    out = []
    for r in _csv(raw):
        d, m, y = r["Date"].split("-")
        out.append(
            {
                "reference_month": f"{y}-{m}",
                "commune_name": r["Commune"],
                "canton": r["Canton"],
                "sex": r["Sexe"],
                "job_seekers": _f(r["Personnes"]),
            }
        )
    return out


def lustat_csv(raw: bytes) -> list[dict]:
    """Parse un SDMX-CSV LUSTAT avec libellés (labels=name) : code + libellé par dimension."""
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    head, out = rows[0], []
    dims = [(i, head[i].lower()) for i in range(4, len(head) - 1, 2)]
    for r in rows[1:]:
        rec = {k: r[i] for i, k in dims}
        rec |= {f"{k}_label": r[i + 1] for i, k in dims}
        rec["obs_value"] = _f(rec.pop("obs_value", None))
        out.append(rec)
    return out


_MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()


def fuel_prices_csv(raw: bytes) -> list[dict]:
    """Parse les prix moyens mensuels des carburants et énergies (data.public.lu, CC0)."""
    units = {"Hydrogene": "EUR/kg", "Electricie_Fournisseur": "EUR/kWh"}
    out = []
    for r in _csv(raw):
        mon, yy = r.pop("Intervalle").strip().split("-")
        month = f"20{yy}-{_MONTHS.index(mon[:3].lower()) + 1:02d}"
        for k, v in r.items():
            if (val := _f(v)) is not None:
                u = units.get(k, "EUR/kWh" if k.startswith("Recharge") else "EUR/l")
                rec = {"reference_month": month, "energy_type": k, "price_eur": val, "unit": u}
                out.append(rec)
    return out


CIVIC_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    f.__name__: f
    for f in (
        holidays_lu_json,
        openholidays,
        meteoalarm_json,
        petitions_chd_csv,
        adem_communes_csv,
        lustat_csv,
        fuel_prices_csv,
    )
} | {
    f"openholidays_{c.lower()}": partial(openholidays, country=c) for c in ("LU", "FR", "BE", "DE")
}
