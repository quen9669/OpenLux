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
- **Schéma exact** : `station_id`, `station_name`, `observed_at_utc`, `temperature`, `humidity`, `pressure_hpa`, `wind_speed_kmh`, `precipitation_mm`, `weather_condition`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Mesures concentrées sur les stations officielles principales (Findel, etc.) ; microclimats locaux non captés.

### 2.2 `gold_traffic_events`
- **Domaine** : `traffic_cita`
- **Grain** : 1 ligne par événement de circulation routière (accident, bouchon, chantier).
- **Fichier** : `data/gold/gold_traffic_events.parquet` (ZSTD)
- **Sources** : `traffic_cita_datex2` (CITA DATEX II XML via `cita_datex2`).
- **Schéma exact** : `event_id`, `road_name`, `situation_type`, `observed_at_utc`, `lat`, `lon`, `commune_lau`, `traffic_comment`, `source_id`.
- **Limites connues** : Couvre exclusivement le réseau autoroutier national exploité par CITA (A1, A3, A4, A6, A7, A13, B40).

### 2.3 `gold_holidays`
- **Domaine** : `holidays_vacations`
- **Grain** : 1 ligne par date de jour férié officiel ou vacances scolaires.
- **Fichier** : `data/gold/gold_holidays.parquet` (ZSTD)
- **Sources** : `holidays_lu` (`data.public.lu`).
- **Schéma exact** : `holiday_date`, `observed_at_utc`, `holiday_name_fr`, `holiday_name_de`, `holiday_name_lb`, `is_legal_holiday`, `is_school_vacation`, `commune_lau`, `lat`, `lon`, `source_id`.
- **Limites connues** : Valable pour le calendrier légal officiel du Grand-Duché de Luxembourg.

