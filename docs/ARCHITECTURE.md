# OpenLux Hub — Architecture Technique (v1.5)

> Ce document vivant décrit l'état actuel et l'architecture cible d'OpenLux Hub.
> Il est mis à jour à chaque évolution de module, ajout de flux ou modification de schéma.

---

## 1. Vue d'Ensemble & Flux de Données

```mermaid
flowchart LR
    subgraph CFG["Configuration Unique"]
        TOML["config/sources.toml<br/>(Flux atomiques, domaines, backups,<br/>SLA, licences, limites IA)"]
    end

    subgraph ING["1. Collecte Python (3 Adaptateurs + PARSERS)"]
        ADAPT["BaseCollector (--due)<br/>(http_json | http_csv | http_jsonld | PARSERS)<br/>Fallback auto + Hash SHA-256 + Filtre Zero-PII"]
        BRZ[("BRONZE (Brut Immuable)<br/>data/bronze/{source}/YYYY/MM/DD/*.gz<br/>(Rejeu offline via rebuild)")]
    end

    subgraph TRF["2. Transformation SQL (dbt-duckdb)"]
        SLV["SILVER (DuckDB)<br/>Typage, WGS84 EPSG:4326,<br/>Communes LAU, Dédoublonnage, SCD2"]
        TMP["data/gold/.tmp/*.parquet"]
        GLD[("GOLD (Source de Vérité Unique)<br/>data/gold/*.parquet (ZSTD)<br/>Bascule atomique os.replace()")]
    end

    subgraph OBS["3. Qualité & Observabilité"]
        DBTR["target/run_results.json<br/>(Résultats dbt test)"]
        DQ["Moteur Trust Score (0-100)<br/>Table obs_runs (DuckDB)<br/>last_checked vs last_changed"]
        STAT["STATUS.md (auto) +<br/>Webhook Discord/Telegram"]
    end

    subgraph EXP["4. Exposition Multi-Canaux"]
        API["FastAPI (Swagger /docs)<br/>Routeur sécurisé (Whitelist + ?)<br/>Stream CSV / GeoJSON à la volée"]
        MCP["Serveur FastMCP<br/>4 Outils sémantiques IA<br/>+ known_limitations"]
        ODL["Synchro API data.public.lu<br/>(CC0/CC-BY + datapackage.json + CSV)"]
    end

    TOML --> ADAPT
    ADAPT --> BRZ
    BRZ --> SLV
    SLV --> TMP
    TMP -->|os.replace| GLD
    ADAPT --> DQ
    SLV --> DBTR
    DBTR --> DQ
    DQ --> STAT
    GLD -->|Lecture seule :memory:| API
    GLD -->|Lecture seule :memory:| MCP
    GLD --> ODL
```

---

## 2. Découpage des Couches de Données & Ingestion Incrémentale Stricte

### 2.1 Couche Bronze (Immuable & Rejouable)
- **Format** : Fichiers bruts compressés GZIP (`.json.gz`, `.csv.gz`).
- **Chemin** : `data/bronze/{source_id}/YYYY/MM/DD/{source_id}_{timestamp_utc}_{hash8}.[json|csv].gz` et miroir `latest.[json|csv].gz`.
- **Garantie** : Sanitized Zero-PII et Factual-Only appliqués en amont de l'écriture. Les payloads inchangés (`UNCHANGED`) ne créent pas de nouveau fichier physique.
- **Rétention Historique** : L'ensemble des archives quotidiennes est conservé.
- **Rejeu** : `uv run openlux rebuild` permet de reconstruire l'intégralité des couches Silver et Gold sans aucun accès internet.

