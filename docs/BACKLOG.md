# Backlog & Feuille de Route — OpenLux Hub

> Ce document centralise les évolutions futures et sources complémentaires identifiées pour enrichir continuellement la base de données unifiée du Luxembourg et de sa Grande Région.

---

## 1. Événements, Culture & Réseaux Sociaux

| ID / Thème | Source Cible | Description & Objectif | Modalité & Conformité |
| :--- | :--- | :--- | :--- |
| `social_vdl_events` | Facebook Pages VdL / Communes | Manifestations et fêtes communales publiées par les comptes officiels des 100 communes | Meta Graph API (Pages publiques vérifiées), Zero-PII, Factual-Only |
| `social_culture_insta` | Instagram Musées & Salles | Expositions et concerts annoncés par Mudam, Philharmonie, Rockhal, Kulturfabrik | Extraction métadonnées factuelles (dates, prix, lieux), sans commentaires |
| `events_cinemas_lu` | Kinepolis & Cinémathèque | Grille complète des séances et tarifs cinématographiques au Grand-Duché | Flux ouvert JSON / API partenaires cinéma |
| `nightlife_lu` | Événements nocturnes et clubs | Programmation des clubs et scènes musicales émergentes | Déclaration `config/sources.toml` + modèles SQL |

---

## 2. Marché Immobilier & Logement Élargi

| ID / Thème | Source Cible | Description & Objectif | Modalité & Conformité |
| :--- | :--- | :--- | :--- |
| `housing_dvf_frontiere` | Demandes de Valeurs Foncières (DVF France) | Prix réels des transactions immobilières dans le bassin de vie frontalier (Thionville, Longwy, Metz) | Open Data officiel Etalab (licence ouverte), parcelles anonymisées |
| `housing_rent_indices` | Observatoire de l'Habitat | Séries trimestrielles des loyers annoncés au m² par commune et type de bien | Import CSV officiel dans `data/bronze/` |
| `cadastre_parcels` | Geoportail.lu | Découpage parcellaire et autorisations d'urbanisme | WFS / GeoJSON officiel |

---

## 3. Profondeur Historique des Séries Temporelles

| Domaine | Couverture Cible | Source & Format |
| :--- | :--- | :--- |
| **Électricité Spot** | Historique horaire complet 2020–2026 (zone DE-LU) | Archives ENTSO-E / SMARD (Parquet partitionné) |
| **Météorologie** | Données climatiques quotidiennes sur 20 ans (2005–2025) | Archives Open-Meteo Historical / MeteoLux |
| **Économie & Inflation** | Séries mensuelles de l'indice des prix à la consommation depuis 1990 | Archives statistiques STATEC (Tableaux Excel / CSV ouverts) |
| **Niveaux des Cours d'Eau** | Historique des crues majeures (Alzette, Sûre, Moselle) sur 10 ans | Archives Administration de la Gestion de l'Eau (AGE) |

---

## 4. Garde-Fous Techniques pour le Backlog
Toute implémentation future issue de ce backlog devra respecter les principes fondateurs d'OpenLux :
1. **Config-driven** : 1 flux = 1 bloc dans `config/sources.toml` + modèle dbt SQL.
2. **Budget de code strict** : Préservation du cœur Python $< 1\,500$ lignes.
3. **Zéro-PII & Factual-Only** : Filtrage automatique systématique de tout nom ou identifiant personnel.
4. **Pas de contournement de sécurité** : Respect absolu des CGU et des robots.txt.
