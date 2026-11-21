-- Silver: Consolidation, dédoublonnage et géolocalisation des événements culturels et manifestations
WITH all_events AS (
    SELECT title, raw_start_date, raw_end_date, venue, raw_city, category, source_url, source_id
    FROM {{ ref('stg_culture_echo_lu') }}
    UNION ALL
    SELECT title, raw_start_date, raw_end_date, venue, raw_city, category, source_url, source_id
    FROM {{ ref('stg_culture_venues') }}
    UNION ALL
    SELECT title, raw_start_date, raw_end_date, venue, raw_city, category, source_url, source_id
    FROM {{ ref('stg_events_vdl') }}
    UNION ALL
    SELECT title, raw_start_date, raw_end_date, venue, raw_city, category, source_url, source_id
    FROM {{ ref('stg_events_visitlu') }}
    UNION ALL
    SELECT title, raw_start_date, raw_end_date, venue, raw_city, category, source_url, source_id
    FROM {{ ref('stg_venues_luxexpo') }}
    UNION ALL
    SELECT title, raw_start_date, raw_end_date, venue, raw_city, category, source_url, source_id
    FROM {{ ref('stg_venues_stade_coque') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
),
deduped_events AS (
    SELECT
        title,
        TRY_CAST(raw_start_date AS TIMESTAMP) AS start_date,
        TRY_CAST(raw_end_date AS TIMESTAMP) AS end_date,
        venue,
        raw_city,
        category,
        source_url,
        source_id,
        ROW_NUMBER() OVER (
            PARTITION BY LOWER(TRIM(title)), TRY_CAST(raw_start_date AS DATE)
            ORDER BY source_id
        ) AS rn
    FROM all_events
)
SELECT
    d.title,
    d.start_date,
    d.end_date,
    d.venue,
    d.category,
    d.source_url,
    COALESCE(c.code_lau, d.raw_city) AS commune_lau,
    c.canton,
    c.lat,
    c.lon,
    d.source_id
FROM deduped_events d
LEFT JOIN ref_communes c
    ON LOWER(d.raw_city) = LOWER(c.commune_name)
    OR LOWER(d.raw_city) = LOWER(c.commune_name_lb)
    OR d.raw_city = c.code_lau
WHERE d.rn = 1
