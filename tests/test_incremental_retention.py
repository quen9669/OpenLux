"""Test de validation stricte de l'ingestion incrémentale sans suppression (Zero Deletion)
et de l'accroissement continu des lignes à chaque rechargement (hourly increment) 100 % isolé.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb

from openlux.core.gold import export_gold_parquets


def test_incremental_zero_deletion_and_new_rows_accumulation(tmp_path: Path) -> None:
    # 1. Création d'une base de test DuckDB totalement isolée dans tmp_path
    tmp_db = tmp_path / "test.duckdb"
    gold_dir = tmp_path / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)

    t0 = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    with duckdb.connect(str(tmp_db)) as con:
        con.execute("""
            CREATE TABLE gold_mobility_veloh (
                station_id VARCHAR, station_name VARCHAR, observed_at_utc TIMESTAMP,
                available_bikes INTEGER, available_stands INTEGER,
                broken_or_disabled_stands INTEGER, total_capacity INTEGER,
                occupancy_rate DOUBLE, is_installed BOOLEAN, is_renting BOOLEAN,
                hourly_rate_eur DECIMAL(10,2), tariff_details VARCHAR,
                opening_hours VARCHAR, lat DOUBLE, lon DOUBLE, commune_lau VARCHAR,
                canton VARCHAR, source_id VARCHAR
            );
            CREATE TABLE gold_mobility_parkings (
                parking_id VARCHAR, parking_name VARCHAR, observed_at_utc TIMESTAMP,
                available_spaces INTEGER, total_capacity INTEGER,
                occupied_spaces INTEGER, occupancy_rate DOUBLE, trend INTEGER,
                is_open BOOLEAN, is_full BOOLEAN, is_out_of_order BOOLEAN,
                is_free_pr BOOLEAN, hourly_rate_eur DECIMAL(10,2),
                tariff_details VARCHAR, opening_hours VARCHAR, lat DOUBLE,
                lon DOUBLE, commune_lau VARCHAR, canton VARCHAR, source_id VARCHAR
            );
        """)
        # Injection du lot initial T0
        con.execute(f"""
            INSERT INTO gold_mobility_veloh VALUES
            ('VELOH_01', 'Hamilius', '{t0}', 10, 5, 1, 16, 62.5, true, true, 0.00,
             'VDL', '24/7', 49.61, 6.13, 'LU0704', 'Luxembourg', 'veloh_stations'),
            ('VELOH_02', 'Glacis', '{t0}', 8, 8, 2, 18, 44.4, true, true, 0.00,
             'VDL', '24/7', 49.62, 6.12, 'LU0704', 'Luxembourg', 'veloh_stations');

            INSERT INTO gold_mobility_parkings VALUES
            ('PARK_01', 'Knuedler', '{t0}', 50, 200, 150, 75.0, 1, true, false, false,
             false, 2.80, 'VDL', '24/7', 49.61, 6.13, 'LU0704', 'Luxembourg', 'parkings_vdl'),
            ('PARK_02', 'Glacis', '{t0}', 200, 500, 300, 60.0, 0, true, false, false,
             false, 2.00, 'VDL', '24/7', 49.62, 6.12, 'LU0704', 'Luxembourg', 'parkings_vdl');
        """)

    # 2. Run 1: Export initial vers le répertoire Gold de test
    exported = export_gold_parquets(duckdb_path=tmp_db, gold_dir=gold_dir)
    assert set(exported) == {"gold_mobility_veloh", "gold_mobility_parkings"}

    # 3. Vérification des volumes initiaux au Run 1
    with duckdb.connect() as con:
        v_p = (gold_dir / "gold_mobility_veloh.parquet").as_posix()
        p_p = (gold_dir / "gold_mobility_parkings.parquet").as_posix()
        v_cnt_run1 = con.execute(f"SELECT count(*) FROM read_parquet('{v_p}')").fetchone()[0]
        p_cnt_run1 = con.execute(f"SELECT count(*) FROM read_parquet('{p_p}')").fetchone()[0]
        assert v_cnt_run1 == 2
        assert p_cnt_run1 == 2

    # 4. Run 2: Ré-exécution sans nouvelles données
    export_gold_parquets(duckdb_path=tmp_db, gold_dir=gold_dir)

    # 5. Vérification Zero Deletion stricte (aucune ligne perdue, volume identique)
    with duckdb.connect() as con:
        v_cnt_run2 = con.execute(f"SELECT count(*) FROM read_parquet('{v_p}')").fetchone()[0]
        p_cnt_run2 = con.execute(f"SELECT count(*) FROM read_parquet('{p_p}')").fetchone()[0]
        assert v_cnt_run2 == v_cnt_run1 == 2
        assert p_cnt_run2 == p_cnt_run1 == 2

    # 6. Simulation du rechargement après 1 heure (H+1) avec de nouvelles observations horaires
    t1 = (datetime.now(UTC) + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    with duckdb.connect(str(tmp_db)) as con:
        con.execute(f"""
            INSERT INTO gold_mobility_veloh VALUES
            ('VELOH_01', 'Hamilius', '{t1}', 12, 3, 1, 16, 75.0, true, true, 0.00,
             'VDL', '24/7', 49.61, 6.13, 'LU0704', 'Luxembourg', 'veloh_stations');

            INSERT INTO gold_mobility_parkings VALUES
            ('PARK_01', 'Knuedler', '{t1}', 40, 200, 160, 80.0, 1, true, false, false,
             false, 2.80, 'VDL', '24/7', 49.61, 6.13, 'LU0704', 'Luxembourg', 'parkings_vdl');
        """)

    # 7. Run 3: Export incrémental Gold
    export_gold_parquets(duckdb_path=tmp_db, gold_dir=gold_dir)

    # 8. Vérification de l'accumulation continue : new_cnt == initial_cnt + 1 et zéro suppression
    with duckdb.connect() as con:
        v_cnt_run3 = con.execute(f"SELECT count(*) FROM read_parquet('{v_p}')").fetchone()[0]
        p_cnt_run3 = con.execute(f"SELECT count(*) FROM read_parquet('{p_p}')").fetchone()[0]
        assert v_cnt_run3 == 3, f"Veloh: attendu 3, obtenu {v_cnt_run3}"
        assert p_cnt_run3 == 3, f"Parkings: attendu 3, obtenu {p_cnt_run3}"

        # Vérification que l'historique T0 et le nouveau relevé T1 coexistent
        q_h1 = (
            f"SELECT available_bikes, broken_or_disabled_stands "
            f"FROM read_parquet('{v_p}') WHERE observed_at_utc = '{t1}'"
        )
        h1_v = con.execute(q_h1).fetchone()
        assert h1_v == (12, 1)

        # Invariant physique garanti sur toutes les lignes : bikes + stands + broken == capacity
        invariants = con.execute(f"""
            SELECT count(*) FROM read_parquet('{v_p}')
            WHERE (available_bikes + available_stands + broken_or_disabled_stands) != total_capacity
        """).fetchone()[0]
        assert invariants == 0, "Invariant de capacité violé !"
