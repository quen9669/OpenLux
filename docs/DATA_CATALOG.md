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

## 2. Data Marts Actifs

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

### 2.4 `gold_air_quality` (Vague 3A)
- **Domaine** : `air_quality`
- **Grain** : 1 ligne par station, par polluant mesuré et par relevé.
- **Fichier** : `data/gold/gold_air_quality.parquet` (ZSTD)
- **Sources** : `air_quality_lu` (Administration de l'Environnement, backup Open-Meteo Air Quality).
- **Schéma exact** :
  - `station_id` (`VARCHAR`), `station_name` (`VARCHAR`)
  - `observed_at_utc` (`TIMESTAMP`)
  - `pollutant` (`VARCHAR`), `pollutant_value` (`DOUBLE`), `unit` (`VARCHAR`), `aqi_index` (`VARCHAR`)
  - `lat` (`DOUBLE`), `lon` (`DOUBLE`), `commune_lau` (`VARCHAR`), `canton` (`VARCHAR`), `source_id` (`VARCHAR`)
- **Limites connues** : Données issues des stations automatiques avant validation définitive annuelle.

### 2.5 `gold_water_levels` (Vague 3A)
- **Domaine** : `water_levels`
- **Grain** : 1 ligne par station hydrologique et par relevé.
- **Fichier** : `data/gold/gold_water_levels.parquet` (ZSTD)
- **Sources** : `water_levels_lu` (Administration de la Gestion de l'Eau).
- **Schéma exact** :
  - `station_id` (`VARCHAR`), `station_name` (`VARCHAR`), `river_name` (`VARCHAR`)
  - `observed_at_utc` (`TIMESTAMP`)
  - `water_level_cm` (`DOUBLE`), `discharge_m3s` (`DOUBLE`), `alert_level` (`VARCHAR`)
  - `lat` (`DOUBLE`), `lon` (`DOUBLE`), `commune_lau` (`VARCHAR`), `canton` (`VARCHAR`), `source_id` (`VARCHAR`)
- **Limites connues** : Mesures automatiques en direct soumises aux crues subites.

### 2.6 `gold_fuel_prices` (Vague 3A)
- **Domaine** : `economy_fuel`
- **Grain** : 1 ligne par type de carburant routier et par mise à jour officielle.
- **Fichier** : `data/gold/gold_fuel_prices.parquet` (ZSTD)
- **Sources** : `fuel_prices_lu` (Ministère de l'Économie).
- **Schéma exact** :
  - `fuel_type` (`VARCHAR`)
  - `observed_at_utc` (`TIMESTAMP`)
  - `price_eur_per_litre` (`DOUBLE`), `price_change_eur` (`DOUBLE`)
  - `source_id` (`VARCHAR`)
- **Limites connues** : Prix maxima légaux autorisés au Luxembourg ; les stations peuvent appliquer des rabais.

### 2.7 `gold_statec_inflation` (Vague 3A)
- **Domaine** : `economy_fuel`
- **Grain** : 1 ligne par mois de référence.
- **Fichier** : `data/gold/gold_statec_inflation.parquet` (ZSTD)
- **Sources** : `statec_inflation` (STATEC, backup Eurostat).
- **Schéma exact** :
  - `reference_month` (`VARCHAR`)
  - `observed_at_utc` (`TIMESTAMP`)
  - `ipcn_index` (`DOUBLE`), `inflation_annual_rate` (`DOUBLE`), `wage_index_quote` (`DOUBLE`)
  - `source_id` (`VARCHAR`)
- **Limites connues** : Publication mensuelle officielle le premier mercredi suivant la fin du mois.

### 2.8 `gold_electricity_spot` (Vague 3A)
- **Domaine** : `energy_climate`
- **Grain** : 1 ligne par heure d'échéance Day-Ahead.
- **Fichier** : `data/gold/gold_electricity_spot.parquet` (ZSTD)
- **Sources** : `electricity_spot_delu` (ENTSO-E / EPEX SPOT DE-LU).
- **Schéma exact** :
  - `observed_at_utc` (`TIMESTAMP`)
  - `price_eur_per_mwh` (`DOUBLE`), `bidding_zone` (`VARCHAR`)
  - `source_id` (`VARCHAR`)
- **Limites connues** : Prix spot de gros conjointe Allemagne-Luxembourg hors réseau et taxes.

### 2.9 `gold_radioactivity` (Vague 3A)
- **Domaine** : `energy_climate`
- **Grain** : 1 ligne par sonde de télémesure nationale et par relevé.
- **Fichier** : `data/gold/gold_radioactivity.parquet` (ZSTD)
- **Sources** : `radioactivity_lu` (Division de la Radioprotection).
- **Schéma exact** :
  - `station_id` (`VARCHAR`), `station_name` (`VARCHAR`)
  - `observed_at_utc` (`TIMESTAMP`)
  - `dose_rate_nsvh` (`DOUBLE`), `radiological_status` (`VARCHAR`)
  - `lat` (`DOUBLE`), `lon` (`DOUBLE`), `commune_lau` (`VARCHAR`), `canton` (`VARCHAR`), `source_id` (`VARCHAR`)
- **Limites connues** : Mesure en nSv/h ; légères hausses naturelles lors des épisodes de pluie (radon).

### 2.10 `gold_bathing_water` (Vague 3A)
- **Domaine** : `energy_climate`
- **Grain** : 1 ligne par site officiel de baignade et par contrôle sanitaire.
- **Fichier** : `data/gold/gold_bathing_water.parquet` (ZSTD)
- **Sources** : `bathing_water_lu` (Administration de la Gestion de l'Eau).
- **Schéma exact** :
  - `site_id` (`VARCHAR`), `site_name` (`VARCHAR`), `water_body` (`VARCHAR`)
  - `observed_at_utc` (`TIMESTAMP`)
  - `quality_class` (`VARCHAR`), `cyanobacteria_bloom` (`VARCHAR`)
  - `lat` (`DOUBLE`), `lon` (`DOUBLE`), `commune_lau` (`VARCHAR`), `canton` (`VARCHAR`), `source_id` (`VARCHAR`)
- **Limites connues** : Prélèvements réalisés bimensuellement pendant la saison estivale (mai - septembre).

---

## 3. Vue Consolidée Multimodale

### 3.1 `gold_luxembourg_daily_context` (Consolidation finale Phase 3)
- **Grain** : `date × commune_lau` (100 communes luxembourgeoises).
- **Contenu** : Agrégation quotidienne des 8 signaux critiques (météo, qualité de l'air, état du trafic autoroutier/frontalier, chantiers, grèves, crues, jours fériés et événements majeurs).
- **Usage IA privilégié** : Fournit le contexte complet d'une journée au Luxembourg pour les agents conversationnels et modèles prédictifs.
