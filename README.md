# OpenLux Hub 🇱🇺

> Plateforme open source et open data unifiée pour le Grand-Duché de Luxembourg.
> Architecture minimaliste, déclarative, pilotée par la configuration et 100 % reproductible.

[![CI](https://github.com/quen9669/OpenLux/actions/workflows/ci.yml/badge.svg)](https://github.com/quen9669/OpenLux/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)

---

## 🎯 Mission

Fédérer les données publiques **réelles et vérifiées** du Luxembourg (45 flux, 24 tables Gold : météo, air, eau, trafic LU et frontalier, transports, mobilité, économie, logement, calendrier, culture). Aucune donnée n'est inventée : une source en échec produit 0 ligne et un statut `ERROR`. Catalogue : [docs/DATA_CATALOG.md](docs/DATA_CATALOG.md) ; vérification des sources : [docs/sources/](docs/sources/).
- **Priorité Absolue — Rétention Incrémentale Stricte (Zéro Suppression)** : Chaque rechargement accumule les données au fur et à mesure sans jamais supprimer l'historique importé (`UNION ALL BY NAME` + `SELECT DISTINCT` sur l'ensemble des tables).
- **Priorité Absolue — Couverture des 12 Cantons & Historique Maximum** : Couverture géographique exhaustive sur l'ensemble des 12 cantons du Grand-Duché et récupération du maximum d'historique glissant possible (météo, air, crues, etc.).
- **Bronze** : Données brutes immuables compressées (`.json.gz`, `.csv.gz`), rejouables hors-ligne.
- **Silver / Gold** : Modélisation analytique SQL déclarative (`dbt-duckdb`), exports Parquet compressés ZSTD.
- **Zero-PII & Factual-Only** : Filtrage strict des données personnelles et respect absolu du droit d'auteur.
- **Multi-canaux** : API REST (FastAPI / OpenAPI), serveur MCP pour agents IA (`fastmcp`), et publication certifiée sur `data.public.lu`.

---

## ⚡ Démarrage Rapide

```bash
# 1. Cloner et installer les dépendances avec uv
git clone https://github.com/quen9669/OpenLux.git
cd OpenLux
uv sync

# 2. Exécuter la suite de tests 100 % hors ligne (sur de vraies réponses réduites)
uv run pytest

# 3. Lancer la CLI unifiée
uv run openlux --help

# 4. Valider la publication Open Data et les métadonnées (DCAT-AP-LU, Data Package)
uv run openlux publish --dry-run

# 5. Lancer l'API REST FastAPI (Swagger interactif sur http://127.0.0.1:8000/docs)
uv run openlux serve

# 6. Lancer le serveur FastMCP pour agents IA (Claude Desktop, Antigravity, Cursor)
uv run openlux mcp
```

---

## 📊 Standards Open Data & Formats Européens

OpenLux intègre nativement les standards de référence attendus par `data.public.lu` et les directives européennes :
- **Catalogue & Profils** : `datapackage.json` (Frictionless Data Package) et `dcat_ap_lu.json` (DCAT-AP-LU 2.0).
- **Transports & Lignes** : **NeTEx** (CEN/TS 16614), **SIRI** (CEN/TS 15531) et **GTFS / GTFS-RT**.
- **Trafic & Voirie** : **DATEX II** (CEN/TS 16157).
- **Géolocalisation** : Coordonnées WGS84 (EPSG:4326) et GeoJSON standardisé.
- **Analytique & Performance** : Fichiers Parquet compressés en ZSTD (zéro CSV statique sur disque).

---

## 📓 Notebooks Pédagogiques

Retrouvez des guides interactifs prêts à l'emploi dans [`notebooks/`](notebooks/) :
- [`01_quickstart_api_csv.ipynb`](notebooks/01_quickstart_api_csv.ipynb) : Prise en main rapide, requêtes DuckDB in-memory sans serveur, API REST et streaming CSV.
- [`02_analyse_contexte_lu.ipynb`](notebooks/02_analyse_contexte_lu.ipynb) : Analyse territoriale consolidée, suivi de qualité en 1 clic (`data_quality_grade`, `data_completeness_pct`), géolocalisation des grèves frontalières et parcs de mobilité 24/7.

---

## 🌐 Exposition Multi-Canaux

### API REST FastAPI (`openlux serve`)
- `GET /v1/status` : santé de chaque source, Trust Scores (0-100) et horodatages SLA.
- `GET /v2/` : site public (catalogue mesuré, supervision) ; `/` y redirige.
- `GET /v1/datasets` : Catalogue dynamique des Data Marts Gold (descriptions, licences, schémas).
- `GET /v1/data/{dataset}` : Requête sécurisée avec paramètres liés `?` (commune, date_from, date_to, lat, lon, radius_km, limit, offset) et enveloppe standard `_meta`.
- `GET /v1/exports/{dataset}.parquet` : Téléchargement direct du fichier Parquet ZSTD officiel.
- `GET /v1/exports/{dataset}.csv` : Streaming CSV à la volée depuis DuckDB in-memory (zéro duplication disque).
- `GET /v1/exports/{dataset}.geojson` : Streaming GeoJSON FeatureCollection à la volée.
- `GET /docs` & `/redoc` : Documentation OpenAPI interactive auto-générée.

### Serveur FastMCP (`openlux mcp`)
Connectez vos agents IA directement au serveur MCP standardisé :
1. `get_platform_health(domain)` : Observabilité, fraîcheur et Trust Scores des flux.
2. `get_luxembourg_day_context(date, canton)` : contexte quotidien d'un canton (météo, air, fériés, trafic, chantiers).
3. `search_luxembourg_events_and_works(...)` : Recherche croisée textuelle et géospatiale sur les chantiers et perturbations autoroutières.
4. `query_dataset(dataset, commune, limit)` : Requête directe et sécurisée sur n'importe quel Data Mart Gold.

---

## 🏛️ Architecture & Philosophie

Le projet repose sur 4 outils et **exactement 7 bibliothèques runtime** verrouillées (`httpx`, `pydantic`, `duckdb`, `dbt-duckdb`, `beautifulsoup4`, `fastapi`, `fastmcp`).

Pour en savoir plus :
- [Architecture Complète](docs/ARCHITECTURE.md)
- [Contrat Opérationnel Antigravity](AGENTS.md)
- [Blueprint d'Ingénierie v2](OPENLUX_BLUEPRINT.md)
- [Gouvernance, RGPD & Licences](docs/GOVERNANCE_GDPR.md)
- [Journal des Décisions (ADR)](docs/adr/)
- [Santé des Sources en Direct](STATUS.md)
