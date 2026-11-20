# AGENTS.md — Contrat Opérationnel pour Antigravity (OpenLux Hub)

> Ce fichier définit les règles strictes à respecter à **chaque session** sur le dépôt `openlux-hub`.
> Spécification complète du projet : **`OPENLUX_BLUEPRINT.md`**.

---

## 1. Mission & Philosophie

Tu agis en tant que **développeur senior minimaliste** (Data Engineering, Gouvernance, MLOps, AI Engineering).
Ton objectif est de livrer vite, proprement, avec un maximum de transparence et un **minimum de code**.

**Question réflexe avant toute ligne de Python :**
> *"Peut-on exprimer ceci en quelques lignes dans `config/sources.toml` ou en SQL déclaratif dans `dbt_project/` ?"*

---

## 2. Garde-Fous Non Négociables

1. **Budget de code strict** :
   - Cœur Python (`src/openlux/`) : **$< 1\,500$ lignes au total** (cible $< 1\,200$).
   - Fonction : **$\le 40$ lignes** (parser pur dans `core/parsers.py` : **$\le 30$ lignes**).
   - Fichier Python : **$\le 200$ lignes**.
   - Zéro abstraction prématurée, zéro classe factory inutile, zéro duplication de code entre sources.

2. **Verrouillage des dépendances (7 runtime exactes)** :
   - Runtime autorisées uniquement : `httpx`, `pydantic`, `duckdb`, `dbt-duckdb`, `beautifulsoup4`, `fastapi` (+ `uvicorn`), `fastmcp`.
   - Dev autorisées uniquement : `pytest`, `ruff`.
   - Config : utiliser **`tomllib`** (bibliothèque standard Python 3.12), **ne pas** ajouter `pyyaml`.
   - **Interdiction absolue** d'ajouter une autre bibliothèque sans accord explicite de l'utilisateur et création d'un ADR dans `docs/adr/`.

3. **Atomicité & Concurrence** :
   - **1 entrée `[[sources]]` dans `config/sources.toml` = 1 flux HTTP atomique** (regroupés par `domain`).
   - **Couche Gold** : stocker uniquement des fichiers **`.parquet` (ZSTD)** sur disque. Toujours écrire dans `data/gold/.tmp/{table}.parquet` puis basculer via `os.replace()`. Ne pas écrire de `.csv` statiques dans `data/gold/` (FastAPI les streame à la volée).
   - **Fraîcheur vs Mutation** : toujours logger `last_checked_utc` (y compris quand le hash SHA-256 renvoie `UNCHANGED`) séparément de `last_changed_utc`.

4. **Sécurité, RGPD & Juridique** :
   - **Zero-PII** : le sanitizer (`core/sanitizer.py`) nettoie récursivement les *valeurs chaînes* et *nœuds texte* avant toute écriture Bronze, sans jamais altérer la syntaxe JSON/XML.
   - **Factual-Only** : pour `factual_only = true`, appliquer une liste blanche de champs factuels, bloquer tout texte éditorial (`body`, `description`, `summary`) et tronquer `title` à $\le 140$ caractères.
   - **Anti-injection SQL** : dans FastAPI et FastMCP, valider le nom de dataset contre la **whitelist du registre Gold** et passer tous les paramètres de requête via **`?`** dans DuckDB (jamais de f-string SQL sur une entrée utilisateur).
   - **Clés API optionnelles** : si `auth_env_var` est absent de l'environnement, ne jamais faire planter le pipeline — basculer sur le backup ou marquer la source `NOT_TESTED`.

5. **Tests 100 % Offline & Déterministes** :
   - Les tests unitaires et d'intégration (`pytest`) ne doivent **jamais** dépendre du réseau.
   - Utiliser des échantillons anonymisés dans `tests/fixtures/` et **`httpx.MockTransport`**.

6. **Respect strict du Hors-Scope V1** :
   - Ne jamais introduire Docker complexe, Airflow, Dagster, n8n, Grafana, Prometheus, Postgres, Next.js, MLflow ou Iceberg pendant les Phases 0 à 4.

---

## 3. Standards de Code & Transparence Documentaire

### 3.1 Style Python
- Python 3.12+, `from __future__ import annotations`, type hints complets sur toutes les fonctions.
- Formatage et lint stricts : `uv run ruff check .` et `uv run ruff format --check .` doivent toujours passer sans warning.
- En-tête concis obligatoire en haut de chaque fichier Python (3 à 5 lignes) :
  ```python
  """Rôle : <responsabilité unique du module>.
  Entrées/Sorties : <ce qu'il lit et produit>.
  Hors-scope : <ce qu'il ne fait volontairement pas>.
  """
  ```
- **Commentaires orientés *pourquoi*** : ne jamais paraphraser du code évident. Utiliser le préfixe `# POURQUOI : ...` pour documenter toute règle métier, contournement d'API externe, contrainte RGPD ou choix de performance.

### 3.2 Documentation Synchrone (Obligatoire dans le même lot)
Un travail n'est **pas terminé** tant que la documentation n'est pas synchronisée :
- Ajout/modification de module, flux ou table Gold $\rightarrow$ mettre à jour **`docs/ARCHITECTURE.md`**.
- Petit arbitrage technique (seuil, filtre, compromis API, gestion d'edge case) $\rightarrow$ ajouter une ligne dans **`docs/DECISIONS_LOG.md`**.
- Choix structurant $\rightarrow$ créer/mettre à jour **`docs/adr/NNN-titre.md`**.
- Fin de phase ou vague $\rightarrow$ mettre à jour **`CHANGELOG.md`**.

---

## 4. Protocole d'Exécution par Checkpoints

Avancer strictement **phase par phase** (et vague par vague en Phase 3) selon la Section 7 de `OPENLUX_BLUEPRINT.md`.

### Avant de déclarer une étape terminée, exécuter :
```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```
*(Et dès la Phase 1 en place : `uv run dbt parse` / `uv run dbt test` + comptage des lignes de `src/openlux/`.)*

### Format obligatoire du Bilan de Checkpoint
À la fin de chaque phase/vague, afficher un résumé structuré puis **s'arrêter et attendre la validation humaine** :
1. **Fichiers créés / modifiés** (liste concise).
2. **Budget de code** : nombre total de lignes dans `src/openlux/` (et fichier le plus long).
3. **Vérifications exécutées** : résultats exacts de `ruff`, `pytest`, `dbt test` et commande CLI testée.
4. **Transparence & Décisions** : mises à jour effectuées dans `docs/ARCHITECTURE.md`, `docs/DECISIONS_LOG.md` et `docs/adr/`.
5. **Question de validation** : proposer explicitement le passage à l'étape suivante ou demander les ajustements souhaités.
