"""Tests offline du moteur de collecte (fallback, SHA-256, auth optionnelle, jetons d'URL)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from openlux.config import EndpointConfig, QualityConfig, SourceConfig
from openlux.core import collector
from openlux.core.collector import _expand_url, collect_source

PAYLOAD = {"unix_seconds": [1795500000, 1795500900], "price": [101.5, 99.0]}


@pytest.fixture(autouse=True)
def _isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(collector, "BRONZE", tmp_path / "bronze")
    monkeypatch.setattr(collector.time, "sleep", lambda _s: None)


def _source(backup: str | None = "https://mock.backup/x", auth: str | None = None) -> SourceConfig:
    return SourceConfig(
        id="mock_source",
        domain="test",
        description="Source de test",
        parser="energy_charts_price",
        cadence_minutes=15,
        sla_minutes=30,
        primary=EndpointConfig(url="https://mock.primary/x", auth_env_var=auth),
        backup=EndpointConfig(url=backup) if backup else None,
        quality=QualityConfig(min_rows=1),
    )


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_primary_success_writes_bronze() -> None:
    res = collect_source(_source(), client=_client(lambda r: httpx.Response(200, json=PAYLOAD)))
    assert (res.status, res.source_used, res.row_count) == ("SUCCESS", "primary", 2)
    assert res.file_path is not None and res.file_path.exists()
    assert len(res.sha256) == 64


def test_fallback_to_backup_is_attention() -> None:
    def handler(r: httpx.Request) -> httpx.Response:
        return httpx.Response(500) if "primary" in str(r.url) else httpx.Response(200, json=PAYLOAD)

    res = collect_source(_source(), client=_client(handler))
    assert (res.status, res.source_used) == ("ATTENTION", "backup")


def test_backup_can_use_its_own_parser() -> None:
    src = _source()
    src.backup.parser = "meteolux_hvd"
    hvd = {"data": [{"id": "st", "value": 3.1}], "timestamp": "2026-11-24T20:00:00Z"}

    def handler(r: httpx.Request) -> httpx.Response:
        return httpx.Response(500) if "primary" in str(r.url) else httpx.Response(200, json=hvd)

    res = collect_source(src, client=_client(handler))
    assert res.source_used == "backup"
    assert json.loads(res.raw_bytes)[0]["temperature_c"] == 3.1


def test_unchanged_payload_is_idempotent() -> None:
    cl = _client(lambda r: httpx.Response(200, json=PAYLOAD))
    first = collect_source(_source(), client=cl)
    second = collect_source(
        _source(), client=cl, last_sha256=first.sha256, last_changed_utc=first.changed_at_utc
    )
    assert second.status == "UNCHANGED" and second.file_path is None
    assert second.changed_at_utc == first.changed_at_utc


def test_both_endpoints_failing_is_error_without_any_data() -> None:
    res = collect_source(_source(), client=_client(lambda r: httpx.Response(503)))
    assert (res.status, res.row_count, res.raw_bytes) == ("ERROR", 0, b"")
    assert "primary" in res.error_message and "backup" in res.error_message


def test_transient_error_is_retried_once() -> None:
    calls = {"n": 0}

    def handler(r: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(404) if calls["n"] == 1 else httpx.Response(200, json=PAYLOAD)

    res = collect_source(_source(backup=None), client=_client(handler))
    assert res.status == "SUCCESS" and calls["n"] == 2


def test_missing_api_key_never_crashes() -> None:
    cl = _client(lambda r: httpx.Response(200, json=PAYLOAD))
    assert collect_source(_source(None, "NO_SUCH_KEY_42"), client=cl).status == "NOT_TESTED"
    res = collect_source(_source(auth="NO_SUCH_KEY_42"), client=cl)
    assert (res.status, res.source_used) == ("ATTENTION", "backup")


def test_url_date_tokens() -> None:
    now = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
    url = _expand_url("x?from={last_year}-01-01&to={today}&y={next_year}&t={now_ms}", now)
    assert url == "x?from=2025-01-01&to=2026-11-24&y=2027&t=1795521600000"
