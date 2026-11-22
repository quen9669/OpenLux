-- Gold: Data Mart final des chantiers autoroutiers et voiries communales
SELECT
    work_id,
    authority,
    road_name,
    start_date,
    end_date,
    impact_level,
    title,
    observed_at_utc,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_roadworks') }}
ORDER BY observed_at_utc DESC NULLS LAST, work_id
