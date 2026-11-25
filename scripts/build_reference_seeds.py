"""Rôle : Régénère les seeds de référence dbt depuis les sources officielles (aucune saisie manuelle).
Entrées/Sorties : communes (limites administratives CC0), stations Vel'oh (GBFS), stations hydro (AGE).
Hors-scope : Ne s'exécute pas dans le pipeline (référentiels quasi statiques, à relancer au besoin).
"""

from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

import httpx

CSV_URL = "https://data.public.lu/fr/datasets/r/3931f0cf-ebf9-4050-b71c-e1b61b1bfa2c"
GEO_URL = "https://data.public.lu/fr/datasets/r/16103fa4-7ff1-486a-88bc-5018353957ea"
GBFS_INFO = "https://api.cyclocity.fr/contracts/luxembourg/gbfs/v2/station_information.json"
WATER_GEO = "https://data.public.lu/fr/datasets/r/5835f0e0-2e30-4a1f-b3a5-f05fba878de9"
SEEDS = Path("dbt_project/seeds")
OUT = SEEDS / "ref_communes_lu.csv"
# POURQUOI : l'export CSV AGE et le GeoJSON des stations n'utilisent pas exactement les mêmes noms
WATER_ALIASES = {
    "Stadtbredimus": "Stadtbrediums",
    "Gemünd_Our": "Gemünd",
    "Esch-Sure": "Esch/Sûre",
    "Ubersyren": "Uebersyren",
    "Roodt sur Syre": "Roodt-Syre",
    "Hunnebuer": "Hunnebour",
    "Mersch": "Mersch ( Beringen )",
}
WATER_CSV = "https://data.public.lu/fr/datasets/r/94fecbb1-4fce-4bee-8f2d-fc03b9fa314f"


def _write(path: Path, header: list[str], rows: list) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"{path} : {len(rows)} lignes")


def build_veloh(c: httpx.Client) -> None:
    st = c.get(GBFS_INFO).json()["data"]["stations"]
    rows = sorted(
        (int(s["station_id"]), s["name"], s.get("address"), s["lat"], s["lon"], s.get("capacity"))
        for s in st
    )
    _write(SEEDS / "ref_veloh_stations.csv", ["station_number", "station_name", "address", "lat", "lon", "capacity"], rows)


def build_water(c: httpx.Client) -> None:
    geo = {f["properties"]["Nom"]: f["geometry"]["coordinates"] for f in c.get(WATER_GEO).json()["features"]}
    names = [r[0].removeprefix("SN_") for r in csv.reader(io.StringIO(c.get(WATER_CSV).text.lstrip("﻿")))][1:]
    rows = []
    for n in names:
        lo, la = geo.get(WATER_ALIASES.get(n, n), (None, None))[:2]
        rows.append((n, la, lo))
    missing = [r[0] for r in rows if r[1] is None]
    print(f"Stations hydro sans coordonnées officielles : {missing}")
    _write(SEEDS / "ref_water_stations.csv", ["station_name", "lat", "lon"], rows)


def _ring_centroid(ring: list[list[float]]) -> tuple[float, float, float]:
    """Centroïde surfacique (formule du lacet) d'un anneau [lon, lat] : (aire, lat, lon)."""
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:], strict=False):
        cr = x0 * y1 - x1 * y0
        a, cx, cy = a + cr, cx + (x0 + x1) * cr, cy + (y0 + y1) * cr
    return (abs(a / 2), cy / (3 * a), cx / (3 * a)) if a else (0.0, ring[0][1], ring[0][0])


def main() -> int:
    with httpx.Client(follow_redirects=True, timeout=60) as c:
        build_veloh(c)
        build_water(c)
        rows = list(csv.DictReader(io.StringIO(c.get(CSV_URL).text.lstrip("﻿"))))
        feats = c.get(GEO_URL).json()["features"]
    cent = {}
    for f in feats:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        # POURQUOI : centroïde du plus grand polygone (évite les enclaves qui décalent la moyenne)
        _, lat, lon = max(_ring_centroid(p[0]) for p in polys)
        cent[f["properties"]["LAU2"]] = (round(lat, 5), round(lon, 5))
    out = sorted(
        (r["CODE_LAU2"], r["COMMUNE"], r["CANTON"], f"LU{r['CODE_LAU2']}", *cent[r["CODE_LAU2"]])
        for r in rows
    )
    assert len(out) == 100, f"Attendu 100 communes, obtenu {len(out)}"
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["commune_code", "commune_name", "canton", "code_lau", "lat", "lon"])
        w.writerows(out)
    print(f"{OUT} : {len(out)} communes, {len({r[2] for r in out})} cantons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