### 2.2 Couche Silver (Normalisation, Typage SQL & Scan Historique Wildcard)
- **Moteur** : DuckDB via `dbt-duckdb`.
- **Modèles** :
  - `staging` : Décompression et typage à la volée lisant la totalité de l'historique Bronze via glob (`**/*.json.gz`, `**/*.csv.gz`, `union_by_name = true`) avec `SELECT DISTINCT`.
  - `silver` : Standardisation temporelle en UTC (`TIMESTAMP`), coordonnées projetées en WGS84 (`lat`, `lon` en EPSG:4326), jointure sur le référentiel officiel des 100 communes (`commune_lau`).
  - **Couverture Cantons** : Couverture géographique obligatoire sur les 12 cantons du pays (Capellen, Clervaux, Diekirch, Echternach, Esch-sur-Alzette, Grevenmacher, Luxembourg, Mersch, Redange, Remich, Vianden, Wiltz).

### 2.3 Couche Gold (Rétention Incrémentale Zéro Suppression)
- **Format** : Uniquement fichiers Parquet compressés **ZSTD** dans `data/gold/{nom_table}.parquet`.
- **Atomicité & Incrémentalité Stricte** : Écriture systématique dans `data/gold/.tmp/{nom_table}.parquet` en exécutant un `SELECT DISTINCT *` fusionnant l'existant (`read_parquet`) et le nouveau lot (`UNION ALL BY NAME SELECT * FROM {table}`), puis basculement instantané via `os.replace()`. Aucune donnée importée n'est jamais écrasée ou supprimée. DuckDB interne est synchronisé via `CREATE OR REPLACE TABLE AS SELECT * FROM read_parquet(...)`.
- **Isolation Lecture/Écriture** : FastAPI et FastMCP chargent les Parquet en mémoire vive (`:memory:`) ; ils ne subissent aucun verrouillage d'écriture.

---

## 3. Stack Technique Verrouillée

| Outil / Dépendance | Usage Exclusif |
| :--- | :--- |
| **Python 3.12+ & `uv`** | Environnement, `tomllib` natif, packaging et exécution CLI |
| **`httpx`** | Téléchargements HTTP, retries, `MockTransport` pour tests offline déterministes |
| **`pydantic`** | Validation du contrat `sources.toml`, modèles qualité et métadonnées API (`_meta`) |
| **`duckdb`** (+ `spatial`) | Moteur analytique in-process, calculs spatiaux, streaming CSV/GeoJSON |
| **`dbt-duckdb`** | Transformations SQL déclaratives, tests d'intégrité, génération du catalogue de données |
| **`beautifulsoup4`** | Extraction sélective des balises schema.org/Event `<script type="application/ld+json">` |
| **`fastapi` (+ `uvicorn`)** | API REST haute performance avec documentation OpenAPI / Swagger automatique |
| **`fastmcp`** | Serveur MCP (Model Context Protocol) branché sur les Parquet Gold |
| **`pytest` & `ruff`** | Tests unitaires hors-ligne, validation statique de types, lint et formatage strict |

---

## 4. Contrat de Métadonnées MLOps (`_meta`)

Chaque appel API `/v1/data/{dataset}` et chaque outil FastMCP fournit cette enveloppe standardisée (Section 5.3 du Blueprint) :
```json
{
  "_meta": {
    "dataset": "gold_crossborder_traffic",
    "trust_score": 100.0,
    "status": "GOOD",
    "is_stale": false,
    "last_checked_utc": "2026-11-20T22:00:00Z",
    "last_changed_utc": "2026-11-20T21:00:00Z",
    "source_used": "primary",
    "source_url": "https://data.public.lu/fr/datasets/r/traffic-fr-a31.json",
    "license_spdx": "Open-EU",
    "commercial_use_safe": true,
    "known_limitations": "Données DIR Est / Bison Futé indicatives...",
    "run_id": "uuid-v4",
    "pipeline_git_sha": "git_v1",
    "row_count": 6
  },
  "data": []
}
```

---

## 5. Modules Cœur Implémentés (Phase 4 — Finalisation Open Source & Publication)

