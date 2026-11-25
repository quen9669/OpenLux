"""Rôle : Génération de STATUS.md, payload de monitoring et export Prometheus.
Entrées/Sorties : Lit les métriques de santé des sources et produit STATUS.md / JSON / Prometheus.
Hors-scope : N'exécute pas les collecteurs ni les calculs de scores qualité.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from openlux.config import SourceConfig

ICONS = {
    "GOOD": "🟢 `GOOD`",
    "ATTENTION": "🟡 `ATTENTION`",
    "ERROR": "🔴 `ERROR`",
    "NOT_TESTED": "⚪ `NOT_TESTED`",
}


def generate_status_markdown(
    sources: dict[str, SourceConfig],
    health_map: dict[str, dict[str, Any]],
    output_path: Path | str = "STATUS.md",
) -> str:
    hdr = (
        "# État de Santé des Sources OpenLux Hub\n\n"
        "> Ce fichier est mis à jour à chaque exécution du pipeline (`openlux run`).\n\n"
        "| Domaine | Source ID | État | Trust Score | Source Active | Lignes | "
        "Dernier contrôle (UTC) | Dernière mutation (UTC) | Licence |\n"
        "| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- |\n"
    )
    rows = []
    for sid, src in sources.items():
        info = health_map.get(sid, {})
        st = info.get("status", "NOT_TESTED")
        sc = f"{info['trust_score']:.1f}" if "trust_score" in info and st != "NOT_TESTED" else "-"
        act = info.get("source_used", "primary" if st == "GOOD" else "-")
        r, c, m = (
            str(info.get("row_count", "-")),
            info.get("last_checked_utc", "-"),
            info.get("last_changed_utc", "-"),
        )
        ic, lic = ICONS.get(st, f"`{st}`"), src.license_spdx
        rows.append(
            f"| *{src.domain}* | `{sid}` | {ic} | {sc} | {act} | {r} | {c} | {m} | `{lic}` |"
        )
    legend = (
        "\n\n*Légende :* 🟢 `GOOD` (85-100) | 🟡 `ATTENTION` (60-84) | "
        "🔴 `ERROR` (<60) | ⚪ `NOT_TESTED`\n"
    )
    content = hdr + "\n".join(rows) + legend
    Path(output_path).write_text(content, encoding="utf-8")
    return content


def build_monitoring_payload(
    sources: dict[str, SourceConfig],
    health_map: dict[str, dict[str, Any]],
    history_map: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    now, items = datetime.now(UTC), []
    for sid, src in sources.items():
        h = health_map.get(sid, {})
        st, last_chk = h.get("status", "NOT_TESTED"), h.get("last_checked_utc")
        cadence = float(src.cadence_minutes)
        next_dt_iso, rem_sec, is_due = None, 0.0, True
        if last_chk:
            try:
                ndt = datetime.fromisoformat(last_chk) + timedelta(minutes=cadence)
                next_dt_iso, rem_sec = ndt.isoformat(), round((ndt - now).total_seconds())
                is_due = rem_sec <= 0
            except Exception:
                pass
        used = "backup" if (h.get("score_source") == 80.0 or st == "ATTENTION") else "primary"
        url = src.backup.url if (used == "backup" and src.backup) else src.primary.url
        rows, min_r, score = (
            int(h.get("row_count", 0)),
            int(src.quality.min_rows),
            float(h.get("trust_score", 100.0)),
        )
        items.append(
            {
                "source_id": sid,
                "domain": src.domain,
                "description": src.description,
                "status": st,
                "trust_score": score,
                "score_freshness": float(h.get("score_freshness", 100.0)),
                "score_completeness": float(h.get("score_completeness", 100.0)),
                "score_validity": float(h.get("score_validity", 100.0)),
                "score_source": float(h.get("score_source", 100.0)),
                "row_count": rows,
                "min_rows": min_r,
                "min_rows_passed": rows >= min_r,
                "required_fields": src.quality.required_fields,
                "quality_test_passed": score >= 85.0 and rows >= min_r,
                "adapter": src.parser,
                "source_used": used,
                "endpoint_url": url,
                "last_checked_utc": last_chk,
                "last_changed_utc": h.get("last_changed_utc"),
                "next_run_due_utc": next_dt_iso,
                "seconds_until_due": rem_sec,
                "is_due": is_due,
                "cadence_minutes": cadence,
                "sla_minutes": float(src.sla_minutes),
                "error_message": h.get("error_message", ""),
                "sha256": h.get("sha256", ""),
                "license_spdx": src.license_spdx,
                "history": (history_map or {}).get(sid, []),
            }
        )
    st_set = {i["status"] for i in items}
    overall = (
        "DEGRADED" if "ERROR" in st_set else ("ATTENTION" if "ATTENTION" in st_set else "HEALTHY")
    )
    avg = round(sum(i["trust_score"] for i in items) / len(items), 1) if items else 100.0
    kpis = {
        "total_sources": len(sources),
        "healthy_count": len([i for i in items if i["status"] in ("GOOD", "UNCHANGED")]),
        "attention_count": len([i for i in items if i["status"] == "ATTENTION"]),
        "error_count": len([i for i in items if i["status"] == "ERROR"]),
        "total_rows_collected": sum(i["row_count"] for i in items),
        "average_trust_score": avg,
    }
    return {"status": overall, "checked_at_utc": now.isoformat(), "kpis": kpis, "sources": items}


def format_prometheus_metrics(
    sources: dict[str, SourceConfig], health_map: dict[str, dict[str, Any]]
) -> str:
    lines = [
        "# HELP openlux_flow_status Statut d'execution (1=OK, 0.5=ATTENTION, 0=KO)",
        "# TYPE openlux_flow_status gauge",
        "# HELP openlux_flow_trust_score Trust Score qualite (0-100)",
        "# TYPE openlux_flow_trust_score gauge",
        "# HELP openlux_flow_rows_collected Nombre total de lignes",
        "# TYPE openlux_flow_rows_collected gauge",
        "# HELP openlux_flow_last_run_timestamp_seconds Timestamp Unix dernier run",
        "# TYPE openlux_flow_last_run_timestamp_seconds gauge",
    ]
    st_val = {"GOOD": 1.0, "UNCHANGED": 1.0, "ATTENTION": 0.5, "ERROR": 0.0, "NOT_TESTED": 0.0}
    for sid, src in sources.items():
        h = health_map.get(sid, {})
        lbl = f'source_id="{sid}",domain="{src.domain}"'
        lines.append(
            f"openlux_flow_status{{{lbl}}} {st_val.get(h.get('status', 'NOT_TESTED'), 0.0)}"
        )
        lines.append(f"openlux_flow_trust_score{{{lbl}}} {float(h.get('trust_score', 100.0)):.1f}")
        lines.append(f"openlux_flow_rows_collected{{{lbl}}} {int(h.get('row_count', 0))}")
        if chk := h.get("last_checked_utc"):
            try:
                ts = datetime.fromisoformat(chk).timestamp()
                lines.append(f"openlux_flow_last_run_timestamp_seconds{{{lbl}}} {ts}")
            except Exception:
                pass
    return "\n".join(lines) + "\n"


def send_alert_if_needed(
    source_id: str,
    current_status: str,
    recent_history: list[str],
    webhook_url: str | None = None,
    client: httpx.Client | None = None,
) -> bool:
    target = webhook_url or os.environ.get("OPENLUX_ALERT_WEBHOOK_URL")
    if not target:
        return False
    prev = recent_history[-1] if recent_history else "GOOD"
    if (current_status == "ERROR" and prev != "ERROR") or (
        current_status == "ATTENTION"
        and sum(1 for s in recent_history[-2:] if s == "ATTENTION") + 1 >= 3
    ):
        try:
            (client or httpx).post(
                target,
                json={
                    "source_id": source_id,
                    "status": current_status,
                    "reason": f"Statut {current_status} pour {source_id}",
                },
                timeout=5.0,
            )
            return True
        except Exception:
            pass
    return False
