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
- **Sources** : `meteo_lux_obs` (MeteoLux, backup Open-Meteo).
- **Champs principaux** : `station_name`, `temperature_c`, `humidity_pct`, `precipitation_mm`, `wind_speed_kmh`.
- **Limites connues** : Mesures concentrées sur les stations officielles principales (Findel, etc.) ; microclimats locaux non captés.

### 2.2 `gold_traffic_events`
- **Domaine** : `traffic_cita`
- **Grain** : 1 ligne par événement de circulation routière (accident, bouchon, fermeture).
- **Sources** : `traffic_cita_datex2` (CITA DATEX II XML).
- **Champs principaux** : `event_id`, `road_name`, `direction`, `event_type`, `delay_minutes`, `latitude`, `longitude`.
- **Limites connues** : Couvre exclusivement le réseau autoroutier national exploité par CITA (A1, A3, A4, A6, A7, A13, B40).

### 2.3 `gold_holidays_calendar`
- **Domaine** : `holidays_vacations`
- **Grain** : 1 ligne par jour férié officiel ou période de vacances scolaires.
- **Sources** : `holidays_lu` (`data.public.lu`).
- **Champs principaux** : `date`, `name_fr`, `name_de`, `name_lb`, `name_en`, `is_official_holiday`, `is_school_vacation`.
- **Limites connues** : Valable pour le calendrier légal du Grand-Duché de Luxembourg.

---

## 3. Vue Consolidée Multimodale (Phase 3)

### 3.1 `gold_luxembourg_daily_context`
- **Grain** : `date × commune_lau` (100 communes luxembourgeoises).
- **Contenu** : Agrégation quotidienne des 8 signaux critiques : météo moyenne/extrêmes, indice qualité de l'air, état du trafic autoroutier, chantiers actifs, préavis de grèves, vigilances crues/météo, jours fériés et événements d'envergure.
- **Usage IA privilégié** : Fournit le contexte complet d'une journée au Luxembourg pour les agents conversationnels et modèles prédictifs.
