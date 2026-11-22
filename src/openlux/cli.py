"""Rôle : Interface CLI unifiée d'OpenLux Hub (run, rebuild, status, serve, schedule, mcp).
Entrées/Sorties : Reçoit les commandes terminal et orchestre collecte, dbt et planification.
Hors-scope : N'héberge pas le serveur HTTP persistant (délégué à api/main.py).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from openlux.config import SourceConfig, load_sources_config
from openlux.core.collector import CollectorResult, collect_source
from openlux.core.gold import export_gold_parquets
from openlux.core.monitoring import generate_status_markdown, send_alert_if_needed
from openlux.core.quality import (
    calculate_trust_score,
    get_dbt_validity_score,
    get_latest_source_health,
    init_obs_runs_table,
    record_run,
)


def _dbt(cmd: str, *args: str) -> bool:
    args_list = [
        "-m",
        "dbt.cli.main",
        cmd,
        *args,
        "--project-dir",
        "dbt_project",
        "--profiles-dir",
        "dbt_project",
    ]
    return subprocess.run([sys.executable, *args_list], check=False).returncode == 0


_run_dbt_command = _dbt


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
    try:
        init_obs_runs_table(con)
        health, r_id = get_latest_source_health(con), str(uuid.uuid4())
        selected = {
            s: c
            for s, c in sources.items()
            if (not sources_filter or s in sources_filter)
            and (not due_only or _is_due(c, health.get(s, {}).get("last_checked_utc")))
        }
        if not selected:
            return 0

        for sid, src in selected.items():
            prev = health.get(sid, {})
            try:
                res = collect_source(
                    src,
                    last_sha256=prev.get("sha256"),
                    last_changed_utc=prev.get("last_changed_utc"),
                )
            except Exception as exc:
                now_s = datetime.now(UTC).isoformat()
                res = CollectorResult(
                    sid, "ERROR", "none", "", 0, b"", None, now_s, now_s, str(exc)
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
    finally:
        con.close()

    for c in [("seed", "--full-refresh"), ("run",), ("test",)]:
        _dbt(*c)
    export_gold_parquets()
    with duckdb.connect(str(db_p), read_only=True) as con_r:
        generate_status_markdown(sources, get_latest_source_health(con_r))
    return 0


def schedule_pipeline(interval_seconds: int = 60) -> int:
    print(f"OpenLux Scheduler démarré ({interval_seconds}s). Ctrl+C pour quitter.")
    try:
        while True:
            run_pipeline(due_only=True)
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        pass
    return 0


def rebuild_pipeline() -> int:
    for c in [("seed", "--full-refresh"), ("run",), ("test",)]:
        _dbt(*c)
    export_gold_parquets()
    with duckdb.connect("data/openlux.duckdb") as con:
        init_obs_runs_table(con)
        generate_status_markdown(load_sources_config(), get_latest_source_health(con))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OpenLux Hub CLI")
    sub = parser.add_subparsers(dest="cmd")
    r_p = sub.add_parser("run")
    r_p.add_argument("--sources")
    r_p.add_argument("--due", action="store_true")
    sch = sub.add_parser("schedule")
    sch.add_argument("--interval", type=int, default=60, help="Intervalle en secondes")
    for c in ["rebuild", "status", "compact", "mcp"]:
        sub.add_parser(c)
    pub = sub.add_parser("publish")
    pub.add_argument("--live", dest="dry_run", action="store_false", default=True)
    srv = sub.add_parser("serve", aliases=["api"])
    srv.add_argument("--host", default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8000)
    srv.add_argument("--auto-sync", action="store_true")

    a = parser.parse_args(argv if argv is not None else sys.argv[1:])
    if not a.cmd:
        parser.print_help()
        return 0
    if a.cmd == "run":
        return run_pipeline([s.strip() for s in a.sources.split(",")] if a.sources else None, a.due)
    if a.cmd == "schedule":
        return schedule_pipeline(a.interval)
    if a.cmd == "rebuild":
        return rebuild_pipeline()
    if a.cmd in ("serve", "api"):
        if getattr(a, "auto_sync", False):
            os.environ["OPENLUX_AUTO_SYNC"] = "1"
        import uvicorn

        uvicorn.run("openlux.api.main:app", host=a.host, port=a.port)
        return 0
    if a.cmd == "mcp":
        from openlux.mcp.server import mcp

        mcp.run()
        return 0
    if a.cmd == "compact":
        from openlux.publish.opendata_lu import compact_bronze_archives

        print(f"Compactage terminé : {compact_bronze_archives(Path('data/bronze'))} archives.")
        return 0
    if a.cmd == "publish":
        from openlux.publish.opendata_lu import publish_to_data_public_lu

        st = publish_to_data_public_lu(dry_run=a.dry_run)["status"]
        print(f"Publication data.public.lu ({st}).")
        return 0
    if a.cmd == "status":
        db = "data/openlux.duckdb" if Path("data/openlux.duckdb").exists() else ":memory:"
        with duckdb.connect(db) as con:
            init_obs_runs_table(con)
            generate_status_markdown(load_sources_config(), get_latest_source_health(con))
        print(Path("STATUS.md").read_text(encoding="utf-8"))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
