"""Rôle : Génération de STATUS.md et envoi d'alertes webhook anti-spam.
Entrées/Sorties : Lit les métriques de santé des sources et produit STATUS.md.
Hors-scope : N'exécute pas les collecteurs ni les calculs de scores qualité.
"""

from __future__ import annotations

import os
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
        ico, lic = ICONS.get(st, f"`{st}`"), src.license_spdx
        rows.append(
            f"| *{src.domain}* | `{sid}` | {ico} | {sc} | {act} | {r} | {c} | {m} | `{lic}` |"
        )
    legend = (
        "\n\n*Légende :* 🟢 `GOOD` (85-100) | 🟡 `ATTENTION` (60-84) | "
        "🔴 `ERROR` (<60) | ⚪ `NOT_TESTED`\n"
    )
    content = hdr + "\n".join(rows) + legend
    Path(output_path).write_text(content, encoding="utf-8")
    return content


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
    alert = (current_status == "ERROR" and prev != "ERROR") or (
        current_status == "ATTENTION"
        and sum(1 for s in recent_history[-2:] if s == "ATTENTION") + 1 >= 3
    )
    if alert:
        try:
            msg = f"Statut {current_status} pour {source_id}"
            (client or httpx.Client()).post(
                target,
                json={"source_id": source_id, "status": current_status, "reason": msg},
                timeout=5.0,
            )
            return True
        except Exception:
            pass
    return False
