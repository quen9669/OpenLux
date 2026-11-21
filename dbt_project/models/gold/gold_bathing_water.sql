-- Gold: Data Mart final de la qualité des eaux de baignade au Luxembourg
SELECT
    site_id,
    site_name,
    water_body,
    observed_at_utc,
    quality_class,
    cyanobacteria_bloom,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_bathing_water') }}
