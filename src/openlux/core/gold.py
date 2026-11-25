"""Rôle : Export atomique, registre sécurisé, requêtes et streaming de la couche Gold Parquet.
Entrées/Sorties : Lit/écrit les tables Gold dans data/gold/ et DuckDB en mémoire.
Hors-scope : N'effectue pas d'appels réseau ni de transformation Silver dbt.
"""

from __future__ import annotations

import contextlib
import os
import time
from pathlib import Path

import duckdb

# POURQUOI : clé métier de chaque table Gold ; à la fusion avec l'historique Parquet on garde la
# version la plus récente (collected_at_utc) de chaque clé, sans jamais supprimer une clé passée.
GOLD_KEYS: dict[str, str] = {
    "gold_weather_observations": "station_id, observed_at_utc",
    "gold_air_quality": "station_id, observed_at_utc, pollutant",
    "gold_water_levels": "station_name, observed_at_utc",
    "gold_bathing_water": "site_id",
    "gold_traffic_events": "source_id, event_id",
    "gold_roadworks": "source_id, work_id",
    "gold_transit_disruptions": "source_id, disruption_id",
    "gold_mobility_veloh": "station_number, observed_at_utc",
    "gold_mobility_parkings": "parking_id, observed_at_utc",
    "gold_chargy_stations": "site_name, collected_at_utc",
    "gold_aviation": "icao24, observed_at_utc",
    "gold_fuel_prices": "reference_month, energy_type",
    "gold_inflation": "reference_month",
    "gold_electricity_spot": "observed_at_utc",
    "gold_building_permits": "canton_code, building_type_code, reference_year",
    "gold_housing_prices": "reference_year, property_type, commune_name",
    "gold_unemployment": "reference_month, commune_name, sex",
    "gold_holidays": "holiday_date, country_code, region_code, holiday_type",
    "gold_weather_warnings": "alert_id, area",
    "gold_equipment": "source_id, item_id",
    "gold_petitions": "petition_id",
    "gold_culture_events": "event_id",
    "gold_strikes_news": "article_id",
    "gold_luxembourg_daily_context": "context_date, canton",
}


def _export_one(
    con: duckdb.DuckDBPyConnection, tbl: str, tmp: Path, target: Path
) -> tuple[Path, Path] | None:
    t, f = tmp / f"{tbl}.parquet", target / f"{tbl}.parquet"
    cols = [c[0] for c in con.execute(f"DESCRIBE SELECT * FROM {tbl}").fetchall()]
    key = GOLD_KEYS.get(tbl, ", ".join(cols))
    order = "computed_at_utc" if "computed_at_utc" in cols else "collected_at_utc"
    order = order if order in cols else cols[0]
    src = f"SELECT * FROM {tbl}"
    if f.exists() and f.stat().st_size > 0:
        src = f"SELECT * FROM read_parquet('{f.as_posix()}') UNION ALL BY NAME {src}"
    rep = (
        f" REPLACE (MIN(first_seen_utc) OVER (PARTITION BY {key}) AS first_seen_utc)"
        if "first_seen_utc" in cols
        else ""
    )
    q = (
        f"SELECT *{rep} FROM ({src}) QUALIFY ROW_NUMBER() OVER "
        f"(PARTITION BY {key} ORDER BY {order} DESC NULLS LAST) = 1 ORDER BY {key}"
    )
    con.execute(f"COPY ({q}) TO '{t.as_posix()}' (FORMAT PARQUET, CODEC 'ZSTD')")
    return (t, f)


def export_gold_parquets(
    duckdb_path: Path | str = "data/openlux.duckdb", gold_dir: Path | str = "data/gold"
) -> list[str]:
    """Exporte de façon incrémentale et atomique chaque table Gold en Parquet ZSTD."""
    if not Path(duckdb_path).exists():
        return []
    target, tmp = Path(gold_dir), Path(gold_dir) / ".tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    con = None
    for _ in range(10):
        with contextlib.suppress(Exception):
            if con := duckdb.connect(str(duckdb_path), read_only=True):
                break
        time.sleep(0.2)
    if not con:
        return []
    try:
        q = "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'gold_%'"
        tables = [r[0] for r in con.execute(q).fetchall()]
        replaces = [r for tbl in tables if (r := _export_one(con, tbl, tmp, target))]
    finally:
        con.close()
    for t, f in replaces:
        for _ in range(5):
            with contextlib.suppress(PermissionError):
                os.replace(t, f)
                break
            time.sleep(0.05)
        with contextlib.suppress(Exception), duckdb.connect(str(duckdb_path)) as rw:
            p_pos = f.as_posix()
            rw.execute(f"CREATE OR REPLACE TABLE {t.stem} AS SELECT * FROM read_parquet('{p_pos}')")
    return tables


def list_gold_datasets(gold_dir: Path | str = "data/gold") -> list[str]:
    return [p.stem for p in Path(gold_dir).glob("gold_*.parquet")]


def get_gold_table_path(dataset: str, gold_dir: Path | str = "data/gold") -> Path | None:
    if any(c in dataset for c in ("/", "\\", ";", "'", '"', "..")):
        return None
    valid = {p.stem.lower(): p for p in Path(gold_dir).glob("gold_*.parquet")}
    return valid.get(n := dataset.strip().lower()) or valid.get(f"gold_{n}")
