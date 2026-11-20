"""Tests unitaires 100 % offline du moteur de collecte (fallback, SHA-256, MockTransport)."""

from __future__ import annotations

import httpx

from openlux.config import EndpointConfig, QualityConfig, SourceConfig
from openlux.core.collector import collect_source


def _build_dummy_source(
    primary_url: str = "https://mock.primary.lu/data.json",
    backup_url: str | None = "https://mock.backup.com/data.json",
    auth_var: str | None = None,
) -> SourceConfig:
    return SourceConfig(
        id="mock_source",
        domain="test",
        description="Source de test mock",
        adapter="http_json",
        cadence_minutes=15,
        sla_minutes=30,
        primary=EndpointConfig(url=primary_url, auth_env_var=auth_var),
        backup=EndpointConfig(url=backup_url) if backup_url else None,
        quality=QualityConfig(min_rows=1, required_fields=["id"]),
    )


def test_collector_primary_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"id": 1, "name": "Findel"}])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    source = _build_dummy_source()
    res = collect_source(source, client=client)

    assert res.status == "SUCCESS"
    assert res.source_used == "primary"
    assert res.row_count == 1
    assert len(res.sha256) == 64
    assert res.file_path is not None
    assert res.file_path.exists()


def test_collector_fallback_to_backup_when_primary_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "mock.primary.lu" in str(request.url):
            return httpx.Response(500, text="Internal Server Error")
        return httpx.Response(200, json=[{"id": 2, "name": "Backup Station"}])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    source = _build_dummy_source()
    res = collect_source(source, client=client)

    assert res.status == "ATTENTION"
    assert res.source_used == "backup"
    assert res.row_count == 1


def test_collector_unchanged_idempotence_sha256() -> None:
    payload = [{"id": 42, "status": "ok"}]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    source = _build_dummy_source()

    # 1er run -> SUCCESS
    res1 = collect_source(source, client=client)
    assert res1.status == "SUCCESS"

    # 2e run avec le même sha256 -> UNCHANGED
    res2 = collect_source(
        source,
        client=client,
        last_sha256=res1.sha256,
        last_changed_utc=res1.changed_at_utc,
    )
    assert res2.status == "UNCHANGED"
    assert res2.sha256 == res1.sha256
    assert res2.file_path is None  # Aucun nouveau fichier horodaté n'a été créé
    assert res2.changed_at_utc == res1.changed_at_utc


def test_collector_both_fail_returns_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    source = _build_dummy_source()
    res = collect_source(source, client=client)

    assert res.status == "ERROR"
    assert res.source_used == "none"
    assert res.row_count == 0


def test_collector_missing_auth_env_var_marks_not_tested_or_falls_back() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"id": 99}])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    # Source sans backup avec auth requise manquante
    src_no_backup = _build_dummy_source(backup_url=None, auth_var="NON_EXISTENT_KEY_12345")
    res_no_backup = collect_source(src_no_backup, client=client)
    assert res_no_backup.status == "NOT_TESTED"

    # Source avec backup qui doit basculer sans planter
    src_with_backup = _build_dummy_source(
        backup_url="https://mock.backup.com/data.json", auth_var="NON_EXISTENT_KEY_12345"
    )
    res_backup = collect_source(src_with_backup, client=client)
    assert res_backup.status == "ATTENTION"
    assert res_backup.source_used == "backup"
