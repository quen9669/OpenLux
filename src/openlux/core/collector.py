"""Rôle : Moteur de collecte unifié (3 adaptateurs + custom, fallback, SHA-256, Bronze).
Entrées/Sorties : Reçoit une SourceConfig et écrit le flux compressé dans data/bronze/.
Hors-scope : N'exécute pas les transformations dbt ni le calcul du Trust Score.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

from openlux.config import EndpointConfig, SourceConfig
from openlux.core.parsers import PARSERS
from openlux.core.sanitizer import apply_factual_only, sanitize_text, sanitize_value


@dataclass
class CollectorResult:
    """Résultat immuable d'une opération de collecte atomique."""

    source_id: str
    status: str  # SUCCESS, UNCHANGED, ATTENTION, ERROR, NOT_TESTED
    source_used: str  # primary, backup, none
    sha256: str
    row_count: int
    raw_bytes: bytes
    file_path: Path | None
    checked_at_utc: str
    changed_at_utc: str
    error_message: str | None = None


def _fetch_endpoint(endpoint: EndpointConfig, client: httpx.Client, timeout: float = 15.0) -> bytes:
    """Effectue la requête HTTP vers un endpoint configuré."""
    # POURQUOI : Vérification de la présence des secrets sans exposer la valeur dans les logs.
    headers = dict(endpoint.headers)
    if endpoint.auth_env_var:
        token = os.environ.get(endpoint.auth_env_var)
        if not token:
            raise PermissionError(f"Variable d'authentification absente: {endpoint.auth_env_var}")
        headers["Authorization"] = f"Bearer {token}"
    resp = client.get(endpoint.url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def _process_json(raw: bytes, factual_only: bool) -> tuple[bytes, int]:
    """Parse, assainit (Zero-PII) et normalise un payload JSON."""
    parsed: Any = json.loads(raw.decode("utf-8"))
    cleaned = sanitize_value(parsed)
    if factual_only:
        cleaned = apply_factual_only(cleaned)
    normalized = json.dumps(cleaned, ensure_ascii=False, sort_keys=True).encode("utf-8")
    count = len(cleaned) if isinstance(cleaned, list) else (1 if cleaned else 0)
    return normalized, count


def _process_csv(raw: bytes) -> tuple[bytes, int]:
    """Nettoie cellule par cellule un CSV en conservant l'encodage UTF-8."""
    # POURQUOI : Assainissement Zero-PII cellule par cellule sans altérer la disposition tabulaire.
    reader = csv.reader(io.StringIO(raw.decode("utf-8", errors="replace")))
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    row_count = 0
    for idx, row in enumerate(reader):
        sanitized_row = [sanitize_text(cell) for cell in row]
        writer.writerow(sanitized_row)
        if idx > 0 and any(cell.strip() for cell in sanitized_row):
            row_count += 1
    return output.getvalue().encode("utf-8"), row_count


def _process_jsonld(raw: bytes, factual_only: bool) -> tuple[bytes, int]:
    """Extrait exclusivement les blocs JSON-LD Event d'une page HTML."""
    soup = BeautifulSoup(raw.decode("utf-8", errors="replace"), "html.parser")
    events: list[dict] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        if not tag.string:
            continue
        try:
            data = json.loads(tag.string)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") == "Event" or "event" in str(item.get("@type", "")).lower():
                    events.append(item)
        except Exception:
            continue
    cleaned = sanitize_value(events)
    if factual_only:
        cleaned = apply_factual_only(cleaned, strict_whitelist=True)
    normalized = json.dumps(cleaned, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return normalized, len(cleaned)


def _process_payload(source: SourceConfig, raw: bytes) -> tuple[bytes, int, str]:
    """Achemine les octets bruts vers l'adaptateur ou le parser adéquat."""
    if source.adapter == "http_json":
        b, count = _process_json(raw, source.factual_only)
        return b, count, "json"
    if source.adapter == "http_csv":
        b, count = _process_csv(raw)
        return b, count, "csv"
    if source.adapter == "http_jsonld":
        b, count = _process_jsonld(raw, source.factual_only)
        return b, count, "json"
    if source.adapter == "http_custom" and source.parser in PARSERS:
        records = PARSERS[source.parser](raw)
        cleaned = sanitize_value(records)
        if source.factual_only:
            cleaned = apply_factual_only(cleaned)
        b = json.dumps(cleaned, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return b, len(cleaned), "json"
    raise ValueError(f"Adaptateur ou parser non supporté: {source.adapter} / {source.parser}")


def _write_bronze(source_id: str, payload: bytes, ext: str, sha256_hex: str, now: datetime) -> Path:
    """Enregistre le payload immuable dans l'arborescence datée de data/bronze/."""
    # POURQUOI : Stockage immuable .gz et fichier 'latest' pour lectures DuckDB dbt.
    dir_path = Path("data/bronze") / source_id / now.strftime("%Y/%m/%d")
    dir_path.mkdir(parents=True, exist_ok=True)
    ts = now.strftime("%Y%m%dT%H%M%SZ")
    archive_file = dir_path / f"{source_id}_{ts}_{sha256_hex[:8]}.{ext}.gz"
    compressed = gzip.compress(payload)
    archive_file.write_bytes(compressed)
    (Path("data/bronze") / source_id / f"latest.{ext}.gz").write_bytes(compressed)
    return archive_file


def collect_source(
    source: SourceConfig,
    client: httpx.Client | None = None,
    last_sha256: str | None = None,
    last_changed_utc: str | None = None,
) -> CollectorResult:
    """Orchestre la collecte d'un flux : requête, fallback, assainissement et stockage Bronze."""
    now = datetime.now(UTC)
    now_iso = now.isoformat()
    http_client = client or httpx.Client()
    raw: bytes | None = None
    source_used = "primary"
    err_msg: str | None = None

    # POURQUOI : Si la clé API obligatoire manque en local, bascule immédiate sans crash.
    try:
        raw = _fetch_endpoint(source.primary, http_client)
    except Exception as exc:
        err_msg = str(exc)
        if source.backup:
            try:
                raw = _fetch_endpoint(source.backup, http_client)
                source_used = "backup"
                err_msg = None
            except Exception as backup_exc:
                err_msg = f"Primary: {err_msg} | Backup: {backup_exc}"
        elif isinstance(exc, PermissionError):
            return CollectorResult(
                source.id, "NOT_TESTED", "none", "", 0, b"", None, now_iso, now_iso, err_msg
            )

    if raw is None:
        return CollectorResult(
            source.id, "ERROR", "none", "", 0, b"", None, now_iso, now_iso, err_msg
        )

    processed_bytes, count, ext = _process_payload(source, raw)
    sha = hashlib.sha256(processed_bytes).hexdigest()

    # POURQUOI : Idempotence SHA-256 — payload inchangé n'écrit pas de nouveau fichier daté.
    if last_sha256 and sha == last_sha256:
        return CollectorResult(
            source.id,
            "UNCHANGED",
            source_used,
            sha,
            count,
            processed_bytes,
            None,
            now_iso,
            last_changed_utc or now_iso,
        )

    file_path = _write_bronze(source.id, processed_bytes, ext, sha, now)
    status = "ATTENTION" if source_used == "backup" else "SUCCESS"
    return CollectorResult(
        source.id, status, source_used, sha, count, processed_bytes, file_path, now_iso, now_iso
    )
