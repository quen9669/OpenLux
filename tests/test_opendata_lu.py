"""Tests du catalogue mesuré et des métadonnées Data Package / DCAT-AP-LU (offline)."""

from __future__ import annotations

from pathlib import Path

import duckdb

from openlux.publish.opendata_lu import (
    _infer_type,
    build_catalog,
    generate_datapackage,
    generate_dcat_ap_lu,
    publish_to_data_public_lu,
    write_site_catalog,
)


def _gold(tmp_path: Path) -> Path:
    gold = tmp_path / "gold"
    gold.mkdir()
    with duckdb.connect() as con:
        con.execute(
            "COPY (SELECT 'fuel_prices_lu' AS source_id, '2026-10' AS reference_month, "
            "'Diesel_B7' AS energy_type, 2.066 AS price_eur, "
            "TIMESTAMP '2026-11-24 10:00' AS collected_at_utc) "
            f"TO '{(gold / 'gold_fuel_prices.parquet').as_posix()}' (FORMAT PARQUET)"
        )
    return gold


def test_infer_type() -> None:
    assert _infer_type("VARCHAR") == "string"
    assert _infer_type("BIGINT") == "integer"
    assert _infer_type("DOUBLE") == "number"
    assert _infer_type("BOOLEAN") == "boolean"
    assert _infer_type("DATE") == "date"
    assert _infer_type("TIMESTAMP") == "datetime"


def test_catalog_is_measured_not_declared(tmp_path: Path) -> None:
    (d,) = build_catalog(_gold(tmp_path))
    assert d["dataset"] == "gold_fuel_prices" and d["row_count"] == 1
    assert d["coverage"] == {"from": "2026-10", "to": "2026-10"}
    assert d["last_collected_utc"].startswith("2026-11-24 10:00")
    (src,) = d["sources"]
    assert src["source_id"] == "fuel_prices_lu" and src["license_spdx"] == "CC0-1.0"
    assert src["url"].startswith("https://data.public.lu/")


def test_metadata_files(tmp_path: Path) -> None:
    gold = _gold(tmp_path)
    dp = generate_datapackage(gold)
    assert dp["resources"][0]["licenses"] == ["CC0-1.0"]
    assert "email" not in str(dp["resources"])  # aucun contact inventé
    dcat = generate_dcat_ap_lu(gold)
    assert dcat["distributions"][0]["byteSize"] > 0
    res = publish_to_data_public_lu(dry_run=True, gold_dir=gold)
    assert res["status"] == "METADATA_WRITTEN" and Path(res["datapackage_path"]).exists()


def test_site_catalog_snapshot(tmp_path: Path) -> None:
    out = write_site_catalog(_gold(tmp_path), tmp_path / "site")
    assert out.exists() and "gold_fuel_prices" in out.read_text(encoding="utf-8")


def test_cli_publish_options() -> None:
    from openlux.cli import _build_parser

    p = _build_parser()
    assert p.parse_args(["publish"]).dry_run is True
    assert p.parse_args(["publish", "--live"]).dry_run is False
