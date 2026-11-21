"""Rôle : Récupération exhaustive des événements culturels Echo.lu via l'index Algolia public.
Entrées/Sorties : Interroge le CDN Algolia par facettes de catégories et produit data/bronze/culture_echo_lu/latest.json.gz normalisé avec expansion multi-dates.
Hors-scope : Aucun appel à l'API privée v1.
"""

from __future__ import annotations

import gzip
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

TZ_LUX = ZoneInfo("Europe/Luxembourg")


def normalize_event_sessions(h: dict) -> list[dict]:
    raw_exp = h.get("rawExperience", {})
    t = raw_exp.get("title")
    if isinstance(t, dict):
        title = (
            t.get("fr")
            or t.get("en")
            or t.get("de")
            or t.get("lu")
            or next(iter(t.values()), "Événement sans titre")
        )
    elif isinstance(t, str):
        title = t
    else:
        title = "Événement sans titre"

    exp_id = h.get("experienceId") or h.get("objectID")
    source_url = f"https://www.echo.lu/fr/experiences/{exp_id}"

    status_raw = raw_exp.get("status", {})
    status_cur = (
        status_raw.get("current", "published")
        if isinstance(status_raw, dict)
        else str(status_raw or "published")
    )
    if status_cur == "cancelled":
        status_label = "Annulé"
    elif status_cur == "postponed":
        status_label = "Reporté"
    else:
        status_label = "Confirmé"

    is_free = bool(h.get("isFree") or raw_exp.get("priceType") == "free")
    tickets = raw_exp.get("tickets") or []
    prices = [
        float(t_item.get("price"))
        for t_item in tickets
        if isinstance(t_item, dict) and t_item.get("price") is not None
    ]
    if is_free or (prices and max(prices) == 0.0):
        is_free = True
        price_eur = 0.0
        price_text = "Gratuit"
    elif prices:
        min_p = min(prices)
        max_p = max(prices)
        price_eur = min_p
        price_text = f"{min_p:g} €" if min_p == max_p else f"{min_p:g} € - {max_p:g} €"
        is_free = False
    else:
        price_eur = None
        price_text = "Payant"
        is_free = False

    venues = h.get("rawVenues") or []
    if venues and isinstance(venues[0], dict):
        v = venues[0]
        venue_name = v.get("title") or v.get("name") or "Lieu non spécifié"
        addr_obj = (
            v.get("location", {}).get("address", {}) if isinstance(v.get("location"), dict) else {}
        )
        street = addr_obj.get("street") or ""
        number = addr_obj.get("number") or ""
        postcode = addr_obj.get("postcode") or ""
        town = addr_obj.get("town") or addr_obj.get("commune") or "Luxembourg"
        city = town
        parts = []
        if number and street:
            parts.append(f"{number} {street}")
        elif street:
            parts.append(street)
        if postcode and town:
            parts.append(f"{postcode} {town}")
        elif town:
            parts.append(town)
        full_address = ", ".join(parts) if parts else street or town or "Luxembourg"
        geoloc = v.get("_geoloc") or []
        if geoloc and isinstance(geoloc, list) and isinstance(geoloc[0], dict):
            lat = float(geoloc[0].get("lat", 49.6117))
            lon = float(geoloc[0].get("lng", 6.1319))
        elif addr_obj.get("latitude") and addr_obj.get("longitude"):
            lat = float(addr_obj["latitude"])
            lon = float(addr_obj["longitude"])
        else:
            lat = None
            lon = None
    else:
        venue_name = "Lieu non spécifié"
        city = h.get("communes", ["Luxembourg"])[0] if h.get("communes") else "Luxembourg"
        full_address = city
        lat = None
        lon = None

    global_purchase_link = raw_exp.get("purchaseLink") or ""
    cats = raw_exp.get("categories", [])
    cat = cats[0] if cats else "Culture"

    dates = raw_exp.get("dates", [])
    sessions = []

    if dates and isinstance(dates, list):
        for d in dates:
            if not isinstance(d, dict):
                continue
            from_dict = d.get("from", {}) if isinstance(d.get("from"), dict) else {}
            to_dict = d.get("to", {}) if isinstance(d.get("to"), dict) else {}
            from_sec = from_dict.get("_seconds")
            to_sec = to_dict.get("_seconds")
            if not from_sec:
                continue
            dt_start = datetime.fromtimestamp(from_sec, tz=TZ_LUX)
            dt_end = datetime.fromtimestamp(to_sec, tz=TZ_LUX) if to_sec else dt_start
            p_link = d.get("purchaseLink") or global_purchase_link or None

            sessions.append(
                {
                    "title": str(title)[:140],
                    "status": status_label,
                    "start_date": dt_start.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_date": dt_end.strftime("%Y-%m-%d %H:%M:%S"),
                    "start_time": dt_start.strftime("%H:%M"),
                    "venue": str(venue_name),
                    "address": str(full_address),
                    "city": str(city),
                    "category": str(cat),
                    "price_eur": price_eur,
                    "price_text": price_text,
                    "is_free": is_free,
                    "source_url": source_url,
                    "ticket_url": p_link,
                    "lat": lat,
                    "lon": lon,
                }
            )

    if not sessions:
        from_ts = h.get("from_timestamp")
        to_ts = h.get("to_timestamp")
        dt_start = datetime.fromtimestamp(from_ts / 1000, tz=TZ_LUX) if from_ts else None
        dt_end = datetime.fromtimestamp(to_ts / 1000, tz=TZ_LUX) if to_ts else dt_start
        sessions.append(
            {
                "title": str(title)[:140],
                "status": status_label,
                "start_date": dt_start.strftime("%Y-%m-%d %H:%M:%S") if dt_start else None,
                "end_date": dt_end.strftime("%Y-%m-%d %H:%M:%S") if dt_end else None,
                "start_time": dt_start.strftime("%H:%M") if dt_start else None,
                "venue": str(venue_name),
                "address": str(full_address),
                "city": str(city),
                "category": str(cat),
                "price_eur": price_eur,
                "price_text": price_text,
                "is_free": is_free,
                "source_url": source_url,
                "ticket_url": global_purchase_link or None,
                "lat": lat,
                "lon": lon,
            }
        )

    return sessions


