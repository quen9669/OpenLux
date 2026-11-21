# Changelog

Toutes les modifications notables de ce projet sont consignées dans ce fichier.
Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère à [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

## [0.5.0] - 2026-11-21

### Added
- **Phase 3 : Passage à l'Échelle — Vague 3B (Mobilité & Frontières)**
  - Intégration déclarative 100 % config-driven de 11 nouvelles sources atomiques dans `config/sources.toml` :
    - `traffic_fr_bisonfute` (`crossborder_traffic`) : Trafic et bouchons sur l'A31 (France vers Luxembourg) via DIR Est / Bison Futé.
    - `traffic_de_autobahn` (`crossborder_traffic`) : Trafic et ralentissements sur l'A64 (Allemagne vers Luxembourg) via Autobahn GmbH.
    - `traffic_be_trafiroutes` (`crossborder_traffic`) : Trafic et encombrements sur l'E411 (Belgique vers Luxembourg) via Trafiroutes.
    - `rail_crossborder` (`crossborder_traffic`) : Suivi des trains transfrontaliers TER Fluo, CFL L50 et SNCB.
    - `transit_mobiliteit` (`public_transit`) : État du réseau national de transport public (Mobiliteit.lu / CFL / Tram / RGTR).
    - `transit_avl_rt` (`public_transit`) : Temps réel et retards des autobus municipaux de la Ville de Luxembourg (AVL).
    - `veloh_stations` (`mobility_parkings`) : Disponibilité en direct des vélos et bornes Vel'oH de la capitale et périphérie.
    - `parkings_vdl` (`mobility_parkings`) : Places libres en temps réel dans les parkings couverts et parcs relais P+R VDL.
    - `chargy_stations` (`mobility_parkings`) : Disponibilité et état des bornes de recharge pour véhicules électriques Chargy.
    - `aviation_opensky_lu` (`aviation_noise`) : Suivi des vols en approche et décollage de l'aéroport Findel (LUX) via OpenSky.
    - `noise_zones_lu` (`aviation_noise`) : Zones de bruit stratégiques et courbes d'exposition sonore aéroportuaire Lden.
  - Modèles de transformation dbt complets (staging, silver, gold) unifiant les flux par domaine :
    - 11 modèles Staging (`stg_traffic_fr_bisonfute`, `stg_traffic_de_autobahn`, `stg_traffic_be_trafiroutes`, `stg_rail_crossborder`, `stg_transit_mobiliteit`, `stg_transit_avl_rt`, `stg_veloh_stations`, `stg_parkings_vdl`, `stg_chargy_stations`, `stg_aviation_opensky_lu`, `stg_noise_zones_lu`).
    - 4 modèles Silver unifiant les flux avec standardisation spatiotemporelle et calculs d'occupation (`silver_crossborder_traffic`, `silver_public_transit`, `silver_mobility_parkings`, `silver_aviation_noise`).
    - 4 Data Marts Gold Parquet ZSTD (`gold_crossborder_traffic`, `gold_public_transit`, `gold_mobility_parkings`, `gold_aviation_noise`).
  - Extension du test d'intégrité RGPD `assert_no_pii_in_gold.sql` sur les colonnes textuelles des 4 nouveaux Data Marts.
  - 11 nouveaux jeux d'échantillons offline anonymisés dans `tests/fixtures/` pour des tests 100 % déterministes.
  - Mise à jour de `tests/test_pipeline_slice.py` validant la collecte et la transformation des 21 sources et 14 tables Gold.
  - Synchronisation de `STATUS.md`, `docs/ARCHITECTURE.md` (v1.3), `docs/DATA_CATALOG.md` et `docs/DECISIONS_LOG.md`.

## [0.4.0] - 2026-11-21

### Added
- **Phase 3 : Passage à l'Échelle — Vague 3A (Environnement & Énergie)**
  - Intégration déclarative 100 % config-driven de 7 nouvelles sources atomiques dans `config/sources.toml` :
    - `air_quality_lu` (`air_quality`) : Qualité de l'air en temps réel (NO2, O3, PM10, PM2.5, AQI) de l'Administration de l'Environnement.
    - `water_levels_lu` (`water_levels`) : Niveaux d'eau, débits et alertes crues de l'Administration de la Gestion de l'Eau.
    - `fuel_prices_lu` (`economy_fuel`) : Prix maxima officiels des carburants routiers du Ministère de l'Économie.
    - `statec_inflation` (`economy_fuel`) : Indices IPCN et inflation mensuelle STATEC.
    - `electricity_spot_delu` (`energy_climate`) : Prix spot Day-Ahead électricité zone conjointe DE-LU.
    - `radioactivity_lu` (`energy_climate`) : Surveillance radiologique et taux de dose gamma ambiant de la Radioprotection.
    - `bathing_water_lu` (`energy_climate`) : Analyses bactériologiques et qualité sanitaire des eaux de baignade officielles.
  - Modèles de transformation dbt complets (staging, silver, gold) pour chaque source :
    - 7 modèles Staging (`stg_air_quality`, `stg_water_levels`, `stg_fuel_prices`, `stg_statec_inflation`, `stg_electricity_spot`, `stg_radioactivity`, `stg_bathing_water`).
    - 7 modèles Silver normalisant les horodatages UTC et projetant les communes sur le référentiel officiel `ref_communes_lu`.
    - 7 Data Marts Gold Parquet ZSTD (`gold_air_quality`, `gold_water_levels`, `gold_fuel_prices`, `gold_statec_inflation`, `gold_electricity_spot`, `gold_radioactivity`, `gold_bathing_water`).
  - Extension du test d'intégrité RGPD `assert_no_pii_in_gold.sql` pour couvrir les colonnes texte des nouvelles tables Gold.
  - 7 nouveaux jeux de fixtures offline anonymisés dans `tests/fixtures/` pour des tests 100 % déterministes.
  - Mise à jour de la suite d'intégration offline `tests/test_pipeline_slice.py` validant la collecte, le stockage Bronze, les transformations dbt et l'export Parquet de l'ensemble des 10 sources actives.
  - Synchronisation de `STATUS.md`, `docs/ARCHITECTURE.md` (v1.2), `docs/DATA_CATALOG.md` et `docs/DECISIONS_LOG.md`.

## [0.3.0] - 2026-11-21

### Added
- **Phase 2 : Exposition Universelle : FastAPI (Swagger) & FastMCP**
  - Routeur REST sécurisé dans `src/openlux/api/main.py` :
    - Whitelist stricte validant `{dataset}` contre les fichiers Parquet Gold existants et rejetant systématiquement toute injection SQL ou path traversal (HTTP 404).
    - Requêtes paramétrées `?` avec DuckDB in-memory (`:memory:`) pour une isolation sans verrou de lecture/écriture.
    - Filtrage géospatial par distance sphérique WGS84 (`ST_Distance_Spheroid`) via l'extension DuckDB `spatial`.
    - Enveloppe standard `_meta` conforme au contrat Section 5.3 (traçabilité MLOps, SLA, `is_stale`, licence SPDX, `known_limitations`).
    - Téléchargement direct Parquet ZSTD (`GET /v1/exports/{dataset}.parquet`).
    - Streaming CSV et GeoJSON `FeatureCollection` à la volée depuis DuckDB (`GET /v1/exports/{dataset}.csv`, `.geojson`) sans duplication de fichier sur disque.
    - Endpoints de statut global (`GET /v1/status`) et catalogue dynamique (`GET /v1/datasets`).
    - Documentation interactive OpenAPI 3.1 automatique (`GET /docs` et `GET /redoc`).
  - Serveur FastMCP pour agents IA dans `src/openlux/mcp/server.py` :
    - Outil `get_platform_health(domain)` : observabilité et Trust Scores par flux/domaine.
    - Outil `get_luxembourg_day_context(date, commune)` : consolidation journalière météo, jours fériés et trafic autoroutier.
    - Outil `search_luxembourg_events_and_works(...)` : recherche croisée textuelle et spatiale sur perturbations et chantiers.
    - Outil `query_dataset(dataset, commune, limit)` : accès direct structuré et sécurisé aux tables Gold autorisées.
  - Commandes CLI dans `src/openlux/cli.py` :
    - `openlux serve [--host] [--port]` pour démarrer l'API Uvicorn en lecture seule sur les Parquet Gold.
    - `openlux mcp` pour démarrer le serveur FastMCP en mode standard stdio.
  - Fonctions utilitaires Gold dans `src/openlux/core/gold.py` (`get_gold_table_path`, `get_gold_metadata`, `query_gold_table`).
  - Suite de tests 100 % offline dans `tests/test_api_contracts.py` (contrats `_meta`, rejet d'injections SQL, streaming CSV/GeoJSON, documentation Swagger et 4 outils FastMCP).


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
