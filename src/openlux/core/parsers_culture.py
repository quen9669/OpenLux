"""Rôle : Parsers agenda culturel & actualités (echo.lu, agenda VdL, Rockhal, RSS grèves).
Entrées/Sorties : Reçoit des octets bruts (JSON/RSS) et produit des listes de dicts factuels.
Hors-scope : Aucun texte éditorial (descriptions, résumés) : titre ≤ 140 car., date, lieu, lien.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import datetime
from email.utils import parsedate_to_datetime

from openlux.core.parsers import _f, _j, _utc


def _rfc822(s: str | None) -> str | None:
    try:
        return _utc(parsedate_to_datetime(s).isoformat()) if s else None
    except (TypeError, ValueError):
        return None


def _ts(v) -> str | None:
    return _utc(v.get("_seconds")) if isinstance(v, dict) else None


def echo_algolia(raw: bytes) -> list[dict]:
    """Parse l'index public echo.lu (Algolia) : une ligne par événement, prix et lieu factuels."""
    out = []
    for h in _j(raw).get("hits", []):
        x = h.get("rawExperience", {})
        t = x.get("title") or {}
        t = t if isinstance(t, dict) else {"fr": str(t)}
        geo = h.get("_geoloc") or {}
        geo = (geo or [{}])[0] if isinstance(geo, list) else geo
        venues = h.get("rawVenues") or []
        prices = [v for p in x.get("tickets") or [] if (v := _f(p.get("price"))) is not None]
        out.append(
            {
                "event_id": f"echo-{h.get('objectID')}",
                "title": (t.get("fr") or t.get("en") or t.get("de") or "")[:140],
                "start_utc": _ts(h.get("from")),
                "end_utc": _ts(h.get("to")),
                "venue": next((v["title"] for v in venues if v.get("title")), None),
                "category": ",".join(x.get("categories") or []) or None,
                "is_free": bool(h.get("isFree")),
                "price_min_eur": min(prices) if prices else None,
                "commune_slug": ",".join(h.get("communes") or []) or None,
                "url": f"https://www.echo.lu/fr/experiences/{h.get('experienceId')}",
                "lat": geo.get("lat"),
                "lon": geo.get("lng"),
            }
        )
    return out


def vdl_agenda_rss(raw: bytes) -> list[dict]:
    """Parse l'agenda RSS de la Ville de Luxembourg (titre + lien ; pubDate = date annoncée)."""
    return [
        {
            "event_id": f"vdl-{(it.findtext('guid') or it.findtext('link') or '').strip()}",
            "title": (it.findtext("title") or "").strip()[:140],
            "start_utc": _rfc822(it.findtext("pubDate")),
            "end_utc": None,
            "venue": None,
            "category": None,
            "is_free": None,
            "price_min_eur": None,
            "commune_slug": "luxembourg",
            "url": (it.findtext("link") or "").strip(),
            "lat": None,
            "lon": None,
        }
        for it in ET.fromstring(raw).iter("item")
    ]


def _rockhal_date(s: str | None) -> str | None:
    try:
        return datetime.strptime(s or "", "%a %d %b %Y").date().isoformat()
    except ValueError:
        return None


def rockhal_shows(raw: bytes) -> list[dict]:
    """Parse l'API WordPress des concerts à venir de la Rockhal (Esch-Belval)."""
    return [
        {
            "event_id": f"rockhal-{s.get('id')}",
            "title": " – ".join(x for x in (s.get("title"), s.get("subtitle")) if x)[:140],
            "start_utc": _rockhal_date(s.get("start_date")),
            "end_utc": _rockhal_date(s.get("end_date")),
            "venue": s.get("location"),
            "category": ",".join(g["name"] for g in s.get("genres") or []) or None,
            "is_free": None,
            "price_min_eur": None,
            "commune_slug": "esch-sur-alzette",
            "url": s.get("permalink"),
            "lat": 49.5014,
            "lon": 5.9446,
        }
        for s in _j(raw).get("shows", [])
    ]


_STRIKE = re.compile(r"\b(grève|greve|grèves|streik\w*|strike\w*|débrayage|préavis)\b", re.I)
_COUNTRY = {
    "FR": re.compile(r"\b(sncf|france|lorraine|metz|thionville|français)\b", re.I),
    "BE": re.compile(r"\b(sncb|belgique|belge|arlon|wallonie)\b", re.I),
    "DE": re.compile(r"\b(deutsche bahn|allemagne|deutschland|trier|saar\w*)\b", re.I),
}


def strikes_rss(raw: bytes) -> list[dict]:
    """Filtre un flux RSS d'actualités sur les mots-clés de grève ; titre et lien seulement."""
    out = []
    for it in ET.fromstring(raw).iter("item"):
        title = (it.findtext("title") or "").strip()
        if not _STRIKE.search(title):
            continue
        cc = next((c for c, rx in _COUNTRY.items() if rx.search(title)), "LU")
        out.append(
            {
                "article_id": (it.findtext("guid") or it.findtext("link") or title).strip()[:200],
                "title": title[:140],
                "published_at_utc": _rfc822(it.findtext("pubDate")),
                "country_code": cc,
                "publisher": (it.findtext("source") or "").strip() or None,
                "url": (it.findtext("link") or "").strip(),
            }
        )
    return out


CULTURE_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    f.__name__: f for f in (echo_algolia, vdl_agenda_rss, rockhal_shows, strikes_rss)
}
