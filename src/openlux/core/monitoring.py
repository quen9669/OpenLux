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


def _get_status_icon(status: str) -> str:
    """Renvoie la pastille de couleur correspondant à l'état de santé."""
    icons = {
        "GOOD": "🟢 `GOOD`",
        "ATTENTION": "🟡 `ATTENTION`",
        "ERROR": "🔴 `ERROR`",
        "NOT_TESTED": "⚪ `NOT_TESTED`",
    }
    return icons.get(status, f"`{status}`")


def generate_status_markdown(
    sources: dict[str, SourceConfig],
    health_map: dict[str, dict[str, Any]],
    output_path: Path | str = "STATUS.md",
) -> str:
    """Génère le fichier STATUS.md récapitulant la santé en temps réel des flux."""
    lines = [
        "# État de Santé des Sources OpenLux Hub",
        "",
        "> Ce fichier est mis à jour à chaque exécution du pipeline (`openlux run`).",
        "",
        "| Domaine | Source ID | État | Trust Score | Source Active | Lignes | "
        "Dernier contrôle (UTC) | Dernière mutation (UTC) | Licence |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- |",
    ]

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
        lines.append(
            f"| *{src.domain}* | `{sid}` | {_get_status_icon(st)} | {sc} | {act} | {r} | "
            f"{c} | {m} | `{src.license_spdx}` |"
        )

    lines.extend(
        [
            "",
            "*Légende des états :*",
            "- 🟢 `GOOD` (85-100) : Nominal.",
            "- 🟡 `ATTENTION` (60-84) : Alerte mineure, source de secours active ou retard SLA.",
            "- 🔴 `ERROR` (<60) : Erreur critique, pipeline bloqué ou schéma invalide.",
            "- ⚪ `NOT_TESTED` : En intégration ou clé API absente en local.",
            "",
        ]
    )

    content = "\n".join(lines)
    Path(output_path).write_text(content, encoding="utf-8")
    return content


def send_alert_if_needed(
    source_id: str,
    current_status: str,
    recent_history: list[str],
    webhook_url: str | None = None,
    client: httpx.Client | None = None,
) -> bool:
    """Envoie une notification webhook anti-spam (transition ERROR ou 3x ATTENTION)."""
    # POURQUOI : Anti-spam strict : alerte uniquement sur rupture ou dégradation prolongée.
    target_url = webhook_url or os.environ.get("OPENLUX_ALERT_WEBHOOK_URL")
    if not target_url:
        return False

    should_alert = False
    reason = ""
    prev_status = recent_history[-1] if recent_history else "GOOD"

    if current_status == "ERROR" and prev_status != "ERROR":
        should_alert = True
        reason = f"Alerte critique : la source '{source_id}' est passée en ERROR."
    elif current_status == "ATTENTION":
        consecutive_att = sum(1 for s in recent_history[-2:] if s == "ATTENTION") + 1
        if consecutive_att >= 3:
            should_alert = True
            reason = f"Alerte dégradation : la source '{source_id}' en ATTENTION depuis 3 cycles."

    if should_alert:
        payload = {"source_id": source_id, "status": current_status, "reason": reason}
        http_client = client or httpx.Client()
        try:
            http_client.post(target_url, json=payload, timeout=5.0)
            return True
        except Exception:
            return False
    return False
