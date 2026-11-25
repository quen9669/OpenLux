# ADR-006 : Refonte V3 — uniquement des données réelles et vérifiées

- **Statut** : Accepté
- **Date** : 2026-11-25

## Contexte
L'audit en direct du 24/11/2026 de chaque source et de chaque backup de `config/sources.toml` a montré :
- environ 25 URLs sur 40 inventées : liens `data.public.lu/fr/datasets/r/<nom-lisible>` (le vrai format utilise un UUID) et domaines inexistants (`api.chargy.lu`, `api.lualert.lu`, `news.openlux.lu`…) ;
- `ensure_bronze_baseline` qui copiait les fixtures de test dans Bronze dès qu'une source échouait : les tables Gold mélangeaient données réelles et fictives (niveaux d'eau, radioactivité, Chargy, transports…) ;
- des valeurs codées en dur dans les parsers et les modèles (inflation 1,7 %, cote 944,43, commune forcée à « Luxembourg », dates `2026-11-20`, valeur courante substituée aux heures manquantes, d'où -1 °C fin août) ;
- un seed des communes avec 23 codes LAU faux, des seeds non sourcés (annonces immobilières, marchés récurrents) et `dbt seed` qui échouait sans bruit.

## Options envisagées
1. **Corriger au cas par cas** en gardant l'architecture des données : rapide, mais les fixtures et les valeurs par défaut restent un risque permanent.
2. **Refonte « zéro donnée inventée »** : on reconstruit Gold depuis zéro, on ne garde que des sources vérifiées et on écrit des parsers qui laissent `None` quand une valeur manque.

## Décision
Option 2 :
- **Pas de substitut** : une source en échec écrit 0 ligne ; un échec total vaut toujours `ERROR`.
- **Un parser par endpoint** (le backup peut avoir le sien) ; la sortie du parser est la donnée Bronze.
- **Staging dbt à schéma explicite** (`read_json(columns=…)`) + Gold par domaine ; la couche Silver séparée est supprimée (le rattachement commune/canton est fait par une macro).
- **Fusion Parquet par clé métier** (`GOLD_KEYS`) : dernière version par clé, aucune clé passée supprimée. Cela remplace l'ancien `DISTINCT` sur toutes les colonnes, qui dupliquait chaque nouvelle version.
- **`data_origin` déclaré** par source : les modèles (Open-Meteo, CAMS) ne sont jamais présentés comme des mesures.
- **Lecture XLSX et GML en bibliothèque standard** (zipfile + ElementTree, inverse LAEA de Snyder), sans nouvelle dépendance.
- **Gold purgé et reconstruit** : l'historique accumulé du 20 au 24/11 était indissociable des lignes de fixtures.
- **Domaines sans source fiable retirés** plutôt que simulés (voir ARCHITECTURE §5).

## Conséquences
- Positives : chaque ligne publiée est traçable vers une URL publique testée ; tests sur de vraies réponses réduites ; site et API sans chiffre écrit à la main.
- Compromis acceptés :
  - Historique repartant du 25/11/2026 pour les flux instantanés (parkings, Vel'oh, Chargy, trafic) ; les séries longues viennent des sources elles-mêmes (IPCN depuis 1948, ADEM depuis 2012, prix des logements depuis 2010, électricité depuis 2025, météo et air sur 92 jours).
  - Rattachement commune par centroïde le plus proche (≤ 8 km) : approximatif aux frontières communales.
  - Plusieurs sources sans licence explicite (`unspecified` : Autobahn, iRail, OpenHolidays, echo.lu, Rockhal, Google News) sont marquées `commercial_use_safe = false` quand l'usage n'est pas garanti.
  - **Budget de code dépassé** : environ 2 700 lignes dans `src/openlux/` pour une cible de 1 500 (déjà 2 200 avant la refonte), réparties sur 45 flux et une dizaine de formats. Tous les fichiers font 200 lignes ou moins ; 2 fonctions préexistantes (`build_monitoring_payload`, `calculate_trust_score`) dépassent 40 lignes.
- Critère de réévaluation : si une source officielle apparaît pour un domaine retiré (radioactivité, LU-Alert « dernière alerte », temps réel RGTR/CFL), l'ajouter au registre avec son parser et un test sur une réponse réelle.
