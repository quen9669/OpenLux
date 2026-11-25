"""Rôle : Moteur de collecte unifié (primaire -> backup, parser dédié, SHA-256, Bronze).
Entrées/Sorties : Reçoit une SourceConfig et écrit les enregistrements nettoyés dans data/bronze/.
Hors-scope : N'exécute pas dbt ; n'écrit JAMAIS de données de substitution si une source échoue.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from openlux.config import EndpointConfig, SourceConfig
from openlux.core.parsers import TRAFFIC_PARSERS
from openlux.core.parsers_city import CITY_PARSERS
from openlux.core.parsers_civic import CIVIC_PARSERS
from openlux.core.parsers_culture import CULTURE_PARSERS
from openlux.core.parsers_env import ENV_PARSERS
from openlux.core.parsers_files import FILE_PARSERS
from openlux.core.parsers_transit import TRANSIT_PARSERS
from openlux.core.sanitizer import apply_factual_only, sanitize_value

PARSERS = (
    TRAFFIC_PARSERS
    | TRANSIT_PARSERS
    | ENV_PARSERS
    | CITY_PARSERS
    | CIVIC_PARSERS
    | CULTURE_PARSERS
    | FILE_PARSERS
)
BRONZE = Path("data/bronze")


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


def _expand_url(url: str, now: datetime) -> str:
    """Jetons de date dans les URLs (fenêtres glissantes d'API) : {today} {year} {next_year}..."""
    tokens = {
        "{today}": now.date().isoformat(),
        "{year}": str(now.year),
        "{next_year}": str(now.year + 1),
        "{last_year}": str(now.year - 1),
        "{days_ago_90}": (now - timedelta(days=90)).date().isoformat(),
        "{now_ms}": str(int(now.timestamp() * 1000)),
    }
    for k, v in tokens.items():
        url = url.replace(k, v)
    return url


def _token(var: str) -> str | None:
    token = os.environ.get(var)
    if not token and Path(".env").exists():
        for ln in Path(".env").read_text(encoding="utf-8").splitlines():
            if ln.strip().startswith(f"{var}="):
                token = ln.split("=", 1)[1].strip().strip("\"'")
    return token


def _fetch_endpoint(endpoint: EndpointConfig, client: httpx.Client, timeout: float = 90.0) -> bytes:
    headers = {"User-Agent": "OpenLuxHub/1.0 (+https://github.com/quen9669/OpenLux)"}
    headers |= endpoint.headers
    url = _expand_url(endpoint.url, datetime.now(UTC))
    if endpoint.auth_env_var:
        if not (token := _token(endpoint.auth_env_var)):
            raise PermissionError(f"Auth manquante: {endpoint.auth_env_var}")
        url = url.replace("{key}", token)
    for attempt in (1, 2):
        try:
            resp = client.get(url, headers=headers, timeout=timeout, follow_redirects=True)
            resp.raise_for_status()
            return resp.content
        except (httpx.TransportError, httpx.HTTPStatusError):
            # POURQUOI : CDN en cours de rafraîchissement / serveurs Overpass saturés => 2e essai
            if attempt == 2:
                raise
            time.sleep(3)
    raise RuntimeError("inatteignable")


def parse_payload(source: SourceConfig, raw: bytes, parser: str | None = None) -> tuple[bytes, int]:
    """Applique le parser déclaré, puis la sanitisation Zero-PII et le filtre Factual-Only."""
    name = parser or source.parser
    if name not in PARSERS:
        raise ValueError(f"Parser inconnu: {name}")
    records = sanitize_value(PARSERS[name](raw))
    if source.factual_only:
        records = apply_factual_only(records)
    return json.dumps(records, ensure_ascii=False, sort_keys=True).encode("utf-8"), len(records)


def _write_bronze(source_id: str, payload: bytes, sha256_hex: str, now: datetime) -> Path:
    d = BRONZE / source_id / now.strftime("%Y/%m/%d")
    d.mkdir(parents=True, exist_ok=True)
    archive = d / f"{source_id}_{now.strftime('%Y%m%dT%H%M%SZ')}_{sha256_hex[:8]}.json.gz"
    archive.write_bytes(gzip.compress(payload))
    return archive


def collect_source(
    source: SourceConfig,
    client: httpx.Client | None = None,
    last_sha256: str | None = None,
    last_changed_utc: str | None = None,
) -> CollectorResult:
    now = datetime.now(UTC)
    # POURQUOI : sans client fourni, httpx.get() ferme sa connexion (un Client créé ici fuyait)
    now_iso, http, errors = now.isoformat(), client or httpx, []
    for ep, label in [(source.primary, "primary"), (source.backup, "backup")]:
        if not ep:
            continue
        try:
            payload, count = parse_payload(source, _fetch_endpoint(ep, http), ep.parser)
            break
        except PermissionError as exc:
            errors.append(f"{label}: {exc}")
            if label == "primary" and not source.backup:
                return CollectorResult(
                    source.id, "NOT_TESTED", "none", "", 0, b"", None, now_iso, now_iso, str(exc)
                )
        except Exception as exc:  # noqa: BLE001 — toute erreur bascule sur le backup
            errors.append(f"{label}: {type(exc).__name__}: {exc}"[:300])
    else:
        msg = " | ".join(errors) or "aucun endpoint"
        return CollectorResult(source.id, "ERROR", "none", "", 0, b"", None, now_iso, now_iso, msg)

    sha = hashlib.sha256(payload).hexdigest()
    if last_sha256 and sha == last_sha256:
        changed = last_changed_utc or now_iso
        return CollectorResult(
            source.id, "UNCHANGED", label, sha, count, payload, None, now_iso, changed
        )
    fpath = _write_bronze(source.id, payload, sha, now)
    # POURQUOI : une liste vide peut être légitime (aucun bouchon) ; seul min_rows décide
    st = "ATTENTION" if label == "backup" or count < source.quality.min_rows else "SUCCESS"
    return CollectorResult(source.id, st, label, sha, count, payload, fpath, now_iso, now_iso)
