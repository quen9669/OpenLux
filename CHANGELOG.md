# Changelog

Toutes les modifications notables de ce projet sont consignées dans ce fichier.
Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère à [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

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
