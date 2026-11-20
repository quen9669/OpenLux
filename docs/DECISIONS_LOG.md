# Decisions Log — Arbitrages Techniques Quotidiens

Ce journal recense tous les arbitrages techniques, petits compromis d'intégration, seuils de filtrage et choix d'implémentation réalisés au cours du développement d'OpenLux Hub.

| Date | Sujet | Choix retenu | Pourquoi | Réversible ? |
| :--- | :--- | :--- | :--- | :---: |
| 2026-11-20 | Format de config | TOML (`tomllib`) au lieu de YAML | Évite `pyyaml` en dépendance runtime et reste strictement à 7 dépendances conformes au manifeste | Oui |
| 2026-11-20 | Partitionnement Bronze | `data/bronze/{source}/YYYY/MM/DD/*.gz` | Format immuable simple, hiérarchique, rejouable hors-ligne sans dépendre d'un metastore | Oui |
| 2026-11-20 | Format Gold physique | Parquet ZSTD unique dans `data/gold/` | Écritures atomiques via `.tmp/` et `os.replace()`, zéro lock, streaming CSV/GeoJSON à la volée | Oui |
| 2026-11-20 | Référentiel Communes | 100 communes officielles (fusion 2023) | Intègre les fusions Bous-Waldbredimus et Groussbus-Wal | Non (référence légale) |
| 2026-11-20 | Version DuckDB runtime | `duckdb>=1.1.0,<1.2.0` (1.1.3) | Version éprouvée acceptée par Windows Smart App Control (bloquait 2.0.1 non signé) | Oui |
| 2026-11-20 | Résolution chemin dbt DuckDB | `{{ env_var('OPENLUX_DUCKDB_PATH', 'data/openlux.duckdb') }}` | Exécution uniforme des commandes dbt depuis la racine du projet | Oui |
| 2026-11-20 | Exécution dbt dans CLI | Subprocess racine avec `--project-dir dbt_project --profiles-dir dbt_project` | Évite toute confusion de chemin relatif et les erreurs d'encodage système Windows sous Python | Oui |
| 2026-11-20 | Regex détection téléphones | Préfixe explicite (`+352`, `00352`, intl) ou $\ge 2$ séparateurs (`247 12 34`) | Évite tout faux positif sur timestamps ISO, années, codes postaux ou coordonnées GPS | Oui |
| 2026-11-20 | Distinction Fraîcheur vs Mutation | $S_{\text{fraîcheur}}$ calculé sur `last_checked_utc` | Une source stable `UNCHANGED` (SHA-256 stable) conserve un score nominal de 100 sans fausse alerte | Non (principe MLOps) |
| 2026-11-20 | Statut de repli Backup | Si `source_used == "backup"`, statut `ATTENTION` et score plafonné à 84.0 | Reflète fidèlement l'état dégradé d'une source même si toutes les données sont complètes | Oui |
| 2026-11-20 | Fichier `latest.{ext}.gz` Bronze | Écrit en miroir de l'archive horodatée | Permet des modèles dbt staging instantanés sans scanner l'arborescence complète par glob | Oui |
| 2026-11-21 | Whitelist stricte Gold pour API/MCP | Whitelist basée sur les fichiers réels `gold_*.parquet` + rejet direct des caractères suspects (`/`, `\`, `;`, `'`, `"`, `..`) | Bloque à la racine toute tentative d'injection SQL ou de path traversal avant toute exécution DuckDB | Non (garde-fou sécurité) |
| 2026-11-21 | Requêtes DuckDB in-memory (`:memory:`) | Connexions éphémères `:memory:` lisant `read_parquet(?)` pour FastAPI et FastMCP | Aucun verrou de lecture/écriture sur `data/openlux.duckdb` ; isolation totale des requêtes web concurrentes | Oui |
| 2026-11-21 | Streaming CSV et GeoJSON à la volée | Générateur `_stream_export()` lisant DuckDB par blocs de 500 lignes | Zéro fichier statique CSV/GeoJSON sur disque ; mémoire tampon bornée quel que soit le volume | Oui |
| 2026-11-21 | Comparaison temporelle DuckDB | `TRY_CAST(? AS TIMESTAMP)` pour les paramètres de date sur colonnes `TIMESTAMP` | Résout l'erreur `BinderException` DuckDB interdisant la comparaison implicite `TIMESTAMP` vs `VARCHAR` | Non (syntaxe SQL DuckDB) |
| 2026-11-21 | Alias sans préfixe `gold_` | `get_gold_table_path()` accepte indifféremment `weather_observations` et `gold_weather_observations` | Ergonomie utilisateur maximale dans l'API REST et les requêtes FastMCP sans rupture | Oui |
