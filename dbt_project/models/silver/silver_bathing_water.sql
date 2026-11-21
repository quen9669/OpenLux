-- Silver: Nettoyage, typage strict et enrichissement géographique des eaux de baignade
WITH base AS (
    SELECT * FROM {{ ref('stg_bathing_water') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    b.site_id,
    b.site_name,
    b.water_body,
    TRY_CAST(b.raw_inspection_date AS TIMESTAMP) AS observed_at_utc,
    b.quality_class,
    b.cyanobacteria_bloom,
    COALESCE(b.lat, c.lat) AS lat,
    COALESCE(b.lon, c.lon) AS lon,
    COALESCE(c.code_lau, b.raw_commune_name) AS commune_lau,
    c.canton,
    b.source_id
FROM base b
LEFT JOIN ref_communes c
    ON LOWER(b.raw_commune_name) = LOWER(c.commune_name)
    OR LOWER(b.raw_commune_name) = LOWER(c.commune_name_lb)
    OR b.raw_commune_name = c.code_lau
