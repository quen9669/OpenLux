"""Moissonneur officiel des autorisations de bâtir et logements autorisés STATEC.

Rôle : Récupère les données officielles STATEC Lustat (DF_D4113 & DF_D4123) par canton et VDL.
Entrées : API REST SDMX officielle de STATEC (Lustat).
Sorties : data/bronze/housing_statec/latest.json.gz normalisé.
Hors-scope : Agrégations autres que le découpage officiel par canton et Ville de Luxembourg.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
from pathlib import Path

import httpx

CANTON_NAMES: dict[str, str] = {
    "CPL": "Capellen",
    "CLV": "Clervaux",
    "DIE": "Diekirch",
    "ECT": "Echternach",
    "ESC": "Esch-sur-Alzette",
    "GRE": "Grevenmacher",
    "LUX": "Luxembourg",
    "MER": "Mersch",
    "RED": "Redange",
    "REM": "Remich",
    "VIA": "Vianden",
    "WIL": "Wiltz",
    "VDL": "Luxembourg",
}

PROD_TYPES: dict[str, str] = {
    "CPA_F41001": "HOUSE",
    "CPA_F41002": "APARTMENT",
    "CPA_F410014": "OTHER_RESIDENTIAL",
    "CPA_F41001_41002": "TOTAL_RESIDENTIAL",
}


def harvest_statec_permits() -> list[dict[str, object]]:
    """Récupère les séries officielles STATEC des permis et unités de logements autorisées."""
    print("Harvesting official STATEC building permits and housing units from Lustat SDMX...")
    client = httpx.Client(timeout=30.0)
    headers = {"Accept": "application/vnd.sdmx.data+csv;file=true"}

    url_units = (
        "https://lustat.statec.lu/rest/data/LU1,DF_D4113/all?dimensionAtObservation=AllDimensions"
    )
    url_bld = (
        "https://lustat.statec.lu/rest/data/LU1,DF_D4123/all?dimensionAtObservation=AllDimensions"
    )

    r_units = client.get(url_units, headers=headers)
    r_units.raise_for_status()
    r_bld = client.get(url_bld, headers=headers)
    r_bld.raise_for_status()

    units_map: dict[tuple[str, str, str], int] = {}
    for row in csv.DictReader(io.StringIO(r_units.text)):
        canton = row["CANTON"]
        prod = row["PRODUCT_BCS"]
        period = row["TIME_PERIOD"]
        val = row.get("OBS_VALUE")
        if val and val.isdigit():
            units_map[(canton, prod, period)] = int(val)

    bld_map: dict[tuple[str, str, str], int] = {}
    for row in csv.DictReader(io.StringIO(r_bld.text)):
        canton = row["CANTON"]
        prod = row["PRODUCT_BCS"]
        period = row["TIME_PERIOD"]
        val = row.get("OBS_VALUE")
        if val and val.isdigit():
            bld_map[(canton, prod, period)] = int(val)

    records: list[dict[str, object]] = []
    all_keys = set(units_map.keys()) | set(bld_map.keys())
    for canton_code, prod_code, period in sorted(all_keys):
        if prod_code not in PROD_TYPES:
            continue
        c_name = CANTON_NAMES.get(canton_code, canton_code)
        p_type = PROD_TYPES[prod_code]
        u_auth = units_map.get((canton_code, prod_code, period), 0)
        b_auth = bld_map.get((canton_code, prod_code, period), 0)
        rec_id = f"STATEC_{canton_code}_{p_type}_{period}"

        records.append(
            {
                "record_id": rec_id,
                "canton_code": canton_code,
                "commune_name": "Luxembourg" if canton_code == "VDL" else c_name,
                "canton_name": c_name,
                "property_type": p_type,
                "reference_period": period,
                "permits_count": b_auth,
                "units_authorized": u_auth,
                "observed_at": "2026-11-21T00:00:00Z",
            }
        )

    out_dir = Path("data/bronze/housing_statec")
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_json = json.dumps(records, ensure_ascii=False, indent=2).encode("utf-8")
    (out_dir / "latest.json.gz").write_bytes(gzip.compress(raw_json))
    print(f"Wrote {len(records)} STATEC records to data/bronze/housing_statec/latest.json.gz")
    return records


if __name__ == "__main__":
    harvest_statec_permits()
