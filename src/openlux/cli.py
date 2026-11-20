"""Rôle : Interface CLI unifiée d'OpenLux Hub (run, rebuild, status, compact).
Entrées/Sorties : Reçoit les commandes terminal et orchestre collecte, dbt et qualité.
Hors-scope : N'héberge pas le serveur HTTP persistant (délégué à api/main.py).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from openlux.config import SourceConfig, load_sources_config
from openlux.core.collector import collect_source
from openlux.core.gold import export_gold_parquets
from openlux.core.monitoring import generate_status_markdown, send_alert_if_needed
from openlux.core.quality import (
    calculate_trust_score,
    get_dbt_validity_score,
    get_latest_source_health,
    init_obs_runs_table,
    record_run,
)


def _run_dbt_command(command: str) -> bool:
    """Exécute une sous-commande dbt (seed, run, test) depuis la racine du projet."""
    cmd = [
        sys.executable,
        "-m",
        "dbt.cli.main",
        command,
        "--project-dir",
        "dbt_project",
        "--profiles-dir",
        "dbt_project",
    ]
    res = subprocess.run(cmd, check=False)
    return res.returncode == 0


def _is_due(source: SourceConfig, last_checked_iso: str | None) -> bool:
    """Vérifie si la source a dépassé sa cadence d'exécution."""
    if not last_checked_iso:
        return True
    try:
        dt = datetime.fromisoformat(last_checked_iso)
        age = (datetime.now(UTC) - dt).total_seconds() / 60.0
        return age >= float(source.cadence_minutes)
    except Exception:
        return True


def run_pipeline(sources_filter: list[str] | None = None, due_only: bool = False) -> int:
    """Exécute la collecte, la transformation SQL dbt, les scores et le monitoring."""
    sources = load_sources_config()
    db_path = Path("data/openlux.duckdb")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    init_obs_runs_table(con)
    latest_health = get_latest_source_health(con)

    # Filtrage des sources ciblées
    selected = {
        sid: src
        for sid, src in sources.items()
        if (not sources_filter or sid in sources_filter)
        and (not due_only or _is_due(src, latest_health.get(sid, {}).get("last_checked_utc")))
    }
    run_id = str(uuid.uuid4())

    for sid, src in selected.items():
        prev = latest_health.get(sid, {})
        res = collect_source(
            src, last_sha256=prev.get("sha256"), last_changed_utc=prev.get("last_changed_utc")
        )
        val_score = get_dbt_validity_score(sid)
        metrics = calculate_trust_score(
            src, res.status, res.source_used, res.row_count, res.checked_at_utc, val_score
        )
        record_run(
            con,
            run_id,
            sid,
            "git_v1",
            metrics,
            res.row_count,
            res.checked_at_utc,
            res.changed_at_utc,
            res.sha256,
            res.error_message,
        )
        send_alert_if_needed(sid, metrics.status, [prev.get("status", "GOOD")])

    # Exécution des modèles dbt et bascule Parquet Gold atomique
    _run_dbt_command("seed")
    _run_dbt_command("run")
    _run_dbt_command("test")
    con.close()
    export_gold_parquets()

    con_read = duckdb.connect(str(db_path), read_only=True)
    generate_status_markdown(sources, get_latest_source_health(con_read))
    con_read.close()
    return 0


def rebuild_pipeline() -> int:
    """Rejoue 100 % hors-ligne les transformations dbt et la génération Gold depuis Bronze."""
    # POURQUOI : Rejeu déterministe complet sans aucun appel HTTP externe.
    sources = load_sources_config()
    db_path = Path("data/openlux.duckdb")
    _run_dbt_command("seed")
    _run_dbt_command("run")
    _run_dbt_command("test")
    export_gold_parquets()

    con = duckdb.connect(str(db_path))
    init_obs_runs_table(con)
    generate_status_markdown(sources, get_latest_source_health(con))
    con.close()
    print("Reconstruction hors-ligne Silver -> Gold terminée.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée principal de la CLI OpenLux."""
    parser = argparse.ArgumentParser(description="OpenLux Hub CLI")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Exécute la collecte et le pipeline")
    run_parser.add_argument("--sources", help="Liste de sources séparées par virgule")
    run_parser.add_argument(
        "--due", action="store_true", help="Exécute uniquement les sources dues"
    )

    subparsers.add_parser("rebuild", help="Rejoue le pipeline hors-ligne depuis Bronze")
    subparsers.add_parser("status", help="Affiche l'état des sources et regénère STATUS.md")
    subparsers.add_parser("compact", help="Compacte les archives Bronze")

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    if not args.command:
        parser.print_help()
        return 0

    if args.command == "run":
        srcs = [s.strip() for s in args.sources.split(",")] if args.sources else None
        return run_pipeline(srcs, args.due)
    if args.command == "rebuild":
        return rebuild_pipeline()
    if args.command == "status":
        db_path = Path("data/openlux.duckdb")
        con = duckdb.connect(str(db_path)) if db_path.exists() else duckdb.connect()
        init_obs_runs_table(con)
        generate_status_markdown(load_sources_config(), get_latest_source_health(con))
        con.close()
        print(Path("STATUS.md").read_text(encoding="utf-8"))
        return 0
    print(f"Commande '{args.command}' non active dans la phase actuelle.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
