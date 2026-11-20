# ADR-004 : Stratégie Zero-PII, Scraping Éthique et Conformité des Licences

- **Statut** : Accepté
- **Date** : 2026-11-20

## Contexte
OpenLux Hub agrège des flux variés issus d'administrations publiques, d'agendas culturels, de flux RSS de presse et de plateformes citoyennes.
Deux risques juridiques majeurs existent :
1. **Risque RGPD** : Ingestion involontaire de données à caractère personnel (emails de contact, numéros de téléphone directs, noms d'organisateurs d'événements privés).
2. **Risque de Propriété Intellectuelle (Droit d'auteur & Base de données)** : Ingestion et rediffusion de textes journalistiques, descriptions d'articles ou contenus éditoriaux protégés.

## Options envisagées
1. **Option A : Filtrage a posteriori au niveau de la couche Gold**
   - *Inconvénients* : Les PII et textes protégés sont stockés dans la couche Bronze immuable, ce qui constitue une violation du principe de minimisation RGPD (Art. 5.1.c du RGPD) et empêche une diffusion ouverte des archives.
2. **Option B : Filtrage récursif en amont (Zero-PII) et politique stricte Factual-Only avant stockage Bronze**
   - *Avantages* :
     - Les données personnelles sont caviardées avant même l'écriture sur disque (`data/bronze/`).
     - Pour les sources soumises à droit d'auteur (`factual_only = true`), seule une liste blanche de faits bruts non protégeables (`title` $\le 140$ caractères, dates, lieu, commune, URL source) est conservée ; tout corps de texte (`body`, `description`, `summary`) est rejeté.
     - Les schémas Silver/Gold sont fermés (interdiction de colonnes individuelles).

## Décision
Retenir l'**Option B : Zero-PII et Factual-Only en amont dès l'ingestion**.

### Règles techniques :
1. **Sanitizer Récursif (`core/sanitizer.py`)** :
   - Parcourt les structures (dictionnaires, listes, XML) et applique les regex d'anonymisation **exclusivement sur les chaînes de caractères** et les nœuds texte.
   - Ne modifie jamais les clés de dictionnaires, les nombres, les booléens, ni la structure syntaxique JSON ou XML.
   - Remplace les adresses email par `[REDACTED_EMAIL]` et les téléphones par `[REDACTED_PHONE]`.
2. **Contrat Factual-Only** :
   - Activé par `factual_only = true` dans `sources.toml`.
   - Limite le titre à 140 caractères maximum.
   - Supprime systématiquement tout champ éditorial descriptif.
3. **Schémas Silver et Gold fermés** :
   - Modélisation stricte par contrat SQL dbt interdisant tout champ PII.
   - Test bloquant dbt `tests/assert_no_pii_in_gold.sql` vérifiant l'absence d'emails ou de téléphones dans toutes les colonnes Gold.
4. **Licences et Open Data** :
   - Seuls les flux sous licence compatible (`CC0-1.0`, `CC-BY-4.0`, ou faits bruts vérifiés) sont autorisés à la republication sur `data.public.lu` (`publish_opendata_lu = true`).

## Conséquences
- **Positives** :
  - Conformité RGPD by design et respect total de la propriété intellectuelle.
  - Données Bronze et Gold 100 % rediffusables en open data sans risque de fuite de PII.
  - Procédure de retrait (takedown) claire documentée dans `docs/GOVERNANCE_GDPR.md`.
- **Compromis acceptés** :
  - Les descriptions détaillées d'événements culturels ne sont pas stockées dans la base ; l'utilisateur est renvoyé vers l'URL officielle (`source_url`).
