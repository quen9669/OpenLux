"""Rôle : Parsers de fichiers structurés (XLSX Observatoire, GML INSPIRE, Overpass, mymaps).
Entrées/Sorties : Reçoit des octets bruts et produit des listes de dicts plats (WGS84).
Hors-scope : Aucune dépendance hors stdlib (pas d'openpyxl/pyproj) ; aucun appel réseau.
"""

from __future__ import annotations

import io
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Callable

from openlux.core.parsers import _f, _j, _x

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _cell(c: ET.Element | None, ss: list[str]) -> str | None:
    v = c.findtext(f"{_NS}v") if c is not None else None
    return ss[int(v)] if v is not None and c.get("t") == "s" else v


def _xlsx_sheets(raw: bytes) -> dict[str, list[list[str | None]]]:
    """Lecteur XLSX minimal (stdlib) : {nom_feuille: lignes de valeurs}, cellules C..F."""
    z = zipfile.ZipFile(io.BytesIO(raw))
    ss = [
        "".join(t.text or "" for t in si.iter(f"{_NS}t"))
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(f"{_NS}si")
    ]
    wb_rels = z.read("xl/_rels/workbook.xml.rels").decode()
    rels = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', wb_rels))
    out = {}
    for sh in ET.fromstring(z.read("xl/workbook.xml")).iter(f"{_NS}sheet"):
        rid = sh.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        rows = []
        for row in ET.fromstring(z.read(f"xl/{rels[rid]}")).iter(f"{_NS}row"):
            cells = {re.sub(r"\d", "", c.get("r")): c for c in row.iter(f"{_NS}c")}
            # POURQUOI : toute cellule t="s" est un index de chaîne partagée (ex. '*' masqué)
            vals = [_cell(cells.get(k), ss) for k in "CDEF"]
            rows.append(vals)
        out[sh.attrib["name"]] = rows
    return out


def observatoire_prices_xlsx(raw: bytes) -> list[dict]:
    """Parse les séries annuelles par commune de l'Observatoire de l'Habitat (prix annoncés)."""
    out = []
    for year, rows in _xlsx_sheets(raw).items():
        title = next((str(r[0]) for r in rows if r[0] and "annonc" in str(r[0])), "")
        kind = "HOUSE" if "maison" in title.lower() else "APARTMENT"
        start = next((i for i, r in enumerate(rows) if r[0] == "Commune"), None)
        for r in rows[start + 1 :] if start is not None else []:
            if r[0] and r[1]:
                out.append(
                    {
                        "reference_year": int(year),
                        "property_type": kind,
                        "commune_name": r[0].strip(),
                        "offers_count": _f(r[1]),
                        "avg_price_eur": _f(r[2]) if r[2] != "*" else None,
                        "avg_price_eur_m2": _f(r[3]) if r[3] != "*" else None,
                    }
                )
    return out


def _laea_to_wgs84(n: float, e: float) -> tuple[float, float]:
    """Inverse EPSG:3035 (ETRS89-LAEA, ellipsoïde GRS80, formules de Snyder) -> (lat, lon)."""
    a, es = 6378137.0, 0.00669438002290
    ec, lat0, lon0 = math.sqrt(es), math.radians(52), math.radians(10)

    def q(phi: float) -> float:
        s = math.sin(phi)
        return (1 - es) * (s / (1 - es * s * s) - math.log((1 - ec * s) / (1 + ec * s)) / (2 * ec))

    qp, q0 = q(math.pi / 2), q(lat0)
    rq, b0 = a * math.sqrt(qp / 2), math.asin(q0 / qp)
    d = a * math.cos(lat0) / math.sqrt(1 - es * math.sin(lat0) ** 2) / (rq * math.cos(b0))
    x, y = e - 4321000.0, n - 3210000.0
    rho = math.hypot(x / d, d * y)
    ce = 2 * math.asin(rho / (2 * rq))
    beta = math.asin(math.cos(ce) * math.sin(b0) + d * y * math.sin(ce) * math.cos(b0) / rho)
    den = d * rho * math.cos(b0) * math.cos(ce) - d * d * y * math.sin(b0) * math.sin(ce)
    lon = lon0 + math.atan2(x * math.sin(ce), den)
    lat = beta + (es / 3 + 31 * es**2 / 180) * math.sin(2 * beta)
    lat += 517 * es**2 / 5040 * math.sin(4 * beta)
    return round(math.degrees(lat), 6), round(math.degrees(lon), 6)


def recycling_gml(raw: bytes) -> list[dict]:
    """Parse les centres de recyclage INSPIRE (GML EPSG:3035, axe nord/est) en WGS84."""
    out = []
    root = ET.fromstring(raw)
    for f in (e for e in root.iter() if e.tag.endswith("EnvironmentalManagementFacility")):
        n, e = (float(v) for v in (_x(f, "pos") or "0 0").split())
        la, lo = _laea_to_wgs84(n, e)
        desc = (_x(f, "description") or "").split("\n")
        out.append(
            {
                "item_id": _x(f, "localId"),
                "category": "recycling_center",
                "name": desc[0].strip(),
                "details": desc[1].replace("Adresse :", "").strip() if len(desc) > 1 else None,
                "lat": la,
                "lon": lo,
            }
        )
    return out


def overpass_aed(raw: bytes) -> list[dict]:
    """Parse les défibrillateurs OpenStreetMap (Overpass, zone ISO LU) — ODbL."""
    return [
        {
            "item_id": f"osm-{el['type']}-{el['id']}",
            "category": "defibrillator",
            "name": el.get("tags", {}).get("name"),
            "details": "; ".join(
                f"{k}={v}"
                for k, v in el.get("tags", {}).items()
                if k in ("indoor", "access", "opening_hours", "defibrillator:location")
            )[:140]
            or None,
            "lat": el.get("lat") or el.get("center", {}).get("lat"),
            "lon": el.get("lon") or el.get("center", {}).get("lon"),
        }
        for el in _j(raw).get("elements", [])
    ]


def _km(line: list) -> float:
    r = 0.0
    for (x0, y0, *_), (x1, y1, *_) in zip(line, line[1:], strict=False):
        dx = math.radians(x1 - x0) * math.cos(math.radians((y0 + y1) / 2))
        r += 6371.0 * math.hypot(dx, math.radians(y1 - y0))
    return r


def mymaps_routes(raw: bytes) -> list[dict]:
    """Parse une catégorie mymaps geoportail (itinéraires cyclables) : longueur et point milieu."""
    out = []
    for i, f in enumerate(_j(raw).get("features", [])):
        g = f.get("geometry") or {}
        lines = g["coordinates"] if g.get("type") == "MultiLineString" else [g.get("coordinates")]
        pts = [p for ln in lines if ln for p in ln]
        if not pts:
            continue
        mid = pts[len(pts) // 2]
        out.append(
            {
                "route_id": f"{f['properties'].get('map_id', '')}-{i}",
                "route_name": f["properties"].get("name"),
                "length_km": round(sum(_km(ln) for ln in lines if ln), 3),
                "lat": mid[1],
                "lon": mid[0],
            }
        )
    return out


FILE_PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    f.__name__: f for f in (observatoire_prices_xlsx, recycling_gml, overpass_aed, mymaps_routes)
}
