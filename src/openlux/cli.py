"""Rôle : Interface CLI unifiée d'OpenLux Hub (run, rebuild, status, serve, schedule, mcp).
Entrées/Sorties : Reçoit les commandes terminal et orchestre collecte, dbt et planification.
Hors-scope : N'héberge pas le serveur HTTP persistant (délégué à api/main.py).
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
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
from openlux.core.collector import CollectorResult, _process_payload, _write_bronze, collect_source
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
    opt = ["--project-dir", "dbt_project", "--profiles-dir", "dbt_project"]
    return subprocess.run([sys.executable, "-m", "dbt.cli.main", cmd, *args, *opt]).returncode == 0


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


def ensure_bronze_baseline(sources: dict[str, SourceConfig]) -> None:
    fdir = Path("tests/fixtures")
    if not fdir.exists():
        return
    for sid, src in sources.items():
        if any((Path("data/bronze") / sid).glob("**/*.gz")):
            continue
        c = (
            list(fdir.glob(f"{sid}_sample.*"))
            or list(fdir.glob(f"{sid.replace('_lu', '')}_sample.*"))
            or ([fdir / "cita_datex2_sample.xml"] if "cita" in sid else [])
        )
        if c and c[0].exists():
            with contextlib.suppress(Exception):
                p, cnt, ext = _process_payload(src, c[0].read_bytes())
                _write_bronze(sid, p, ext, hashlib.sha256(p).hexdigest(), datetime.now(UTC), cnt)


def _collect_and_record(
    con: duckdb.DuckDBPyConnection, sid: str, src: SourceConfig, r_id: str, prev: dict[str, Any]
) -> None:
    try:
        res = collect_source(src, prev.get("sha256"), prev.get("last_changed_utc"))
    except Exception as exc:
        n = datetime.now(UTC).isoformat()
        res = CollectorResult(sid, "ERROR", "none", "", 0, b"", None, n, n, str(exc))
    val = get_dbt_validity_score(sid)
    m = calculate_trust_score(
        src, res.status, res.source_used, res.row_count, res.checked_at_utc, val
    )
    meta = (res.checked_at_utc, res.changed_at_utc, res.sha256, res.error_message)
    record_run(con, r_id, sid, "git_v1", m, res.row_count, *meta)
    send_alert_if_needed(sid, m.status, [prev.get("status", "GOOD")])


def run_pipeline(sources_filter: list[str] | None = None, due_only: bool = False) -> int:
    sources, db_p = load_sources_config(), Path("data/openlux.duckdb")
    db_p.parent.mkdir(parents=True, exist_ok=True)
    with _connect_db(str(db_p)) as con:
        init_obs_runs_table(con)
        health, r_id = get_latest_source_health(con), str(uuid.uuid4())
        selected = {
            s: c
            for s, c in sources.items()
            if (sources_filter is None or s in sources_filter)
            and (not due_only or _is_due(c, health.get(s, {}).get("last_checked_utc")))
        }
        for sid, src in selected.items():
            _collect_and_record(con, sid, src, r_id, health.get(sid, {}))
    ensure_bronze_baseline(sources)
    for c in [("seed", "--full-refresh"), ("run",), ("test",)]:
        _run_dbt_command(*c)
    export_gold_parquets()
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
    for c in ["rebuild", "status", "compact", "mcp"]:
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
    elif a.cmd == "compact":
        from openlux.publish.opendata_lu import compact_bronze_archives

        print(f"Compactage terminé : {compact_bronze_archives(Path('data/bronze'))} archives.")
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