| Module | Rôle & Responsabilité Unique | Lignes |
| :--- | :--- | :---: |
| `src/openlux/config.py` | Chargement natif `tomllib` et validation Pydantic de `config/sources.toml` | 47 |
| `src/openlux/core/sanitizer.py` | Filtrage récursif Zero-PII (emails, téléphones) et garanties Factual-Only | 56 |
| `src/openlux/core/parsers.py` | Registre central `PARSERS` : fonctions pures $\le 30$ lignes (DATEX II, grèves, parkings RFC 2822, carburants) | 170 |
| `src/openlux/core/parsers_extra.py` | Parsers spécialisés (STATEC permis SDMX, OpenSky, VDL chantiers ms Epoch, Vel'oH JCDecaux v3) | 171 |
| `src/openlux/core/parsers_env.py` | Parsers environnementaux & macro (qualité de l'air, pollen, météo Open-Meteo, spot SMARD, inflation STATEC) | 171 |
| `src/openlux/core/collector.py` | Moteur de collecte unifié (3 adaptateurs + custom, auth query params, fallback, SHA-256, Bronze résilient) | 172 |
| `src/openlux/core/quality.py` | Calcul du Trust Score (0-100), traçabilité MLOps, table `obs_runs` et historique | 178 |
| `src/openlux/core/monitoring.py` | Régénération de `STATUS.md`, payload de supervision et métriques Prometheus | 180 |
| `src/openlux/core/gold.py` | Exportation atomique `.tmp` $\rightarrow$ `os.replace()`, whitelist et conservation incrémentale | 191 |
| `src/openlux/publish/opendata_lu.py` | Métadonnées conformes (DCAT-AP-LU, Data Package), compactage Bronze & publication | 138 |
| `src/openlux/api/main.py` | API REST FastAPI : cache résilient DuckDB, `/status`, `/metrics` (Prometheus), auto-sync lifespan | 163 |
| `src/openlux/mcp/server.py` | Serveur FastMCP : 4 outils sémantiques IA connectés aux Data Marts Gold | 148 |
| `src/openlux/cli.py` | CLI unifiée (`openlux run`, `schedule`, `rebuild`, `status`, `compact`, `publish`, `serve`, `mcp`) | 187 |
| `src/openlux/**/__init__.py` | En-têtes et initialisations de packages | 9 |
| **Total Cœur Python** | **Tous les fichiers $\le 200$ lignes (strictement $\le 191$)** | **1 981** |


---

## 6. Domaines et Data Marts Actifs (40 Sources, 20 Domaines, 24 Tables Gold)

| # | Domaine | Sources Atomiques Incluses | Table Gold Produite | Format & Moteur |
| :-: | :--- | :--- | :--- | :--- |
| **1** | `weather` | `meteo_lux_obs` | `gold_weather_observations.parquet` | Parquet ZSTD (dbt DuckDB) |
| **2** | `traffic_cita` | `traffic_cita_datex2` | `gold_traffic_events.parquet` | Parquet ZSTD (dbt DuckDB) |
| **3** | `holidays_vacations` | `holidays_lu` | `gold_holidays.parquet` | Parquet ZSTD (dbt DuckDB) |
| **4** | `air_quality` (3A) | `air_quality_lu` | `gold_air_quality.parquet` | Parquet ZSTD (dbt DuckDB) |
| **5** | `water_levels` (3A) | `water_levels_lu` | `gold_water_levels.parquet` | Parquet ZSTD (dbt DuckDB) |
| **6** | `economy_fuel` (3A) | `fuel_prices_lu`, `statec_inflation` | `gold_fuel_prices.parquet`, `gold_statec_inflation.parquet` | Parquet ZSTD (dbt DuckDB) |
| **7** | `energy_climate` (3A) | `electricity_spot_delu`, `radioactivity_lu`, `bathing_water_lu` | `gold_electricity_spot.parquet`, `gold_radioactivity.parquet`, `gold_bathing_water.parquet` | Parquet ZSTD (dbt DuckDB) |
| **8** | `crossborder_traffic` (3B) | `traffic_fr_bisonfute`, `traffic_de_autobahn`, `traffic_be_trafiroutes`, `rail_crossborder` | `gold_crossborder_traffic.parquet` | Parquet ZSTD (dbt DuckDB) |
| **9** | `public_transit` (3B) | `transit_mobiliteit`, `transit_avl_rt` | `gold_public_transit.parquet` | Parquet ZSTD (dbt DuckDB) |
| **10** | `mobility_parkings` (3B) | `parkings_vdl` | `gold_mobility_parkings.parquet` | Parquet ZSTD (dbt DuckDB) |
| **11** | `mobility_veloh` (3B) | `veloh_stations` | `gold_mobility_veloh.parquet` | Parquet ZSTD (dbt DuckDB) |
| **12** | `chargy_stations` (3B) | `chargy_stations` | `gold_chargy_stations.parquet` | Parquet ZSTD (dbt DuckDB) |
| **13** | `aviation_noise` (3B) | `aviation_opensky_lu`, `noise_zones_lu` | `gold_aviation_noise.parquet` | Parquet ZSTD (dbt DuckDB) |
| **14** | `roadworks` (3C) | `roadworks_cita`, `roadworks_vdl` | `gold_roadworks.parquet` | Parquet ZSTD (dbt DuckDB) |
| **15** | `housing_construction` (3C) | `housing_observatoire`, `housing_statec`, `housing_market_listings` | `gold_housing_listings.parquet`, `gold_housing_stats.parquet`, `gold_housing.parquet` | Parquet ZSTD (dbt DuckDB) |
| **16** | `daily_life_sport` (3C) | `bike_lanes_lu`, `open_sundays_vdl`, `recycling_centers` | `gold_daily_life.parquet` | Parquet ZSTD (dbt DuckDB) |
| **15** | `concerts_culture` (3D) | `culture_echo_lu`, `culture_venues_jsonld` | `gold_culture_events.parquet` | Parquet ZSTD (dbt DuckDB) |
| **16** | `local_events_markets` (3D) | `events_vdl`, `events_visitlu` | *(inclus dans `gold_culture_events.parquet`)* | Parquet ZSTD (dbt DuckDB) |
| **17** | `major_venues` (3D) | `venues_luxexpo`, `venues_stade_coque` | *(inclus dans `gold_culture_events.parquet`)* | Parquet ZSTD (dbt DuckDB) |
| **18** | `strikes_disruptions` (3D) | `strikes_rss_lu` | `gold_strikes_disruptions.parquet` | Parquet ZSTD (dbt DuckDB) |
| **19** | `health_pollen_alerts` (3D) | `pollen_lu`, `aed_defib_lu`, `lu_alert` | `gold_health_alerts.parquet` | Parquet ZSTD (dbt DuckDB) |
| **20** | `civic_life` (3D) | `petitions_chd`, `unemployment_adem` | `gold_civic_life.parquet` | Parquet ZSTD (dbt DuckDB) |
| **-** | **Consolidation Globale** | *Les 8 signaux quotidiens unifiés sur 100 communes* | `gold_luxembourg_daily_context.parquet` | Parquet ZSTD (dbt DuckDB) |

---

## 7. Standards Open Data & Publication (data.public.lu)

OpenLux garantit la conformité stricte avec les standards nationaux et européens pour la publication open data :
- **Frictionless Data Package (`data/gold/datapackage.json`)** : Schéma normalisé de toutes les ressources Gold avec typage JSON Table Schema, sommes de contrôle SHA-256, licences SPDX et métadonnées d'interopérabilité.
- **Profil DCAT-AP-LU 2.0 (`data/gold/dcat_ap_lu.json`)** : Schéma d'échange conforme pour le portail national luxembourgeois `data.public.lu` (CKAN API).
- **Standards Sectoriels Reconnus** :
  - **Transports & Lignes** : NeTEx (CEN/TS 16614), SIRI (CEN/TS 15531), GTFS / GTFS-RT.
  - **Trafic & Événements Routiers** : DATEX II (CEN/TS 16157).
  - **Cartographie & SIG** : GeoJSON / WGS84 (EPSG:4326).
  - **Analytique & Tabulaire** : Parquet compressé en ZSTD.
- **Commandes Dédiées** :
  - `uv run openlux publish --dry-run` : Validation et génération des manifestes de métadonnées sans modification externe.
  - `uv run openlux compact` : Compactage mensuel Parquet des snapshots Bronze historiques.

---

## 8. Portail Web Officiel & Interface Utilisateur (SPA Native)

Le portail web officiel d'OpenLux Hub fournit une interface réactive épurée, futuriste et souveraine :
- **Architecture Minimaliste** : Single Page Application (SPA) native sans framework lourd (`web/index.html`, `web/css/style.css`, `web/js/app.js`). Servie directement par FastAPI via Starlette `StaticFiles` à la racine `/`.
- **Zéro Dépendance Runtime NPM** : Fonctionne 100 % hors-ligne sans build Node.js complexe.
- **Intégration API & Fallback Déterministe** : Interroge dynamiquement `/v1/datasets`, `/v1/status` et `/v1/data/{dataset}`. Si l'API n'est pas encore démarrée, bascule sans erreur sur un mock riche des 22 Data Marts.
- **Observabilité & Accès Multimodal** : Visualisation du Trust Score MLOps, schéma des colonnes, streaming CSV à la volée, téléchargement Parquet ZSTD d'origine, snippets DuckDB SQL in-memory et commandes FastMCP IA en 1 clic.
- **Studio Design System Figma** : Onglet dédié intégrant la validation granulaire de la charte graphique (palette WCAG AAA, typographie Inter / JetBrains Mono, matrice des 5 états des boutons, badges de santé pulsants).

---

## 9. Automatisation CI/CD & Synchronisation Continue des Données (GitHub Actions)

OpenLux Hub intègre un mécanisme d'ingestion et de synchronisation continue autonome via GitHub Actions :
- **Workflow Dédié (`.github/workflows/data_pipeline.yml`)** :
  - **Planification & Déclenchement** : Cron horaire régulier (`0 * * * *`) assurant la fraîcheur des données territoriales et déclenchement manuel interactif (`workflow_dispatch` avec option `--due`).
  - **Permissions Restreintes** : `permissions: contents: write` permettant le push sécurisé des modifications vers le dépôt sans exposition de token administrateur.
  - **Performance & Cache** : `astral-sh/setup-uv@v5` avec `enable-cache: true` et Python 3.12 pour des installations de dépendances quasi-instantanées.
  - **Exécution Unifiée** :
    1. Collecte résiliente des flux atomiques (`openlux run`).
    2. Transformations déclaratives SQL dbt (`seed --full-refresh`, `run`, `test`).
    3. Exportation incrémentale atomique de la couche Gold Parquet ZSTD (`data/gold/*.parquet`).
    4. Régénération des métadonnées Frictionless Data Package et DCAT-AP-LU 2.0 (`openlux publish --dry-run`).
    5. Actualisation du tableau de bord de santé MLOps `STATUS.md`.
  - **Commit Atomique Conditionnel** : Contrôle différentiel strict (`git diff --staged --quiet`) pour ne créer un commit (`chore(data): auto-update gold datasets and status [skip ci]`) que lorsque des enregistrements nouveaux ou des modifications sont détectés, sans boucle de déclenchement infinie (`[skip ci]`).
  - **Isolation Git & Hygiène du Dépôt** : `.gitignore` configuré pour suivre et versionner exclusivement `data/gold/*.parquet` et `data/gold/*.json`, tout en ignorant strictement les répertoires temporaires (`data/gold/.tmp/`), les fichiers de base de données DuckDB (`*.duckdb`) et les secrets locaux.


