-- Silver: Nettoyage, typage strict et enrichissement géographique des observations météo
WITH base AS (
    SELECT * FROM {{ ref('stg_meteo_lux_obs') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
),
joined AS (
    SELECT
        b.station_id,
        b.station_name,
        TRY_CAST(b.raw_timestamp AS TIMESTAMP) AS observed_at_utc,
        b.temperature,
        b.humidity,
        b.pressure_hpa,
        b.wind_speed_kmh,
        b.precipitation_mm,
        b.weather_condition,
        COALESCE(b.lat, c.lat) AS lat,
        COALESCE(b.lon, c.lon) AS lon,
        COALESCE(c.code_lau, CASE WHEN LOWER(b.commune_lau) LIKE '%kaerjeng%' THEN 'LU0110' ELSE b.commune_lau END) AS commune_lau,
        COALESCE(c.canton, CASE WHEN LOWER(b.commune_lau) LIKE '%kaerjeng%' THEN 'Capellen' END) AS canton,
        b.source_id
    FROM base b
    LEFT JOIN ref_communes c
        ON LOWER(b.commune_lau) = LOWER(c.commune_name)
        OR LOWER(b.commune_lau) = LOWER(c.commune_name_lb)
        OR LOWER(REPLACE(b.commune_lau, 'ae', 'ä')) = LOWER(c.commune_name)
        OR b.commune_lau = c.code_lau
    WHERE b.station_id IS NOT NULL
      AND TRY_CAST(b.raw_timestamp AS TIMESTAMP) IS NOT NULL
)
SELECT * FROM joined
QUALIFY ROW_NUMBER() OVER (PARTITION BY station_id, observed_at_utc ORDER BY observed_at_utc DESC) = 1
