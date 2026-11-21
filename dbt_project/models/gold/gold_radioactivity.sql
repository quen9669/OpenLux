-- Gold: Data Mart final de la surveillance radiologique nationale
SELECT
    station_id,
    station_name,
    observed_at_utc,
    dose_rate_nsvh,
    radiological_status,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_radioactivity') }}
