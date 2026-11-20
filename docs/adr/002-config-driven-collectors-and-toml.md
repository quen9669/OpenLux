# ADR-002 : Approche Config-Driven (`sources.toml`) et 3 Adaptateurs Génériques

- **Statut** : Accepté
- **Date** : 2026-11-20

## Contexte
OpenLux Hub couvre 20 domaines distincts et des dizaines de flux de données (API REST JSON, CSV statiques et dynamiques, balises schema.org/Event JSON-LD, flux XML DATEX II, flux RSS).
Dans de nombreux projets d'open data, chaque source donne lieu à un script Python sur-mesure (`scrape_meteo.py`, `fetch_buses.py`), générant duplication de code réseau (retries, timeouts, headers), dispersion de la maintenance et dette technique ingérable.

## Options envisagées
1. **Option A : Un script Python dédié par source ou connecteur custom**
   - *Avantages* : Liberté totale pour coder chaque cas particulier.
   - *Inconvénients* : Explosion du volume de code (> 5 000 lignes), bugs répétés sur la gestion d'erreurs HTTP, violation du budget de code strict (< 1 500 lignes), revue de code fastidieuse.
2. **Option B : Orchestrateur lourd de web scraping (Scrapy / Airflow DAGs)**
   - *Avantages* : Frameworks riches avec plugins existants.
   - *Inconvénients* : Dépendances massives (Twisted, Celery, Redis), violation du verrouillage des 7 dépendances, overhead conceptuel disproportionné.
3. **Option C : Déclaration déclarative unique dans `config/sources.toml` + 3 adaptateurs génériques + registre `PARSERS`**
   - *Avantages* : 1 entrée `[[sources]]` = 1 flux HTTP atomique (source primaire + backup). 3 adaptateurs génériques couvrent 90 % des flux (`http_json`, `http_csv`, `http_jsonld`). Les formats spécifiques (DATEX II XML, RSS multilingue) sont délégués à des fonctions pures ($\le 30$ lignes) dans un registre `PARSERS`. Utilisation du module standard `tomllib` (Python 3.12), sans dépendance `pyyaml`.
   - *Inconvénients* : Nécessite une modélisation rigoureuse du schéma de configuration Pydantic.

## Décision
Retenir l'**Option C : Déclaration centralisée dans `config/sources.toml` pilotée par 3 adaptateurs génériques et un registre de parseurs purs**.
Ajouter une nouvelle source se résume dans 90 % des cas à ajouter une dizaine de lignes déclaratives dans `config/sources.toml` sans écrire une seule ligne de Python.

## Conséquences
- **Positives** :
  - Respect scrupuleux du budget de code (< 1 500 lignes pour tout le cœur Python).
  - Gestion uniforme des en-têtes HTTP, du User-Agent responsable, de la politique de fallback, du hachage SHA-256 (`UNCHANGED`) et du filtre Zero-PII.
  - Testabilité unitaire optimale : les adaptateurs sont testés avec `httpx.MockTransport`, et les parseurs sont des fonctions pures testées sur des fixtures statiques.
- **Compromis acceptés** :
  - Les sources extrêmement complexes nécessitent un parseur dédié dans `core/parsers.py`, limité contractuellement à 30 lignes.
- **Critère de réévaluation** :
  - Si un protocole réseau non-HTTP (ex: MQTT, WebSocket direct temps réel continu) devait être intégré dans une version future.
