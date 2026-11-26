"""Rôle : Contrôles qualité transverses (validité dbt par source, chute de volume, champs requis).
Entrées/Sorties : Lit dbt_project/target/*.json, les tables Gold DuckDB et les payloads Bronze.
Hors-scope : Ne calcule pas le Trust Score (core/quality.py) et n'écrit rien.
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median

import duckdb

from openlux.config import QualityConfig
from openlux.core.collector import CollectorResult

TARGET = Path("dbt_project/target")


def _gold_sources(
    con: duckdb.DuckDBPyConnection, model: str, cache: dict[str, list[str]]
) -> list[str]:
    if model not in cache:
        try:
            # POURQUOI : `model` vient du manifest dbt (gold_*), jamais d'une entrée utilisateur
            sql = f'SELECT DISTINCT source_id FROM "{model}"'
            cache[model] = [r[0] for r in con.execute(sql).fetchall()]
        except duckdb.Error:
            cache[model] = []  # table sans source_id (ex. contexte quotidien dérivé)
    return cache[model]


def dbt_validity_by_source(
    con: duckdb.DuckDBPyConnection, target: Path = TARGET
) -> dict[str, tuple[float, list[str]]]:
    """% de nœuds dbt réussis touchant chaque source (via ses tables gold_*), et ceux en échec."""
    try:
        results = json.loads((target / "run_results.json").read_text(encoding="utf-8"))["results"]
        nodes = json.loads((target / "manifest.json").read_text(encoding="utf-8"))["nodes"]
    except (OSError, ValueError, KeyError):
        return {}
    tally: dict[str, tuple[int, int, list[str]]] = {}
    cache: dict[str, list[str]] = {}
    for r in results:
        uid, node = r["unique_id"], nodes.get(r["unique_id"], {})
        deps = [uid] if uid.startswith("model.") else node.get("depends_on", {}).get("nodes", [])
        models = {d.rsplit(".", 1)[-1] for d in deps if d.startswith("model.")}
        ok = r["status"] in ("success", "pass")
        for sid in {
            s for m in models if m.startswith("gold_") for s in _gold_sources(con, m, cache)
        }:
            n_ok, n, bad = tally.get(sid, (0, 0, []))
            tally[sid] = (n_ok + ok, n + 1, bad if ok else [*bad, node.get("name", uid)])
    return {sid: (round(100.0 * k / n, 1), bad) for sid, (k, n, bad) in tally.items()}


def volume_drop(rows: int, past_rows: list[int], ratio: float = 0.5) -> float | None:
    """Médiane des 5 derniers runs non vides si `rows` en vaut moins de `ratio`, sinon None."""
    hist = [r for r in past_rows if r > 0][-5:]
    # POURQUOI : sous 3 runs pas de référence ; la médiane absorbe un pic isolé et suit un
    # changement de périmètre voulu (ex. past_days 92 -> 7) en 3 runs au lieu de 9 pour une moyenne
    if len(hist) < 3:
        return None
    ref = median(hist)
    return ref if rows < ratio * ref else None


def missing_required(fields: list[str], payload: bytes) -> list[str]:
    """Champs requis absents ou vides dans au moins un enregistrement du payload Bronze."""
    if not fields or not payload:
        return []
    recs = json.loads(payload)
    return [f for f in fields if any(r.get(f) in (None, "") for r in recs if isinstance(r, dict))]


def run_checks(
    res: CollectorResult,
    quality: QualityConfig,
    past_rows: list[int],
    validity: dict[str, tuple[float, list[str]]],
) -> tuple[float, bool, list[str]]:
    """Contrôles d'une collecte -> (note de validité, champs requis OK, constats lisibles).
    Une chute de volume fait passer `res.status` de SUCCESS à ATTENTION."""
    v_score, v_bad = validity.get(res.source_id, (100.0, []))
    notes = [res.error_message] if res.error_message else []
    # POURQUOI : sans min_rows, le flux est une liste d'événements (alertes, bouchons) dont le
    # volume varie légitimement : pas de contrôle de chute
    stable = quality.min_rows > 0 and res.status == "SUCCESS"
    if stable and (ref := volume_drop(res.row_count, past_rows)):
        res.status = "ATTENTION"
        notes.append(f"Volume en chute : {res.row_count} lignes (médiane {ref:.0f})")
    if miss := missing_required(quality.required_fields, res.raw_bytes):
        notes.append(f"Champs requis vides : {', '.join(miss)}")
    if v_bad:
        notes.append(f"Tests dbt en échec : {', '.join(v_bad)}")
    return v_score, not miss, notes
