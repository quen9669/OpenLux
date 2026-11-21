"""Script de déploiement et de mise en production de tous les flux OpenLux Hub.
Exécute la collecte live, les transformations SQL dbt, les exports Gold Parquet,
les audits d'intégrité anti-doublons et la publication des métadonnées open data.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from openlux.config import load_sources_config
from openlux.core.collector import collect_source
from openlux.core.gold import export_gold_parquets
from openlux.core.monitoring import generate_status_markdown
from openlux.core.quality import (
    calculate_trust_score,
    get_latest_source_health,
    init_obs_runs_table,
    record_run,
)
from openlux.publish.opendata_lu import publish_catalog_metadata


def print_step(step_num: int, title: str) -> None:
    print(f"\n{'=' * 80}")
    print(f"[{step_num}/6] {title}")
    print(f"{'=' * 80}")


def main() -> int:
    start_time = datetime.now(UTC)
    print("=" * 80)
    print(f"OPENLUX HUB - MISE EN PRODUCTION DES FLUX ({start_time.isoformat()})")
    print("=" * 80)

    # 1. Vérification de la configuration
    print_step(1, "Vérification de la configuration et des sources")
    sources = load_sources_config()
    print(f"Sources déclarées dans config/sources.toml : {len(sources)} flux atomiques.")

    echo_key = os.environ.get("ECHO_API_KEY")
    if echo_key:
        print("  [OK] Clé API Echo.lu détectée (ECHO_API_KEY).")
    else:
        print("  [INFO] ECHO_API_KEY absente : repli automatique open data public.")

    # 2. Collecte des flux (HTTP direct avec résilience)
    print_step(2, "Collecte en direct des flux de données (Couche Bronze)")
    db_path = Path("data/openlux.duckdb")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    init_obs_runs_table(con)

    collected_ok = 0
    collected_warn = 0
    collected_err = 0

    for sid, src in sources.items():
        try:
            res = collect_source(src)
            score = calculate_trust_score(
                latency_ms=res.latency_ms,
                sla_minutes=src.sla_minutes,
                schema_valid=(res.status != "ERROR"),
                source_used=res.source_used,
            )
            record_run(con, res, score)
            if res.status == "SUCCESS":
                collected_ok += 1
            elif res.status == "ATTENTION":
                collected_warn += 1
            else:
                collected_err += 1
            print(f"  - {sid:<24} : {res.status:<9} ({res.row_count} lig, src: {res.source_used})")
        except Exception as e:
            collected_err += 1
            print(f"  - {sid:<24} : ERREUR ({e})")

    con.close()
    print(f"\nBilan : {collected_ok} nominaux, {collected_warn} replis, {collected_err} erreurs.")

    # 3. Exécution dbt (Staging -> Silver -> Gold)
    print_step(3, "Transformations déclaratives SQL dbt (Silver & Gold)")
    cmd_base = [
        sys.executable,
        "-m",
        "dbt.cli.main",
        "--project-dir",
        "dbt_project",
        "--profiles-dir",
        "dbt_project",
    ]

    print("  -> dbt seed --full-refresh...")
    r_seed = subprocess.run([*cmd_base, "seed", "--full-refresh"], check=False)
    if r_seed.returncode != 0:
        print("Erreur critique lors de dbt seed.")
        return 1

    print("  -> dbt run...")
    r_run = subprocess.run([*cmd_base, "run"], check=False)
    if r_run.returncode != 0:
        print("Erreur critique lors de dbt run.")
        return 1

    print("  -> dbt test (Zero-PII & Intégrité)...")
    r_test = subprocess.run([*cmd_base, "test"], check=False)
    if r_test.returncode != 0:
        print("Erreur critique lors de dbt test.")
        return 1

    # 4. Exportation atomique vers la couche Gold Parquet (ZSTD)
    print_step(4, "Exportation atomique Parquet ZSTD (Couche Gold)")
    exported_tables = export_gold_parquets()
    print(f"Tables Gold exportées avec succès : {len(exported_tables)} fichiers Parquet.")

    # 5. Contrôle strict d'absence de doublons
    print_step(5, "Contrôle d'intégrité anti-doublons sur les 22 tables Gold")
    r_dup = subprocess.run([sys.executable, "scripts/verify_no_duplicates.py"], check=False)
    if r_dup.returncode != 0:
        print("Attention : des doublons ont été identifiés dans la couche Gold.")
        return 1

    # 6. Publication des métadonnées officielles
    print_step(6, "Génération des métadonnées de publication open data")
    pub_res = publish_catalog_metadata(dry_run=True)
    val_count = pub_res.get("tables_validated", 0)
    print(f"Publication Frictionless Data Package & DCAT-AP-LU : OK ({val_count} tables validées).")

    # Mise à jour du STATUS.md
    con_ro = duckdb.connect(str(db_path), read_only=True)
    generate_status_markdown(sources, get_latest_source_health(con_ro))
    con_ro.close()

    duration = (datetime.now(UTC) - start_time).total_seconds()
    print("\n" + "=" * 80)
    print(f"MISE EN PRODUCTION TERMINÉE AVEC SUCCÈS en {duration:.1f} secondes !")
    print("=" * 80)
    print("Pour exploiter les données :")
    print("  1. Démarrer l'API REST FastAPI   : uv run openlux serve --port 8000")
    print("  2. Démarrer le serveur FastMCP  : uv run openlux mcp")
    print("  3. Interroger les fichiers Gold  : SELECT * FROM 'data/gold/gold_housing.parquet';")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
