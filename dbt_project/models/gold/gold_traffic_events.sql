-- Gold: Data Mart final des événements et perturbations trafic autoroutiers CITA
SELECT
    event_id,
    road_name,
    situation_type,
    observed_at_utc,
    lat,
    lon,
    commune_lau,
    canton,
    traffic_comment,
    source_id
FROM {{ ref('silver_traffic_events') }}
