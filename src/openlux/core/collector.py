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

import httpx
from bs4 import BeautifulSoup

from openlux.config import EndpointConfig, SourceConfig
from openlux.core.parsers import PARSERS
from openlux.core.sanitizer import apply_factual_only, sanitize_text, sanitize_value


@dataclass
class CollectorResult:
    source_id: str
    status: str
    source_used: str
    sha256: str
    row_count: int
    raw_bytes: bytes
    file_path: Path | None
    checked_at_utc: str
    changed_at_utc: str
    error_message: str | None = None


def _fetch_endpoint(endpoint: EndpointConfig, client: httpx.Client, timeout: float = 15.0) -> bytes:
    headers = dict(endpoint.headers)
    if endpoint.auth_env_var:
        token = os.environ.get(endpoint.auth_env_var)
        if not token:
            raise PermissionError(f"Auth manquante: {endpoint.auth_env_var}")
        headers["Authorization"] = f"Bearer {token}"
    resp = client.get(endpoint.url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def _process_json(raw: bytes, factual_only: bool) -> tuple[bytes, int]:
    cleaned = sanitize_value(json.loads(raw.decode("utf-8")))
    if factual_only:
        cleaned = apply_factual_only(cleaned)
    normalized = json.dumps(cleaned, ensure_ascii=False, sort_keys=True).encode("utf-8")
    count = len(cleaned) if isinstance(cleaned, list) else (1 if cleaned else 0)
    return normalized, count


def _process_csv(raw: bytes) -> tuple[bytes, int]:
    reader = csv.reader(io.StringIO(raw.decode("utf-8", errors="replace")))
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    rows = [[sanitize_text(c) for c in r] for r in reader]
    writer.writerows(rows)
    count = sum(1 for idx, r in enumerate(rows) if idx > 0 and any(c.strip() for c in r))
    return out.getvalue().encode("utf-8"), count


def _process_jsonld(raw: bytes, factual_only: bool) -> tuple[bytes, int]:
    soup = BeautifulSoup(raw.decode("utf-8", errors="replace"), "html.parser")
    events: list[dict] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        if tag.string:
            try:
                data = json.loads(tag.string)
                events.extend(
                    item
                    for item in (data if isinstance(data, list) else [data])
                    if item.get("@type") == "Event" or "event" in str(item.get("@type", "")).lower()
                )
            except Exception:
                pass
    cleaned = sanitize_value(events)
    if factual_only:
        cleaned = apply_factual_only(cleaned, strict_whitelist=True)
    return json.dumps(cleaned, ensure_ascii=False, sort_keys=True).encode("utf-8"), len(cleaned)


def _process_payload(source: SourceConfig, raw: bytes) -> tuple[bytes, int, str]:
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
        return (
            json.dumps(cleaned, ensure_ascii=False, sort_keys=True).encode("utf-8"),
            len(cleaned),
            "json",
        )
    raise ValueError(f"Adaptateur non supporté: {source.adapter} / {source.parser}")


def _write_bronze(source_id: str, payload: bytes, ext: str, sha256_hex: str, now: datetime) -> Path:
    d = Path("data/bronze") / source_id / now.strftime("%Y/%m/%d")
    d.mkdir(parents=True, exist_ok=True)
    archive = d / f"{source_id}_{now.strftime('%Y%m%dT%H%M%SZ')}_{sha256_hex[:8]}.{ext}.gz"
    compressed = gzip.compress(payload)
    archive.write_bytes(compressed)
    (Path("data/bronze") / source_id / f"latest.{ext}.gz").write_bytes(compressed)
    return archive


def collect_source(
    source: SourceConfig,
    client: httpx.Client | None = None,
    last_sha256: str | None = None,
    last_changed_utc: str | None = None,
) -> CollectorResult:
    now = datetime.now(UTC)
    now_iso, http_client, raw, source_used, err_msg = (
        now.isoformat(),
        client or httpx.Client(),
        None,
        "primary",
        None,
    )
    try:
        raw = _fetch_endpoint(source.primary, http_client)
    except Exception as exc:
        err_msg = str(exc)
        if source.backup:
            try:
                raw, source_used, err_msg = (
                    _fetch_endpoint(source.backup, http_client),
                    "backup",
                    None,
                )
            except Exception as b_exc:
                err_msg = f"Primary: {err_msg} | Backup: {b_exc}"
        elif isinstance(exc, PermissionError):
            return CollectorResult(
                source.id, "NOT_TESTED", "none", "", 0, b"", None, now_iso, now_iso, err_msg
            )

    if raw is None:
        return CollectorResult(
            source.id, "ERROR", "none", "", 0, b"", None, now_iso, now_iso, err_msg
        )

    processed, count, ext = _process_payload(source, raw)
    sha = hashlib.sha256(processed).hexdigest()
    if last_sha256 and sha == last_sha256:
        return CollectorResult(
            source.id,
            "UNCHANGED",
            source_used,
            sha,
            count,
            processed,
            None,
            now_iso,
            last_changed_utc or now_iso,
        )

    fpath = _write_bronze(source.id, processed, ext, sha, now)
    return CollectorResult(
        source.id,
        "ATTENTION" if source_used == "backup" else "SUCCESS",
        source_used,
        sha,
        count,
        processed,
        fpath,
        now_iso,
        now_iso,
    )
