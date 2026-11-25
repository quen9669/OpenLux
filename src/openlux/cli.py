"""Rôle : Interface CLI unifiée d'OpenLux Hub (run, rebuild, status, serve, schedule, mcp).
Entrées/Sorties : Reçoit les commandes terminal et orchestre collecte, dbt et planification.
Hors-scope : N'héberge pas le serveur HTTP persistant (délégué à api/main.py).
"""

from __future__ import annotations

import argparse
import contextlib
import gzip
import os
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

from openlux.config import SourceConfig, load_sources_config
from openlux.core.collector import CollectorResult, collect_source
from openlux.core.gold import export_gold_parquets
from openlux.core.monitoring import generate_status_markdown, send_alert_if_needed
from openlux.core.quality import (
    calculate_trust_score,
    get_latest_source_health,
    get_source_run_history,
    init_obs_runs_table,
    record_run,
)


def _run_dbt_command(cmd: str, *args: str) -> bool:
    # POURQUOI : dbt-duckdb résout seeds/ et ../data/ depuis le cwd : on exécute depuis dbt_project/
    opt = ["--project-dir", ".", "--profiles-dir", "."]
    cmd_line = [sys.executable, "-m", "dbt.cli.main", cmd, *args, *opt]
    return subprocess.run(cmd_line, cwd="dbt_project").returncode == 0


def ensure_bronze_placeholders(sources: dict[str, SourceConfig]) -> None:
    """Bronze vide ('[]') pour toute source jamais collectée : 0 ligne, jamais de fixture."""
    for sid in sources:
        d = Path("data/bronze") / sid
        if not any(d.glob("**/*.json.gz")):
            d.mkdir(parents=True, exist_ok=True)
            (d / "empty.json.gz").write_bytes(gzip.compress(b"[]"))


def _connect_db(path: str = "data/openlux.duckdb", read_only: bool = False):
    for _ in range(7):
        with contextlib.suppress(Exception):
            return duckdb.connect(path, read_only=read_only)
        time.sleep(0.3)
    return duckdb.connect(path, read_only=read_only)


def _is_due(source: SourceConfig, last_iso: str | None) -> bool:
    if not last_iso:
        return True
    with contextlib.suppress(Exception):
        age = (datetime.now(UTC) - datetime.fromisoformat(last_iso)).total_seconds() / 60.0
        return age >= float(source.cadence_minutes)
    return True


def _collect_and_record(
    con: duckdb.DuckDBPyConnection,
    sid: str,
    src: SourceConfig,
    r_id: str,
    prev: dict[str, Any],
    past: list[str],
) -> None:
    try:
        res = collect_source(
            src, last_sha256=prev.get("sha256"), last_changed_utc=prev.get("last_changed_utc")
        )
    except Exception as exc:
        n = datetime.now(UTC).isoformat()
        res = CollectorResult(sid, "ERROR", "none", "", 0, b"", None, n, n, str(exc))
    m = calculate_trust_score(src, res.status, res.source_used, res.row_count, res.checked_at_utc)
    meta = (res.checked_at_utc, res.changed_at_utc, res.sha256, res.error_message)
    record_run(con, r_id, sid, "git_v1", m, res.row_count, *meta)
    send_alert_if_needed(sid, m.status, past)


def run_pipeline(sources_filter: list[str] | None = None, due_only: bool = False) -> int:
    sources, db_p = load_sources_config(), Path("data/openlux.duckdb")
    db_p.parent.mkdir(parents=True, exist_ok=True)
    with _connect_db(str(db_p)) as con:
        init_obs_runs_table(con)
        health, r_id = get_latest_source_health(con), str(uuid.uuid4())
        history = get_source_run_history(con)
        selected = {
            s: c
            for s, c in sources.items()
            if (sources_filter is None or s in sources_filter)
            and (not due_only or _is_due(c, health.get(s, {}).get("last_checked_utc")))
        }
        for sid, src in selected.items():
            past = [h["status"] for h in history.get(sid, [])]
            _collect_and_record(con, sid, src, r_id, health.get(sid, {}), past)
    ensure_bronze_placeholders(sources)
    for c in [("seed", "--full-refresh"), ("run",), ("test",)]:
        if not _run_dbt_command(*c):
            # POURQUOI : un modèle ou un test dbt en échec ne doit jamais être publié comme sain
            print(f"dbt {c[0]} en échec : export Gold annulé.", file=sys.stderr)
            return 1
    export_gold_parquets()
    from openlux.publish.opendata_lu import publish_to_data_public_lu, write_site_catalog

    publish_to_data_public_lu(dry_run=True)
    write_site_catalog()
    with _connect_db(str(db_p), read_only=True) as con_r:
        generate_status_markdown(sources, get_latest_source_health(con_r))
    return 0


def schedule_pipeline(interval_seconds: int = 60) -> int:
    print(f"OpenLux Scheduler démarré ({interval_seconds}s). Ctrl+C pour quitter.")
    with contextlib.suppress(KeyboardInterrupt):
        while True:
            run_pipeline(due_only=True)
            time.sleep(interval_seconds)
    return 0


def rebuild_pipeline() -> int:
    return run_pipeline(sources_filter=["__none__"])


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="OpenLux Hub CLI")
    sub = p.add_subparsers(dest="cmd")
    r = sub.add_parser("run")
    r.add_argument("--sources")
    r.add_argument("--due", action="store_true")
    sub.add_parser("schedule").add_argument("--interval", type=int, default=60)
    for c in ["rebuild", "status", "mcp"]:
        sub.add_parser(c)
    pub = sub.add_parser("publish")
    pub.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    pub.add_argument("--live", dest="dry_run", action="store_false")
    srv = sub.add_parser("serve", aliases=["api"])
    srv.add_argument("--host", default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8000)
    srv.add_argument("--auto-sync", action="store_true")
    return p


def _dispatch(a: argparse.Namespace) -> int:
    if a.cmd == "run":
        srcs = [s.strip() for s in a.sources.split(",")] if a.sources else None
        return run_pipeline(srcs, a.due)
    if a.cmd == "schedule":
        return schedule_pipeline(a.interval)
    if a.cmd == "rebuild":
        return rebuild_pipeline()
    if a.cmd in ("serve", "api"):
        if getattr(a, "auto_sync", False):
            os.environ["OPENLUX_AUTO_SYNC"] = "1"
        import uvicorn

        uvicorn.run("openlux.api.main:app", host=a.host, port=a.port)
    elif a.cmd == "mcp":
        from openlux.mcp.server import mcp

        mcp.run()
    elif a.cmd == "publish":
        from openlux.publish.opendata_lu import publish_to_data_public_lu

        res = publish_to_data_public_lu(dry_run=a.dry_run)
        print(f"Publication data.public.lu ({res['status']}).")
    elif a.cmd == "status":
        db = "data/openlux.duckdb" if Path("data/openlux.duckdb").exists() else ":memory:"
        with _connect_db(db, read_only=True) as con:
            with contextlib.suppress(Exception):
                init_obs_runs_table(con)
            generate_status_markdown(load_sources_config(), get_latest_source_health(con))
        print(Path("STATUS.md").read_text(encoding="utf-8"))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = _build_parser()
    a = p.parse_args(argv if argv is not None else sys.argv[1:])
    return _dispatch(a) if a.cmd else (p.print_help() or 0)


if __name__ == "__main__":
    sys.exit(main())