### 2.4 `gold_air_quality` (Vague 3A)
- **Domaine** : `air_quality`
- **Grain** : 1 ligne par station, par polluant mesuré et par relevé.
- **Fichier** : `data/gold/gold_air_quality.parquet` (ZSTD)
- **Sources** : `air_quality_lu` (Administration de l'Environnement, backup Open-Meteo Air Quality).
- **Schéma exact** : `station_id`, `station_name`, `observed_at_utc`, `pollutant`, `pollutant_value`, `unit`, `aqi_index`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Données issues des stations automatiques avant validation définitive annuelle.

### 2.5 `gold_water_levels` (Vague 3A)
- **Domaine** : `water_levels`
- **Grain** : 1 ligne par station hydrologique et par relevé.
- **Fichier** : `data/gold/gold_water_levels.parquet` (ZSTD)
- **Sources** : `water_levels_lu` (Administration de la Gestion de l'Eau).
- **Schéma exact** : `station_id`, `station_name`, `river_name`, `observed_at_utc`, `water_level_cm`, `discharge_m3s`, `alert_level`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Mesures automatiques en direct soumises aux crues subites.

### 2.6 `gold_fuel_prices` (Vague 3A)
- **Domaine** : `economy_fuel`
- **Grain** : 1 ligne par type de carburant routier et par mise à jour officielle.
- **Fichier** : `data/gold/gold_fuel_prices.parquet` (ZSTD)
- **Sources** : `fuel_prices_lu` (Ministère de l'Économie).
- **Schéma exact** : `fuel_type`, `observed_at_utc`, `price_eur_per_litre`, `price_change_eur`, `source_id`.
- **Limites connues** : Prix maxima légaux autorisés au Luxembourg ; les stations peuvent appliquer des rabais.

### 2.7 `gold_statec_inflation` (Vague 3A)
- **Domaine** : `economy_fuel`
- **Grain** : 1 ligne par mois de référence.
- **Fichier** : `data/gold/gold_statec_inflation.parquet` (ZSTD)
- **Sources** : `statec_inflation` (STATEC, backup Eurostat).
- **Schéma exact** : `reference_month`, `observed_at_utc`, `ipcn_index`, `inflation_annual_rate`, `wage_index_quote`, `source_id`.
- **Limites connues** : Publication mensuelle officielle le premier mercredi suivant la fin du mois.

### 2.8 `gold_electricity_spot` (Vague 3A)
- **Domaine** : `energy_climate`
- **Grain** : 1 ligne par heure d'échéance Day-Ahead.
- **Fichier** : `data/gold/gold_electricity_spot.parquet` (ZSTD)
- **Sources** : `electricity_spot_delu` (ENTSO-E / EPEX SPOT DE-LU).
- **Schéma exact** : `observed_at_utc`, `price_eur_per_mwh`, `bidding_zone`, `source_id`.
- **Limites connues** : Prix spot de gros conjointe Allemagne-Luxembourg hors réseau et taxes.

### 2.9 `gold_radioactivity` (Vague 3A)
- **Domaine** : `energy_climate`
- **Grain** : 1 ligne par sonde de télémesure nationale et par relevé.
- **Fichier** : `data/gold/gold_radioactivity.parquet` (ZSTD)
- **Sources** : `radioactivity_lu` (Division de la Radioprotection).
- **Schéma exact** : `station_id`, `station_name`, `observed_at_utc`, `dose_rate_nsvh`, `radiological_status`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Mesure en nSv/h ; légères hausses naturelles lors des épisodes de pluie (radon).

### 2.10 `gold_bathing_water` (Vague 3A)
- **Domaine** : `energy_climate`
- **Grain** : 1 ligne par site officiel de baignade et par contrôle sanitaire.
- **Fichier** : `data/gold/gold_bathing_water.parquet` (ZSTD)
- **Sources** : `bathing_water_lu` (Administration de la Gestion de l'Eau).
- **Schéma exact** : `site_id`, `site_name`, `water_body`, `observed_at_utc`, `quality_class`, `cyanobacteria_bloom`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Prélèvements réalisés bimensuellement pendant la saison estivale (mai - septembre).

### 2.11 `gold_crossborder_traffic` (Vague 3B)
- **Domaine** : `crossborder_traffic`
- **Grain** : 1 ligne par événement ou corridor frontalier (A31, A64, E411, lignes TER/CFL).
- **Fichier** : `data/gold/gold_crossborder_traffic.parquet` (ZSTD)
- **Sources** : `traffic_fr_bisonfute`, `traffic_de_autobahn`, `traffic_be_trafiroutes`, `rail_crossborder`.
- **Schéma exact** : `event_id`, `corridor`, `transport_mode`, `observed_at_utc`, `delay_minutes`, `status`, `comment`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Temps de parcours et retards indicatifs fournis par les gestionnaires d'infrastructures voisins (DIR Est, Autobahn GmbH, SPW, SNCF).

### 2.12 `gold_public_transit` (Vague 3B)
- **Domaine** : `public_transit`
- **Grain** : 1 ligne par ligne de transport, réseau et état de service.
- **Fichier** : `data/gold/gold_public_transit.parquet` (ZSTD)
- **Sources** : `transit_mobiliteit`, `transit_avl_rt`.
- **Schéma exact** : `line_id`, `network`, `observed_at_utc`, `delay_seconds`, `disruption_level`, `message`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Couvre le réseau national Mobiliteit.lu (CFL, Tram, RGTR) et les autobus municipaux AVL.

### 2.13 `gold_mobility_parkings` (Vague 3B)
- **Domaine** : `mobility_parkings`
- **Grain** : 1 ligne par équipement de mobilité (station Vel'oH, parking public, P+R, borne Chargy).
- **Fichier** : `data/gold/gold_mobility_parkings.parquet` (ZSTD)
- **Sources** : `veloh_stations`, `parkings_vdl`, `chargy_stations`.
- **Schéma exact** : `facility_id`, `facility_type`, `facility_name`, `observed_at_utc`, `available_capacity`, `total_capacity`, `occupancy_rate`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Taux d'occupation en temps réel ; ne comprend pas le stationnement payant résidentiel en voirie.

### 2.14 `gold_aviation_noise` (Vague 3B)
- **Domaine** : `aviation_noise`
- **Grain** : 1 ligne par mouvement aérien Findel (vols en approche/décollage) ou contour de bruit réglementaire.
- **Fichier** : `data/gold/gold_aviation_noise.parquet` (ZSTD)
- **Sources** : `aviation_opensky_lu`, `noise_zones_lu`.
- **Schéma exact** : `record_id`, `record_type`, `callsign_or_zone`, `observed_at_utc`, `altitude_m_or_dba`, `status`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Vols ADS-B captés par OpenSky dans la bounding box Luxembourg ; courbes d'isophonie réglementaires révisées périodiquement.

### 2.15 `gold_roadworks` (Vague 3C)
- **Domaine** : `roadworks`
- **Grain** : 1 ligne par chantier ou perturbation programmée sur le réseau autoroutier et voiries communales VDL.
- **Fichier** : `data/gold/gold_roadworks.parquet` (ZSTD)
- **Sources** : `roadworks_cita`, `roadworks_vdl`.
- **Schéma exact** : `work_id`, `authority`, `road_name`, `start_date`, `end_date`, `impact_level`, `title`, `observed_at_utc`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Couvre les autoroutes CITA et le réseau municipal de la Ville de Luxembourg ; calendrier sous réserve d'aléas météo.

### 2.16 `gold_housing` (Vague 3C)
- **Domaine** : `housing_construction`
- **Grain** : 1 ligne par commune, type de bien, période de référence et indicateur (prix m² ou autorisations de bâtir).
- **Fichier** : `data/gold/gold_housing.parquet` (ZSTD)
- **Sources** : `housing_observatoire`, `housing_statec`.
- **Schéma exact** : `record_id`, `record_type`, `property_type`, `reference_period`, `metric_value`, `count_value`, `observed_at_utc`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Prix médians et transactions de l'Observatoire de l'Habitat basés sur les actes notariés enregistrés ; autorisations de bâtir trimestrielles STATEC.

### 2.17 `gold_daily_life` (Vague 3C)
- **Domaine** : `daily_life_sport`
- **Grain** : 1 ligne par aménagement ou équipement du quotidien (pistes cyclables nationales, ouvertures dominicales VDL, parcs de recyclage).
- **Fichier** : `data/gold/gold_daily_life.parquet` (ZSTD)
- **Sources** : `bike_lanes_lu`, `open_sundays_vdl`, `recycling_centers`.
- **Schéma exact** : `item_id`, `category`, `name`, `status_or_schedule`, `details`, `observed_at_utc`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Pistes cyclables gérées par les Ponts & Chaussées ; horaires des centres de recyclage et commerces sous réserve d'actualisation municipale.

### 2.18 `gold_culture_events` (Vague 3D)
- **Domaine** : `concerts_culture`, `local_events_markets`, `major_venues`
- **Grain** : 1 ligne par manifestation culturelle ou sortie unique (dédoublonnée par titre et date de début).
- **Fichier** : `data/gold/gold_culture_events.parquet` (ZSTD)
- **Sources** : `culture_echo_lu`, `culture_venues_jsonld`, `events_vdl`, `events_visitlu`, `venues_luxexpo`, `venues_stade_coque`.
- **Schéma exact** : `title`, `start_date`, `end_date`, `venue`, `category`, `source_url`, `commune_lau`, `canton`, `lat`, `lon`, `source_id`.
- **Limites connues** : Extraction factuelle stricte schema.org/Event sans reproduction de textes descriptifs sous droit d'auteur (`FACTUAL-ONLY`).

### 2.19 `gold_strikes_disruptions` (Vague 3D)
- **Domaine** : `strikes_disruptions`
- **Grain** : 1 ligne par préavis ou alerte de grève / manifestation sociale.
- **Fichier** : `data/gold/gold_strikes_disruptions.parquet` (ZSTD)
- **Sources** : `strikes_rss_lu`.
- **Schéma exact** : `strike_id`, `title`, `published_at_utc`, `sector`, `source_url`, `commune_lau`, `canton`, `lat`, `lon`, `source_id`.
- **Limites connues** : Filtrage algorithmique pur sur flux d'actualités via mots-clés grève/streik ; niveau d'impact effectif sujet à l'évolution des négociations.

### 2.20 `gold_health_alerts` (Vague 3D)
- **Domaine** : `health_pollen_alerts`
- **Grain** : 1 ligne par relevé d'allergène, borne de défibrillation d'urgence ou message LU-Alert.
- **Fichier** : `data/gold/gold_health_alerts.parquet` (ZSTD)
- **Sources** : `pollen_lu`, `aed_defib_lu`, `lu_alert`.
- **Schéma exact** : `record_id`, `record_type`, `headline_or_name`, `status_or_severity`, `metric_value`, `observed_at_utc`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Concentrations polliniques issues de la station aérobiologique centrale ; messages LU-Alert actifs uniquement en situation d'urgence ou test officiel.

### 2.21 `gold_civic_life` (Vague 3D)
- **Domaine** : `civic_life`
- **Grain** : 1 ligne par pétition publique citoyenne ou statistique mensuelle communale de l'emploi ADEM.
- **Fichier** : `data/gold/gold_civic_life.parquet` (ZSTD)
- **Sources** : `petitions_chd`, `unemployment_adem`.
- **Schéma exact** : `record_id`, `record_type`, `title_or_indicator`, `signatures_count`, `rate_value`, `status`, `observed_at_utc`, `lat`, `lon`, `commune_lau`, `canton`, `source_id`.
- **Limites connues** : Pétitions issues du portail de la Chambre des Députés ; statistiques de l'emploi publiées mensuellement par l'ADEM.

---

## 3. Vue Consolidée Multimodale

### 3.1 `gold_luxembourg_daily_context` (Consolidation globale Phase 3)
- **Grain** : `context_date × commune_lau` (100 communes luxembourgeoises).
- **Fichier** : `data/gold/gold_luxembourg_daily_context.parquet` (ZSTD)
- **Sources consolidées** : Jointure des 8 signaux quotidiens (`gold_weather_observations`, `gold_air_quality`, `gold_holidays`, `gold_traffic_events`, `gold_crossborder_traffic`, `gold_roadworks`, `gold_strikes_disruptions`, `gold_water_levels`, `gold_culture_events`).
- **Schéma exact** : `context_date`, `commune_lau`, `commune_name`, `canton`, `lat`, `lon`, `avg_temperature_c`, `total_precipitation_mm`, `max_wind_speed_kmh`, `max_aqi_index`, `is_legal_holiday`, `is_school_vacation`, `traffic_events_count`, `active_roadworks_count`, `strikes_count`, `max_water_alert_status`, `major_events_count`, `source_id`.
- **Usage IA privilégié** : Fournit le contexte spatio-temporel complet d'une journée au Luxembourg pour les agents conversationnels, assistants de vie locale et modèles d'analyse multimodaux.
