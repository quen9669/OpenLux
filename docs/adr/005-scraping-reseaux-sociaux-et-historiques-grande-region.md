# ADR-005 : Stratégie d'Extension Massive des Données (Réseaux Sociaux, Immobilier & Historiques)

- **Statut** : Proposé / Documenté
- **Date** : 2026-11-21

## 1. Contexte & Objectif
OpenLux Hub vise à constituer la **base de données unifiée et normalisée de référence pour le Grand-Duché de Luxembourg et sa Grande Région**, accessible librement à tous (humains, data analysts, agents IA).
Pour maximiser la richesse et le volume des données centralisées, la question de l'intégration de nouvelles sources à forte valeur ajoutée a été posée :
1. **Événements & Vie Locale** : Collecte des manifestations et actualités depuis les réseaux sociaux (Instagram, Facebook, etc.).
2. **Marché Immobilier** : Prix réels des transactions et annonces locatives / ventes.
3. **Profondeur Historique** : Séries temporelles pluriannuelles sur l'énergie, la météo, le trafic et l'inflation.

---

## 2. Options Envisagées & Contraintes

### A. Réseaux Sociaux (Instagram, Facebook)
* **Option 1 : Scraping sauvage (headless browsers, rotation de proxies)** :
  - *Risques majeurs* : Violation directe des Conditions Générales d'Utilisation (Meta TOS), déclenchement immédiat de protections anti-bot (Cloudflare, CAPTCHAs bloquants), maintenance technique extrêmement lourde, et risque élevé d'ingestion accidentelle de données personnelles (PII) violant le RGPD.
* **Option 2 : Meta Graph API & Pages Publiques Institutionnelles (Retenue pour le Backlog)** :
  - Ciblage exclusif des pages publiques d'organismes vérifiés (Communes luxembourgeoises, CGDIS, Office du Tourisme, salles de spectacle).
  - Utilisation des endpoints d'événements et de posts factuels via tokens développeur légitimes.
  - Application stricte du sanitizer Zero-PII et du mode Factual-Only (titres $\le 140$ car., dates, lieux, sans commentaires d'utilisateurs).

### B. Marché Immobilier
* Au-delà des données notariales de l'Observatoire de l'Habitat et du STATEC déjà intégrées dans `gold_housing` :
  - Intégration des données ouvertes de valeurs foncières frontalières (DVF France pour la Lorraine / Moselle, portails cadastraux ouverts).
  - Normalisation des indicateurs de prix médians au m² par commune et canton.

### C. Séries Historiques Multi-Annuelles
* Priorité à l'ingestion d'archives officielles (Open-Meteo Historical, ENTSO-E pour les cours de l'électricité depuis 2020, séries STATEC mensuelles depuis 1990).
* Stockage sous forme de partitions Parquet (ZSTD) préservant l'ultra-légèreté du dépôt.

---

## 3. Décision
1. **Inscrire les connecteurs réseaux sociaux dans `docs/BACKLOG.md`** selon l'approche "API Partenaires / Pages Publiques Uniquement" sans scraping non officiel.
2. **Maintenir la discipline d'ingénierie stricte** :
   - Chaque nouvelle source doit être ajoutée de façon déclarative via `config/sources.toml`.
   - Zéro abstraction Python complexe : le budget de code reste plafonné à moins de 1 500 lignes.
   - Les 7 bibliothèques runtime restent verrouillées.

---

## 4. Conséquences
- **Positives** : Élargissement continu de la couverture fonctionnelle sans risque juridique, conservation du Trust Score 100% auditable.
- **Limites acceptées** : Pas de scraping opaque non consenti d'utilisateurs privés.
