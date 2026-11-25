"""Rôle : Catalogue factuel des tables Gold (API, site, Data Package, DCAT-AP-LU) et publication.
Entrées/Sorties : Lit data/gold/*.parquet + config/sources.toml -> catalogue JSON et métadonnées.
Hors-scope : Aucun chiffre saisi à la main : volumes, couverture et sources sont mesurés.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import duckdb

from openlux.config import load_sources_config
from openlux.publish.tables import TABLE_INFO

_TIME_COLS = (
    "observed_at_utc", "context_date", "reference_month", "reference_year", "holiday_date",
    "start_time_utc", "start_utc", "filing_date", "published_at_utc", "collected_at_utc",
)  # fmt: skip


def _infer_type(duck_type: str) -> str:
    t = duck_type.upper()
    if "INT" in t:
        return "integer"
    if any(k in t for k in ("DOUBLE", "FLOAT", "DECIMAL", "NUMERIC")):
        return "number"
    if "BOOL" in t:
        return "boolean"
    return "datetime" if "TIMESTAMP" in t else ("date" if "DATE" in t else "string")


def _source_card(sid: str, src: Any) -> dict[str, Any]:
    return {
        "source_id": sid,
        "description": src.description,
        "url": src.primary.url.split("?")[0],
        "license_spdx": src.license_spdx,
        "data_origin": src.data_origin,
        "commercial_use_safe": src.commercial_use_safe,
        "known_limitations": src.known_limitations,
    }


def _describe(con: duckdb.DuckDBPyConnection, p: Path, sources: dict) -> dict[str, Any]:
    q = f"read_parquet('{p.as_posix()}')"
    cols = con.execute(f"DESCRIBE SELECT * FROM {q}").fetchall()
    names = [c[0] for c in cols]
    tc = next((c for c in _TIME_COLS if c in names), None)
    cov = (
        con.execute(f"SELECT MIN({tc})::VARCHAR, MAX({tc})::VARCHAR FROM {q}").fetchone()
        if tc
        else None
    )
    last = "MAX(collected_at_utc)::VARCHAR" if "collected_at_utc" in names else "NULL"
    n, last_c = con.execute(f"SELECT COUNT(*), {last} FROM {q}").fetchone()
    sids = (
        [r[0] for r in con.execute(f"SELECT DISTINCT source_id FROM {q} ORDER BY 1").fetchall()]
        if "source_id" in names
        else []
    )
    domain, title, stds = TABLE_INFO.get(p.stem, ("Autre", p.stem, []))
    return {
        "dataset": p.stem,
        "title": title,
        "domain": domain,
        "row_count": n,
        "time_column": tc,
        "coverage": {"from": cov[0], "to": cov[1]} if cov else None,
        "last_collected_utc": last_c,
        "standards": stds,
        "columns": [{"name": c[0], "type": str(c[1])} for c in cols],
        "sources": [_source_card(s, src) for s in sids if (src := sources.get(s))],
    }


def build_catalog(gold_dir: Path = Path("data/gold")) -> list[dict[str, Any]]:
    """Catalogue mesuré de chaque table Gold (ordre du registre TABLE_INFO)."""
    sources, order = load_sources_config(), list(TABLE_INFO)
    paths = sorted(
        gold_dir.glob("gold_*.parquet"),
        key=lambda p: (p.stem not in order, order.index(p.stem) if p.stem in order else 0, p.stem),
    )
    with duckdb.connect() as con:
        return [_describe(con, p, sources) for p in paths]


def generate_datapackage(gold_dir: Path = Path("data/gold")) -> dict[str, Any]:
    resources = [
        {
            "name": d["dataset"],
            "title": d["title"],
            "path": f"{d['dataset']}.parquet",
            "format": "parquet",
            "mediatype": "application/vnd.apache.parquet",
            "compression": "zstd",
            "row_count": d["row_count"],
            "sha256": hashlib.sha256(
                (gold_dir / f"{d['dataset']}.parquet").read_bytes()
            ).hexdigest(),
            "licenses": sorted({s["license_spdx"] for s in d["sources"]}),
            "sources": [{"title": s["source_id"], "path": s["url"]} for s in d["sources"]],
            "schema": {
                "fields": [
                    {"name": c["name"], "type": _infer_type(c["type"])} for c in d["columns"]
                ]
            },
        }
        for d in build_catalog(gold_dir)
    ]
    return {
        "profile": "tabular-data-package",
        "name": "openlux-hub-gold",
        "title": "OpenLux Hub — Données ouvertes consolidées du Luxembourg",
        "homepage": "https://github.com/quen9669/OpenLux",
        "spatial": {"country": "LU"},
        "resources": resources,
    }


def generate_dcat_ap_lu(gold_dir: Path = Path("data/gold")) -> dict[str, Any]:
    dp = generate_datapackage(gold_dir)
    raw = "https://raw.githubusercontent.com/quen9669/OpenLux/main/data/gold"
    return {
        "@context": "https://data.public.lu/dcat-ap-lu.jsonld",
        "@type": "dcat:Dataset",
        "title": dp["title"],
        "description": f"{len(dp['resources'])} tables Gold issues de sources publiques vérifiées.",
        "publisher": {"@type": "org:Organization", "name": "OpenLux Hub"},
        "spatial": "http://publications.europa.eu/resource/authority/country/LUX",
        "distributions": [
            {
                "@type": "dcat:Distribution",
                "title": r["title"],
                "downloadURL": f"{raw}/{r['path']}",
                "mediaType": r["mediatype"],
                "byteSize": (gold_dir / r["path"]).stat().st_size,
                "license": r["licenses"],
            }
            for r in dp["resources"]
        ],
    }


def write_site_catalog(gold_dir: Path = Path("data/gold"), site_dir: Path = Path("web_v2")) -> Path:
    """Instantané du catalogue pour le site statique (fonctionne sans API, chiffres réels)."""
    out = site_dir / "data" / "catalog.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(build_catalog(gold_dir), ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return out


def publish_to_data_public_lu(
    dry_run: bool = True, gold_dir: Path = Path("data/gold")
) -> dict[str, Any]:
    """Écrit datapackage.json et dcat_ap_lu.json ; la publication distante n'est pas implémentée."""
    dp, dcat = generate_datapackage(gold_dir), generate_dcat_ap_lu(gold_dir)
    dp_path, dcat_path = gold_dir / "datapackage.json", gold_dir / "dcat_ap_lu.json"
    dp_path.write_text(json.dumps(dp, indent=2, ensure_ascii=False), encoding="utf-8")
    dcat_path.write_text(json.dumps(dcat, indent=2, ensure_ascii=False), encoding="utf-8")
    has_key = bool(os.getenv("DATA_PUBLIC_LU_API_KEY"))
    return {
        "status": "METADATA_WRITTEN" if dry_run or not has_key else "NOT_IMPLEMENTED",
        "dry_run": dry_run,
        "resources_count": len(dp["resources"]),
        "datapackage_path": str(dp_path),
        "dcat_path": str(dcat_path),
    }
