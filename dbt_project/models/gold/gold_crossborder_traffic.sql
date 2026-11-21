-- Gold: Data Mart final du trafic frontalier multimodal (axes autoroutiers et trains)
SELECT
    event_id,
    corridor,
    transport_mode,
    observed_at_utc,
    delay_minutes,
    status,
    comment,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_crossborder_traffic') }}
