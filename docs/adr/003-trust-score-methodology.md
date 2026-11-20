# ADR-003 : Méthodologie du Trust Score et Traçabilité MLOps

- **Statut** : Accepté
- **Date** : 2026-11-20

## Contexte
La fiabilité des données ouvertes est un défi majeur : APIs non documentées, changements silencieux de schémas, interruptions temporaires de service. Pour être exploitable par des applications critiques, des data scientists et des agents d'intelligence artificielle (via FastMCP), la plateforme doit fournir un indicateur objectif, déterministe et traçable de la qualité des données.
De plus, les agents IA ont besoin de connaître les limites connues (`known_limitations`) pour éviter les hallucinations.

## Options envisagées
1. **Option A : Statut binaire simple (UP / DOWN)**
   - *Inconvénients* : Ne capture pas les dérives lentes de volumétrie, les données périmées servies par une API en cache, ou les champs manquants.
2. **Option B : Métriques Prometheus / Grafana externes**
   - *Inconvénients* : Nécessite une pile d'observabilité lourde, non exposée nativement dans les contrats de données retournés aux agents IA ou aux API REST.
3. **Option C : Trust Score algorithmique (0 à 100) embarqué + table DuckDB `obs_runs` + contrat `_meta`**
   - *Avantages* : Calculé localement à chaque exécution du pipeline dans `core/quality.py`. Combine 4 dimensions quantitatives ($S_{\text{fraîcheur}}$, $S_{\text{complétude}}$, $S_{\text{validité}}$, $S_{\text{source}}$). Intègre directement les résultats des tests dbt depuis `target/run_results.json`. Injecté systématiquement dans l'enveloppe `_meta` des réponses API et MCP.

## Décision
Retenir l'**Option C : Trust Score algorithmique standardisé**.

### Formule mathématique :
$$\text{Trust Score} = 0.35 \cdot S_{\text{fraîcheur}} + 0.25 \cdot S_{\text{complétude}} + 0.20 \cdot S_{\text{validité}} + 0.20 \cdot S_{\text{source}}$$

### Règle d'or Fraîcheur vs Mutation :
- **`last_checked_utc`** : horodatage de la dernière vérification réussie de la source distante.
- **`last_changed_utc`** : horodatage du dernier changement effectif de contenu (détecté par hash SHA-256).
- **Conséquence clé** : si une source stable renvoie le même contenu (`UNCHANGED`), son $S_{\text{fraîcheur}}$ reste à `100` tant que `now - last_checked_utc <= SLA`, évitant la fausse pénalisation des tables référentielles peu mouvantes.

### Seuils et actions :
- `GOOD` (85 - 100) : Nominal.
- `ATTENTION` (60 - 84) : Backup actif, léger retard ou champs secondaires absents. Alerte envoyée si $> 3$ runs consécutifs en ATTENTION.
- `ERROR` (< 60) : Panne critique ou données corrompues. Notification immédiate par Webhook. L'API renvoie les dernières données valides avec le drapeau `is_stale: true`.
- `NOT_TESTED` : Source en cours de développement ou clé API absente en environnement local.

## Conséquences
- **Positives** :
  - Transparence absolue pour les consommateurs humains et IA.
  - Zéro duplication de tests : le score de validité exploite directement les résultats natifs de `dbt test`.
  - Prévention des hallucinations IA grâce aux métadonnées `known_limitations` et `is_stale`.
- **Compromis acceptés** :
  - Nécessite d'écrire l'historique des contrôles dans la table `obs_runs` de `data/openlux.duckdb`.
