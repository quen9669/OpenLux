-- Silver: Nettoyage et enrichissement des stations vélos en libre-service Vel'oH
WITH raw_veloh AS (
    SELECT * FROM {{ ref('stg_veloh_stations') }}
),
ref_stations AS (
    SELECT * FROM {{ ref('ref_veloh_stations') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    v.station_id,
    v.station_number,
    CASE
        WHEN (v.station_name LIKE 'Veloh %' OR v.station_name IS NULL OR v.station_name = '') AND s.station_name IS NOT NULL
            THEN s.station_name
        ELSE COALESCE(v.station_name, v.station_id)
    END AS station_name,
    CASE
        WHEN (v.address IS NULL OR v.address = '') AND s.address IS NOT NULL
            THEN s.address
        ELSE COALESCE(v.address, '')
    END AS address,
    COALESCE(
        TRY_CAST(v.raw_observed_at AS TIMESTAMP),
        TRY_STRPTIME(
            REGEXP_EXTRACT(v.raw_observed_at, '([0-9]{1,2} [A-Za-z]{3} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2})'),
            '%d %b %Y %H:%M:%S'
        ),
        CURRENT_TIMESTAMP
    ) AS observed_at_utc,
    v.available_bikes,
    v.available_electrical_bikes,
    v.available_mechanical_bikes,
    v.available_stands,
    v.broken_stands AS broken_or_disabled_stands,
    COALESCE(NULLIF(v.total_capacity, 0), s.nominal_capacity, 15) AS total_capacity,
    CASE
        WHEN COALESCE(NULLIF(v.total_capacity, 0), s.nominal_capacity, 15) > 0 THEN
            ROUND(v.available_bikes * 100.0 / COALESCE(NULLIF(v.total_capacity, 0), s.nominal_capacity, 15), 1)
        ELSE NULL
    END AS occupancy_rate,
    v.status,
    v.is_renting,
    v.is_connected,
    v.is_installed,
    v.has_banking,
    v.is_bonus,
    0.00 AS hourly_rate_eur,
    'Gratuit < 30min avec abonnement Vel''oH' AS tariff_details,
    v.opening_hours,
    COALESCE(v.lat, s.lat, c.lat) AS lat,
    COALESCE(v.lon, s.lon, c.lon) AS lon,
    COALESCE(c.code_lau, v.raw_commune_name) AS commune_lau,
    c.canton,
    v.source_id
FROM raw_veloh v
LEFT JOIN ref_stations s
    ON v.station_number = s.station_number
    OR v.station_id = s.station_id
LEFT JOIN ref_communes c
    ON LOWER(COALESCE(s.commune_name, v.raw_commune_name)) = LOWER(c.commune_name)
    OR LOWER(COALESCE(s.commune_name, v.raw_commune_name)) = LOWER(c.commune_name_lb)
    OR COALESCE(s.commune_name, v.raw_commune_name) = c.code_lau
