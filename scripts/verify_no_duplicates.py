"""Script de vérification de l'unicité et de l'absence totale de doublons sur les 22 tables Gold."""

import sys
from pathlib import Path

import duckdb

# Clés primaires logiques d'intégrité par Data Mart Gold
PRIMARY_KEYS: dict[str, str] = {
    "gold_air_quality": "station_id, observed_at_utc, pollutant",
    "gold_aviation_noise": "record_id",
    "gold_bathing_water": "site_id, observed_at_utc",
    "gold_civic_life": "record_id",
    "gold_crossborder_traffic": "event_id, observed_at_utc",
    "gold_culture_events": "LOWER(TRIM(title)), CAST(start_date AS DATE)",
    "gold_daily_life": "item_id",
    "gold_electricity_spot": "observed_at_utc, bidding_zone",
    "gold_fuel_prices": "fuel_type, observed_at_utc",
    "gold_health_alerts": "record_id",
    "gold_holidays": "holiday_date, country_code, COALESCE(region_code, ''), holiday_name",
    "gold_housing": "record_id",
    "gold_luxembourg_daily_context": "context_date, commune_lau",
    "gold_mobility_parkings": "facility_id, observed_at_utc",
    "gold_public_transit": "line_id, observed_at_utc",
    "gold_radioactivity": "station_id, observed_at_utc",
    "gold_roadworks": "work_id, observed_at_utc",
    "gold_statec_inflation": "reference_month",
    "gold_strikes_disruptions": "strike_id",
    "gold_traffic_events": "event_id, observed_at_utc",
    "gold_water_levels": "station_id, observed_at_utc",
    "gold_weather_observations": "station_id, observed_at_utc",
}


def main() -> int:
    con = duckdb.connect()
    gold_dir = Path("data/gold")
    if not gold_dir.exists():
        print("Erreur : data/gold introuvable.")
        return 1

    parquet_files = sorted(gold_dir.glob("*.parquet"))
    if not parquet_files:
        print("Aucun fichier Parquet dans data/gold.")
        return 1

    print("\n" + "=" * 95)
    print(f"{'TABLE GOLD':<32} | {'TOTAL':>7} | {'UNIQUES':>8} | {'DOUBLONS':>8} | {'STATUT':<10}")
    print("=" * 95)

    has_error = False
    for p in parquet_files:
        tbl = p.stem
        pk = PRIMARY_KEYS.get(tbl, "*")
        total = con.execute(f"SELECT count(*) FROM '{p.as_posix()}'").fetchone()[0]
        uniques = con.execute(f"SELECT count(DISTINCT ({pk})) FROM '{p.as_posix()}'").fetchone()[0]
        dups = total - uniques

        status = "OK [0]" if dups == 0 else f"ERREUR [{dups}]"
        if dups > 0:
            has_error = True
            dup_rows = con.execute(f"""
                SELECT {pk}, count(*) as cnt 
                FROM '{p.as_posix()}' 
                GROUP BY {pk} 
                HAVING count(*) > 1
            """).fetchall()
            print(f"  --> Doublons détectés pour {tbl} ({pk}) : {dup_rows}")

        print(f"{tbl:<32} | {total:>7} | {uniques:>8} | {dups:>8} | {status:<10}")

    print("=" * 95)
    con.close()

    if has_error:
        print("\nDes doublons ont été détectés dans les tables ci-dessus.")
        return 1

    print("\nAucun doublon détecté. Toutes les tables Gold respectent l'unicité stricte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
