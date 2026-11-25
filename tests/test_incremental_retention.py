"""Rétention incrémentale Gold : aucune clé passée n'est supprimée, chaque clé garde sa dernière
version (collected_at_utc), les nouvelles observations s'accumulent.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from openlux.core.gold import export_gold_parquets


def _count(p: Path, where: str = "TRUE") -> int:
    with duckdb.connect() as con:
        q = f"SELECT count(*) FROM read_parquet('{p.as_posix()}') WHERE {where}"
        return con.execute(q).fetchone()[0]


def test_zero_deletion_and_latest_version_per_key(tmp_path: Path) -> None:
    db, gold = tmp_path / "t.duckdb", tmp_path / "gold"
    gold.mkdir()
    pq = gold / "gold_mobility_parkings.parquet"
    ddl = (
        "CREATE OR REPLACE TABLE gold_mobility_parkings (parking_id VARCHAR, "
        "observed_at_utc TIMESTAMP, available_spaces INTEGER, collected_at_utc TIMESTAMP)"
    )
    with duckdb.connect(str(db)) as con:
        con.execute(ddl)
        con.execute(
            "INSERT INTO gold_mobility_parkings VALUES "
            "('20', '2026-11-24 10:00', 50, '2026-11-24 10:01'),"
            "('14', '2026-11-24 10:00', 0, '2026-11-24 10:01')"
        )
    export_gold_parquets(db, gold)
    assert _count(pq) == 2

    # Run suivant : la table DuckDB ne contient plus que le nouveau relevé + une correction
    with duckdb.connect(str(db)) as con:
        con.execute(ddl)
        con.execute(
            "INSERT INTO gold_mobility_parkings VALUES "
            "('20', '2026-11-24 11:00', 42, '2026-11-24 11:01'),"
            "('14', '2026-11-24 10:00', 7, '2026-11-24 11:02')"
        )
    export_gold_parquets(db, gold)
    assert _count(pq) == 3  # 2 anciennes clés conservées + 1 nouvelle
    assert _count(pq, "parking_id = '14' AND available_spaces = 7") == 1  # dernière version
    assert _count(pq, "parking_id = '14' AND available_spaces = 0") == 0  # pas de doublon

    # Run à vide : rien n'est perdu
    with duckdb.connect(str(db)) as con:
        con.execute(ddl)
    export_gold_parquets(db, gold)
    assert _count(pq) == 3
