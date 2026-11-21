-- Silver: Nettoyage, typage strict et enrichissement géographique de la qualité de l'air
WITH base AS (
    SELECT * FROM {{ ref('stg_air_quality') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    b.station_id,
    b.station_name,
    TRY_CAST(b.raw_observed_at AS TIMESTAMP) AS observed_at_utc,
    b.pollutant,
    b.pollutant_value,
    b.unit,
    b.aqi_index,
    COALESCE(b.lat, c.lat) AS lat,
    COALESCE(b.lon, c.lon) AS lon,
    COALESCE(c.code_lau, b.commune_lau) AS commune_lau,
    c.canton,
    b.source_id
FROM base b
LEFT JOIN ref_communes c
    ON LOWER(b.commune_lau) = LOWER(c.commune_name)
    OR LOWER(b.commune_lau) = LOWER(c.commune_name_lb)
    OR b.commune_lau = c.code_lau
