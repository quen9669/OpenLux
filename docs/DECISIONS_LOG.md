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
