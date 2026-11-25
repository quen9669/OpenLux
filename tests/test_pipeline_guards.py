"""Garde-fous du pipeline : alertes sur l'historique réel, export bloqué si dbt échoue (offline)."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from openlux import cli
from openlux.core.monitoring import send_alert_if_needed


@pytest.mark.parametrize(
    ("status", "history", "sent"),
    [
        ("ERROR", ["GOOD"], True),
        ("ERROR", ["GOOD", "ERROR"], False),  # déjà signalée : pas d'alerte en boucle
        ("ATTENTION", ["GOOD", "ATTENTION", "ATTENTION"], True),  # 3e ATTENTION de suite
        ("ATTENTION", ["ATTENTION", "GOOD", "ATTENTION"], False),
    ],
)
def test_alert_rules_use_real_history(status: str, history: list[str], sent: bool) -> None:
    calls: list[httpx.Request] = []
    client = httpx.Client(
        transport=httpx.MockTransport(lambda r: calls.append(r) or httpx.Response(200))
    )
    assert send_alert_if_needed("s", status, history, "https://hook.test/x", client) is sent
    assert len(calls) == int(sent)


def test_dbt_failure_blocks_gold_export(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "sources.toml").write_text(
        Path("config/sources.toml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    exported: list[bool] = []
    monkeypatch.setattr(cli, "_run_dbt_command", lambda cmd, *a: cmd != "test")
    monkeypatch.setattr(cli, "export_gold_parquets", lambda *a: exported.append(True))
    assert cli.run_pipeline(sources_filter=["__none__"]) == 1
    assert not exported
