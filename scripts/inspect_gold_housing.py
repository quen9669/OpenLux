"""Inspecteur et validateur du Data Mart gold_housing.parquet."""

from __future__ import annotations

import duckdb

con = duckdb.connect()
print("=== CONTROLE DU DATA MART GOLD_HOUSING.PARQUET ===")
q_count = "SELECT count(*) FROM read_parquet('data/gold/gold_housing.parquet')"
total = con.execute(q_count).fetchone()[0]
print(f"Total rows: {total}")

types = con.execute(
    "SELECT record_type, count(*), min(reference_period), max(reference_period) "
    "FROM read_parquet('data/gold/gold_housing.parquet') GROUP BY 1 ORDER BY 1"
).fetchall()
for t in types:
    print(f"  - {t[0]}: {t[1]} lignes (période: {t[2]} à {t[3]})")

communes_count = con.execute(
    "SELECT count(distinct commune_name) FROM read_parquet('data/gold/gold_housing.parquet')"
).fetchone()[0]
print(f"Communes distinctes couvertes: {communes_count}")

cantons = con.execute(
    "SELECT distinct canton FROM read_parquet('data/gold/gold_housing.parquet') ORDER BY 1"
).fetchall()
print(f"Cantons couverts ({len(cantons)}): {[c[0] for c in cantons]}")

listings_http = con.execute(
    "SELECT count(*) FROM read_parquet('data/gold/gold_housing.parquet') "
    "WHERE record_type = 'LISTING' AND listing_url IS NOT NULL"
).fetchone()[0]
print(f"Annonces réelles avec URL: {listings_http}")

con.close()
