# Changelog

Toutes les modifications notables de ce projet sont consignées dans ce fichier.
Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère à [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

## [0.2.0] - 2026-11-21

### Added
- **Phase 1 : Moteur Minimal & Vertical Slice (3 Sources Pilotes)**
  - Module `config.py` avec validation déclarative Pydantic de `config/sources.toml` via `tomllib`.
  - Moteur Zero-PII récursif et filtre Factual-Only dans `core/sanitizer.py`.
  - Registre de parsers pures dans `core/parsers.py` avec `cita_datex2` (XML DATEX II CITA autoroutes $\le 30$ lignes).
  - Collecteur générique multi-adaptateurs (`http_json`, `http_csv`, `http_jsonld`, `http_custom`) avec fallback automatique, idempotence SHA-256 (`UNCHANGED`) et stockage Bronze immuable `.gz` dans `core/collector.py`.
  - Calculateur de Trust Score (0 à 100) et persistance MLOps dans la table DuckDB `obs_runs` dans `core/quality.py`.
  - Surveillance zéro-infra et génération dynamique de `STATUS.md` avec webhook anti-spam dans `core/monitoring.py`.
  - Exportation atomique `.tmp` $\rightarrow$ `os.replace()` des Data Marts Gold en Parquet (ZSTD) dans `core/gold.py`.
  - Interface CLI unifiée dans `cli.py` (`openlux run`, `run --due`, `run --sources`, `rebuild`, `status`).
  - Pipeline de transformation SQL dbt complet sur les 3 sources pilotes (`meteo_lux_obs`, `traffic_cita_datex2`, `holidays_lu`) :
    - 3 modèles staging (`stg_meteo_lux_obs`, `stg_traffic_cita`, `stg_holidays_lu`).
    - 3 modèles silver (`silver_weather_observations`, `silver_traffic_events`, `silver_holidays`).
    - 3 modèles gold (`gold_weather_observations`, `gold_traffic_events`, `gold_holidays`).
    - Test SQL bloquant RGPD `assert_no_pii_in_gold.sql`.
  - Échantillons réels anonymisés dans `tests/fixtures/` (`meteo_lux_sample.json`, `cita_datex2_sample.xml`, `holidays_lu_sample.csv`).
  - Suite de 18 tests unitaires et d'intégration 100 % offline (`test_sanitizer.py`, `test_parsers.py`, `test_collector_fallback.py`, `test_trust_score.py`, `test_pipeline_slice.py`).


## [0.1.0] - 2026-11-20

### Added
- **Phase 0 : Initialisation, Gouvernance & Socle Documentaire**
  - Configuration `pyproject.toml` avec verrouillage strict des 7 dépendances runtime et de `uv`.
  - Intégration des règles opérationnelles `AGENTS.md` et du blueprint d'ingénierie `OPENLUX_BLUEPRINT.md`.
  - 4 ADR fondateurs (`ADR-001`, `ADR-002`, `ADR-003`, `ADR-004`) et `docs/adr/000-template.md`.
  - `docs/ARCHITECTURE.md` (v1.0), `docs/GOVERNANCE_GDPR.md`, `docs/DECISIONS_LOG.md` et `docs/DATA_CATALOG.md`.
  - Référentiel officiel des 100 communes du Luxembourg dans `dbt_project/seeds/ref_communes_lu.csv`.
  - Configuration dbt avec DuckDB (`dbt_project.yml`, `profiles.yml`).
  - Pipeline GitHub Actions CI (`.github/workflows/ci.yml`).
