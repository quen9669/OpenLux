-- Silver: Nettoyage et enrichissement des bornes de recharge électrique Chargy
WITH raw_chargy AS (
    SELECT * FROM {{ ref('stg_chargy_stations') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    ch.station_id,
    ch.station_name,
    ch.network_operator,
    COALESCE(
        TRY_CAST(ch.raw_observed_at AS TIMESTAMP),
        TRY_STRPTIME(
            REGEXP_EXTRACT(ch.raw_observed_at, '([0-9]{1,2} [A-Za-z]{3} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2})'),
            '%d %b %Y %H:%M:%S'
        ),
        '2026-11-22 14:00:00'::TIMESTAMP
    ) AS observed_at_utc,
    ch.available_charging_points,
    ch.total_charging_points,
    GREATEST(ch.total_charging_points - ch.available_charging_points, 0) AS occupied_charging_points,
    CASE
        WHEN ch.total_charging_points > 0 THEN ROUND((ch.total_charging_points - ch.available_charging_points) * 100.0 / ch.total_charging_points, 1)
        ELSE NULL
    END AS occupancy_rate,
    22.0 AS power_kw,
    'Type 2' AS connector_types,
    '0.35 €/kWh AC 22kW' AS tariff_details,
    ch.opening_hours,
    COALESCE(ch.lat, c.lat) AS lat,
    COALESCE(ch.lon, c.lon) AS lon,
    COALESCE(c.code_lau, ch.raw_commune_name) AS commune_lau,
    c.canton,
    ch.source_id
FROM raw_chargy ch
LEFT JOIN ref_communes c
    ON LOWER(ch.raw_commune_name) = LOWER(c.commune_name)
    OR LOWER(ch.raw_commune_name) = LOWER(c.commune_name_lb)
    OR ch.raw_commune_name = c.code_lau
