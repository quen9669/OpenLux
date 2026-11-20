# ADR-001 : DuckDB et Parquet ZSTD vs PostgreSQL / Apache Iceberg

- **Statut** : Accepté
- **Date** : 2026-11-20

## Contexte
OpenLux Hub a pour objectif de collecter, transformer et exposer les données ouvertes du Grand-Duché de Luxembourg sur 20 domaines distincts. Le système doit pouvoir s'exécuter localement sur la machine d'un contributeur, en CI (GitHub Actions) sans coût d'infrastructure récurrent, et sur un petit serveur VPS avec un minimum de maintenance opérationnelle.
Nous devons choisir le format de stockage et le moteur analytique pour les couches Silver et Gold.

## Options envisagées
1. **Option A : Base relationnelle persistante hébergée (PostgreSQL + PostGIS)**
   - *Avantages* : ACID complet, transactions concurrentes natives, standard de l'industrie.
   - *Inconvénients* : Nécessite un démon permanent, gestion de backups, migrations de schéma lourdes, latence de connexion, coût de maintenance hors-ligne nul impossible sans Docker ou service managé payant.
2. **Option B : Lac de données moderne (Apache Iceberg / Delta Lake + MinIO/S3)**
   - *Avantages* : Time-travel, transactions concurrentes sur stockage objet, standard des grands lacs de données.
   - *Inconvénients* : Nécessite un metastore (Catalog REST, Hive, Nessie), sur-ingénierie massive pour un volume prévisible à l'échelle du Luxembourg (< 10 Go par an en Gold), dépendances Java ou wrappers complexes.
3. **Option C : DuckDB embarqué + Stockage Gold en fichiers Parquet compressés ZSTD**
   - *Avantages* : Moteur analytique vectorisé in-process ultra-rapide (C++), extension géospatiale native (`spatial`), zéro démon à maintenir, interopérabilité directe avec dbt (`dbt-duckdb`), streaming direct Parquet vers CSV/GeoJSON en mémoire (`:memory:`), découplage total écriture / lecture via un répertoire temporaire et `os.replace()`.
   - *Inconvénients* : Écritures mono-processus simultanées sur la base DuckDB (contourné par l'export immédiat en Parquet immuable pour les consommateurs).

## Décision
Retenir l'**Option C : DuckDB + Parquet ZSTD**.
Les transformations SQL Silver $\rightarrow$ Gold s'exécutent en batch via `dbt-duckdb`. Les tables Gold sont écrites dans `data/gold/.tmp/{table}.parquet` puis basculées de manière atomique via `os.replace()` dans `data/gold/{table}.parquet`. Les serveurs FastAPI et FastMCP lisent uniquement ces fichiers Parquet en mémoire vive (`:memory:`) sans jamais poser de verrou sur le pipeline d'ingestion.

## Conséquences
- **Positives** :
  - Zéro coût d'infrastructure et exécution 100 % reproductible en local comme en CI.
  - Découplage lecture/écriture parfait : FastAPI et FastMCP ne subissent aucun verrouillage pendant les réécritures Gold.
  - Portabilité totale : un fichier `.parquet` peut être inspecté avec n'importe quel outil moderne (Python, DuckDB CLI, R, Polars).
- **Compromis acceptés** :
  - Pas d'accès transactionnel multi-écrivains simultané (le pipeline s'exécute séquentiellement ou par partitionnement de sources).
- **Critère de réévaluation** :
  - Si le volume de données historiques Gold dépasse 10 Go et que des écritures concurrentes distribuées en quasi temps réel deviennent indispensables (voir Backlog V2.2).
