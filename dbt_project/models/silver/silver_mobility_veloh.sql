-- Silver: Nettoyage et enrichissement des stations vélos en libre-service Vel'oH
WITH raw_veloh AS (
    SELECT * FROM {{ ref('stg_veloh_stations') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    v.station_id,
    v.station_name,
    COALESCE(
        TRY_CAST(v.raw_observed_at AS TIMESTAMP),
        TRY_STRPTIME(
            REGEXP_EXTRACT(v.raw_observed_at, '([0-9]{1,2} [A-Za-z]{3} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2})'),
            '%d %b %Y %H:%M:%S'
        ),
        CURRENT_TIMESTAMP
    ) AS observed_at_utc,
    v.available_bikes,
    v.available_stands,
    v.broken_stands AS broken_or_disabled_stands,
    v.total_capacity,
    CASE
        WHEN v.total_capacity > 0 THEN ROUND(v.available_bikes * 100.0 / v.total_capacity, 1)
        ELSE NULL
    END AS occupancy_rate,
    v.is_installed,
    v.is_renting,
    0.00 AS hourly_rate_eur,
    'Gratuit < 30min avec abonnement Vel''oH' AS tariff_details,
    v.opening_hours,
    COALESCE(v.lat, c.lat) AS lat,
    COALESCE(v.lon, c.lon) AS lon,
    COALESCE(c.code_lau, v.raw_commune_name) AS commune_lau,
    c.canton,
    v.source_id
FROM raw_veloh v
LEFT JOIN ref_communes c
    ON LOWER(v.raw_commune_name) = LOWER(c.commune_name)
    OR LOWER(v.raw_commune_name) = LOWER(c.commune_name_lb)
    OR v.raw_commune_name = c.code_lau
