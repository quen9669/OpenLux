"""Rôle : Interface CLI unifiée d'OpenLux Hub (run, rebuild, status, compact, serve, mcp).
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


def _run_dbt_command(cmd: str, *args: str) -> bool:
    full = [
        sys.executable,
        "-m",
        "dbt.cli.main",
        cmd,
        *args,
        "--project-dir",
        "dbt_project",
        "--profiles-dir",
        "dbt_project",
    ]
    return subprocess.run(full, check=False).returncode == 0


_dbt = _run_dbt_command


def _is_due(source: SourceConfig, last_iso: str | None) -> bool:
    if not last_iso:
        return True
    try:
        return (
            (datetime.now(UTC) - datetime.fromisoformat(last_iso)).total_seconds() / 60.0
        ) >= float(source.cadence_minutes)
    except Exception:
        return True


def run_pipeline(sources_filter: list[str] | None = None, due_only: bool = False) -> int:
    sources, db_p = load_sources_config(), Path("data/openlux.duckdb")
    db_p.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_p))
    init_obs_runs_table(con)
    health, r_id = get_latest_source_health(con), str(uuid.uuid4())
    selected = {
        s: c
        for s, c in sources.items()
        if (not sources_filter or s in sources_filter)
        and (not due_only or _is_due(c, health.get(s, {}).get("last_checked_utc")))
    }

    for sid, src in selected.items():
        prev = health.get(sid, {})
        res = collect_source(
            src, last_sha256=prev.get("sha256"), last_changed_utc=prev.get("last_changed_utc")
        )
        val_score = get_dbt_validity_score(sid)
        metrics = calculate_trust_score(
            src, res.status, res.source_used, res.row_count, res.checked_at_utc, val_score
        )
        record_run(
            con,
            r_id,
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

    _dbt("seed", "--full-refresh")
    _dbt("run")
    _dbt("test")
    con.close()
    export_gold_parquets()
    con_r = duckdb.connect(str(db_p), read_only=True)
    generate_status_markdown(sources, get_latest_source_health(con_r))
    con_r.close()
    return 0


def rebuild_pipeline() -> int:
    _dbt("seed", "--full-refresh")
    _dbt("run")
    _dbt("test")
    export_gold_parquets()
    db_p = Path("data/openlux.duckdb")
    con = duckdb.connect(str(db_p))
    init_obs_runs_table(con)
    generate_status_markdown(load_sources_config(), get_latest_source_health(con))
    con.close()
    print("Reconstruction hors-ligne Silver -> Gold terminée.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OpenLux Hub CLI")
    sub = parser.add_subparsers(dest="cmd")
    r_p = sub.add_parser("run")
    r_p.add_argument("--sources")
    r_p.add_argument("--due", action="store_true")
    for c in ["rebuild", "status", "compact", "mcp"]:
        sub.add_parser(c)
    pub = sub.add_parser("publish")
    pub.add_argument("--dry-run", action="store_true", default=True)
    pub.add_argument("--live", dest="dry_run", action="store_false")
    srv = sub.add_parser("serve", aliases=["api"])
    srv.add_argument("--host", default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8000)

    a = parser.parse_args(argv if argv is not None else sys.argv[1:])
    if not a.cmd:
        parser.print_help()
        return 0
    if a.cmd == "run":
        return run_pipeline([s.strip() for s in a.sources.split(",")] if a.sources else None, a.due)
    if a.cmd == "rebuild":
        return rebuild_pipeline()
    if a.cmd in ("serve", "api"):
        import uvicorn

        uvicorn.run("openlux.api.main:app", host=a.host, port=a.port)
        return 0
    if a.cmd == "mcp":
        from openlux.mcp.server import mcp

        mcp.run()
        return 0
    if a.cmd == "compact":
        from openlux.publish.opendata_lu import compact_bronze_archives

        cnt = compact_bronze_archives(Path("data/bronze"))
        print(f"Compactage terminé : {cnt} archives traitées.")
        return 0
    if a.cmd == "publish":
        from openlux.publish.opendata_lu import publish_to_data_public_lu

        st = publish_to_data_public_lu(dry_run=a.dry_run)["status"]
        print(f"Publication data.public.lu ({st}).")
        return 0
    if a.cmd == "status":
        db_p = Path("data/openlux.duckdb")
        con = duckdb.connect(str(db_p)) if db_p.exists() else duckdb.connect()
        init_obs_runs_table(con)
        generate_status_markdown(load_sources_config(), get_latest_source_health(con))
        con.close()
        print(Path("STATUS.md").read_text(encoding="utf-8"))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
