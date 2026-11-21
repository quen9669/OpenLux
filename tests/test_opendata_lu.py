"""Tests pour la publication Open Data et la génération des métadonnées conformes."""

from pathlib import Path

from openlux.publish.opendata_lu import (
    _infer_type,
    compact_bronze_archives,
    generate_datapackage,
    generate_dcat_ap_lu,
    publish_to_data_public_lu,
)


def test_infer_type() -> None:
    assert _infer_type("VARCHAR") == "string"
    assert _infer_type("BIGINT") == "integer"
    assert _infer_type("DOUBLE") == "number"
    assert _infer_type("BOOLEAN") == "boolean"
    assert _infer_type("DATE") == "date"
    assert _infer_type("TIMESTAMP") == "datetime"


def test_generate_datapackage_metadata() -> None:
    gold_dir = Path("data/gold")
    dp = generate_datapackage(gold_dir)
    assert dp["name"] == "openlux-hub-gold"
    assert dp["license"] == "CC0-1.0"
    assert len(dp["resources"]) >= 22

    # Vérification présence des standards sectoriels NeTEx, SIRI, DATEX II
    transit_res = next(r for r in dp["resources"] if r["name"] == "gold_public_transit")
    assert any("NeTEx" in s for s in transit_res["standards_applied"])
    assert any("SIRI" in s for s in transit_res["standards_applied"])

    traffic_res = next(r for r in dp["resources"] if r["name"] == "gold_traffic_events")
    assert any("DATEX II" in s for s in traffic_res["standards_applied"])


def test_generate_dcat_ap_lu() -> None:
    gold_dir = Path("data/gold")
    dcat = generate_dcat_ap_lu(gold_dir)
    assert dcat["@type"] == "dcat:Dataset"
    assert len(dcat["distributions"]) >= 22
    for dist in dcat["distributions"]:
        assert dist["format"] == "parquet"
        assert dist["byteSize"] > 0


def test_publish_dry_run() -> None:
    res = publish_to_data_public_lu(dry_run=True)
    assert res["status"] == "SIMULATED_SUCCESS"
    assert res["resources_count"] >= 22
    assert Path(res["datapackage_path"]).exists()
    assert Path(res["dcat_path"]).exists()


def test_compact_bronze_dry_run(tmp_path: Path) -> None:
    # Création d'un faux snapshot dans un répertoire temporaire
    src_dir = tmp_path / "test_source"
    src_dir.mkdir()
    (src_dir / "snapshot_20260101_120000.gz").write_bytes(b"data")
    count = compact_bronze_archives(tmp_path, dry_run=True)
    assert count == 1
    assert (src_dir / "snapshot_20260101_120000.gz").exists()
