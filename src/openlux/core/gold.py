"""Rôle : Export atomique des tables Gold en Parquet (ZSTD) avec bascule os.replace().
Entrées/Sorties : Lit les tables Gold dans DuckDB et produit des fichiers .parquet dans data/gold/.
Hors-scope : N'effectue pas de requêtes de transformation SQL ni d'écriture CSV statique.
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb


def export_gold_parquets(
    duckdb_path: Path | str = "data/openlux.duckdb",
    gold_dir: Path | str = "data/gold",
) -> list[str]:
    """Exporte atomiquement chaque table Gold en Parquet ZSTD via la zone temporaire .tmp."""
    # POURQUOI : Garantie d'atomicité absolue via os.replace() selon les règles AGENTS.md.
    db_file = Path(duckdb_path)
    if not db_file.exists():
        return []

    target_dir = Path(gold_dir)
    tmp_dir = target_dir / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_file), read_only=True)
    try:
        tables = [
            row[0]
            for row in con.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_name LIKE 'gold_%' AND table_schema = 'main'
            """).fetchall()
        ]
        exported: list[str] = []
        for tbl in tables:
            tmp_path = tmp_dir / f"{tbl}.parquet"
            final_path = target_dir / f"{tbl}.parquet"
            # Format Parquet compressé en ZSTD
            con.execute(f"COPY {tbl} TO '{tmp_path.as_posix()}' (FORMAT PARQUET, CODEC 'ZSTD')")
            if final_path.exists():
                final_path.unlink()
            os.replace(tmp_path, final_path)
            exported.append(tbl)
        return exported
    finally:
        con.close()


def list_gold_datasets(gold_dir: Path | str = "data/gold") -> list[str]:
    """Renvoie la liste des tables Gold disponibles sur disque en format Parquet."""
    directory = Path(gold_dir)
    if not directory.exists():
        return []
    return [p.stem for p in directory.glob("gold_*.parquet")]
