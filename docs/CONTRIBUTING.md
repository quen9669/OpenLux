# Guide de Contribution — OpenLux Hub

Merci pour votre intérêt envers OpenLux Hub ! Ce projet applique une discipline rigoureuse inspirée du développement senior : **priorité absolue à la configuration déclarative et au SQL plutôt qu'au code Python impératif**.

---

## 1. Philosophie & Budget de Code

- **Budget global strict** : Le cœur Python (`src/openlux/`) est plafonné à moins de 1 500 lignes de code.
- **7 dépendances runtime verrouillées** : `httpx`, `pydantic`, `duckdb`, `dbt-duckdb`, `beautifulsoup4`, `fastapi`, `fastmcp`. Aucune bibliothèque supplémentaire ne peut être ajoutée sans un ADR approuvé.
- **Config-Driven** : Ne créez pas de script de scraping. Ajoutez une déclaration dans `config/sources.toml`.

---

## 2. Ajouter une Source en 15 Minutes

Dans 90 % des cas, ajouter une nouvelle source nécessite uniquement :

1. **Ajouter un bloc dans `config/sources.toml`** :
   ```toml
   [[sources]]
   id = "mon_flux_lu"
   domain = "weather"
   description = "Description concise de la source"
   semantic_summary = "Résumé pour les agents IA."
   known_limitations = "Limites et biais connus de la donnée."
   adapter = "http_json"  # ou http_csv, http_jsonld
   cadence_minutes = 60
   sla_minutes = 180
   retention_days = 90
   license_spdx = "CC0-1.0"
   commercial_use_safe = true
   publish_opendata_lu = true
   factual_only = false

   [sources.primary]
   url = "https://api.exemple.lu/data.json"
   headers = { User-Agent = "OpenLuxHub/1.0 (+https://github.com/quen9669/OpenLux)" }

   [sources.backup]
   adapter = "http_json"
   url = "https://backup.exemple.org/lu.json"

   [sources.quality]
   min_rows = 1
   required_fields = ["id", "timestamp"]
   ```

2. **Créer les modèles SQL correspondants dans `dbt_project/`** :
   - `models/staging/stg_mon_flux_lu.sql`
   - `models/silver/sil_mon_flux_lu.sql`
   - Intégrer dans la table Gold du domaine.

3. **Ajouter un échantillon anonymisé dans `tests/fixtures/`** et valider hors-ligne avec `pytest`.

---

## 3. Normes et Formats Sectoriels Recommandés

Lors de l'intégration et de la publication sur `data.public.lu`, veillez à renseigner ou respecter les standards sectoriels appropriés :
- **Transports en commun & Horaires** : NeTEx (CEN/TS 16614), SIRI (CEN/TS 15531), GTFS / GTFS-RT.
- **Trafic autoroutier & Événements routiers** : DATEX II (CEN/TS 16157).
- **Géolocalisation & Cartographie** : Coordonnées WGS84 (EPSG:4326) avec colonnes standardisées `latitude` et `longitude` (GeoJSON).
- **Catalogue & Indexation** : DCAT-AP-LU 2.0 (`data/gold/dcat_ap_lu.json`) et Frictionless Data Package (`data/gold/datapackage.json`).

---

## 4. Commandes de Validation Avant Toute Pull Request

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
cd dbt_project && uv run dbt test --profiles-dir .
uv run openlux publish --dry-run
uv run openlux compact
```