def harvest_echo_to_bronze() -> int:
    client = httpx.Client(
        headers={
            "x-algolia-application-id": "PY7G9MVXE2",
            "x-algolia-api-key": "55301c0ef2e535ae29e6b6d697f4882d",
            "User-Agent": "OpenLuxHub/1.0",
        },
        timeout=15.0,
    )

    res = client.post(
        "https://py7g9mvxe2-dsn.algolia.net/1/indexes/*/queries",
        json={
            "requests": [
                {
                    "indexName": "prod_experiences.compact",
                    "params": "query=&hitsPerPage=0&facets=%5B%22rawExperience.categories%22%5D",
                }
            ]
        },
    )
    categories = list(
        res.json()["results"][0].get("facets", {}).get("rawExperience.categories", {}).keys()
    )
    print(f"Catégories trouvées : {len(categories)}")

    events_by_id = {}
    for cat in categories:
        cat_enc = cat.replace(" ", "%20")
        r = client.post(
            "https://py7g9mvxe2-dsn.algolia.net/1/indexes/*/queries",
            json={
                "requests": [
                    {
                        "indexName": "prod_experiences.compact",
                        "params": f"query=&hitsPerPage=1000&facetFilters=%5B%22rawExperience.categories%3A{cat_enc}%22%5D",
                    }
                ]
            },
        )
        for h in r.json().get("results", [{}])[0].get("hits", []):
            events_by_id[h["objectID"]] = h

    all_sessions = []
    seen_session_keys = set()
    for h in events_by_id.values():
        for sess in normalize_event_sessions(h):
            s_key = (sess["title"], sess["start_date"], sess["venue"])
            if s_key not in seen_session_keys:
                seen_session_keys.add(s_key)
                all_sessions.append(sess)

    out_dir = Path("data/bronze/culture_echo_lu")
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_json = json.dumps(all_sessions, ensure_ascii=False, indent=2).encode("utf-8")
    (out_dir / "latest.json.gz").write_bytes(gzip.compress(raw_json))
    print(
        f"Successfully saved {len(all_sessions)} sessions from {len(events_by_id)} experiences to data/bronze/culture_echo_lu/latest.json.gz!"
    )
    return len(all_sessions)


if __name__ == "__main__":
    harvest_echo_to_bronze()
