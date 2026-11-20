# Catalogue des Données OpenLux Hub

> Ce catalogue recense les tables analytiques de la couche **Gold** produites par OpenLux Hub, leurs schémas, leurs garanties de fraîcheur et leurs limites d'usage connues (`known_limitations`).

---

## 1. Vue d'Ensemble des Tables Gold

Toutes les tables Gold sont stockées au format Parquet compressé en `ZSTD` dans le répertoire `data/gold/`.
Chaque table comporte systématiquement les colonnes de traçabilité spatio-temporelle lorsque cela est applicable :
- `observed_at_utc` (`TIMESTAMP`) : Horodatage universel de la mesure.
- `commune_lau` (`VARCHAR`) : Code officiel LAU de la commune luxembourgeoise.
- `lat` (`DOUBLE`), `lon` (`DOUBLE`) : Coordonnées géographiques en WGS84 (EPSG:4326).
- `source_id` (`VARCHAR`) : Identifiant du flux d'origine.

---

## 2. Tables Initiales (Phases 1 et 2)

### 2.1 `gold_weather_observations`
- **Domaine** : `weather`
- **Grain** : 1 ligne par station météorologique et par relevé.
- **Fichier** : `data/gold/gold_weather_observations.parquet` (ZSTD)
- **Sources** : `meteo_lux_obs` (MeteoLux, backup Open-Meteo).
- **Schéma exact** :
  - `station_id` (`VARCHAR`), `station_name` (`VARCHAR`)
  - `observed_at_utc` (`TIMESTAMP`)
  - `temperature` (`DOUBLE`), `humidity` (`DOUBLE`), `pressure_hpa` (`DOUBLE`)
  - `wind_speed_kmh` (`DOUBLE`), `precipitation_mm` (`DOUBLE`), `weather_condition` (`VARCHAR`)
  - `lat` (`DOUBLE`), `lon` (`DOUBLE`), `commune_lau` (`VARCHAR`), `canton` (`VARCHAR`), `source_id` (`VARCHAR`)
- **Limites connues** : Mesures concentrées sur les stations officielles principales (Findel, etc.) ; microclimats locaux non captés.

### 2.2 `gold_traffic_events`
- **Domaine** : `traffic_cita`
- **Grain** : 1 ligne par événement de circulation routière (accident, bouchon, chantier).
- **Fichier** : `data/gold/gold_traffic_events.parquet` (ZSTD)
- **Sources** : `traffic_cita_datex2` (CITA DATEX II XML via `cita_datex2`).
- **Schéma exact** :
  - `event_id` (`VARCHAR`), `road_name` (`VARCHAR`), `situation_type` (`VARCHAR`)
  - `observed_at_utc` (`TIMESTAMP`)
  - `lat` (`DOUBLE`), `lon` (`DOUBLE`), `commune_lau` (`VARCHAR`), `traffic_comment` (`VARCHAR`), `source_id` (`VARCHAR`)
- **Limites connues** : Couvre exclusivement le réseau autoroutier national exploité par CITA (A1, A3, A4, A6, A7, A13, B40).

### 2.3 `gold_holidays`
- **Domaine** : `holidays_vacations`
- **Grain** : 1 ligne par date de jour férié officiel ou vacances scolaires.
- **Fichier** : `data/gold/gold_holidays.parquet` (ZSTD)
- **Sources** : `holidays_lu` (`data.public.lu`).
- **Schéma exact** :
  - `holiday_date` (`DATE`), `observed_at_utc` (`TIMESTAMP`)
  - `holiday_name_fr` (`VARCHAR`), `holiday_name_de` (`VARCHAR`), `holiday_name_lb` (`VARCHAR`)
  - `is_legal_holiday` (`BOOLEAN`), `is_school_vacation` (`BOOLEAN`)
  - `commune_lau` (`VARCHAR`), `lat` (`DOUBLE`), `lon` (`DOUBLE`), `source_id` (`VARCHAR`)
- **Limites connues** : Valable pour le calendrier légal officiel du Grand-Duché de Luxembourg.

---

## 3. Vue Consolidée Multimodale (Phase 3)

### 3.1 `gold_luxembourg_daily_context`
- **Grain** : `date × commune_lau` (100 communes luxembourgeoises).
- **Contenu** : Agrégation quotidienne des 8 signaux critiques : météo moyenne/extrêmes, indice qualité de l'air, état du trafic autoroutier, chantiers actifs, préavis de grèves, vigilances crues/météo, jours fériés et événements d'envergure.
- **Usage IA privilégié** : Fournit le contexte complet d'une journée au Luxembourg pour les agents conversationnels et modèles prédictifs.
