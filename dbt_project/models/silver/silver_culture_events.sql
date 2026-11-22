-- Silver: Consolidation, dédoublonnage et géolocalisation des événements culturels et manifestations
WITH all_events AS (
    SELECT title, status, raw_start_date, raw_end_date, observed_at_utc, start_time, venue, address, raw_city, category, price_eur, price_text, is_free, source_url, ticket_url, lat_echo, lon_echo, source_id
    FROM {{ ref('stg_culture_echo_lu') }}
    UNION ALL
    SELECT title, status, raw_start_date, raw_end_date, observed_at_utc, start_time, venue, address, raw_city, category, price_eur, price_text, is_free, source_url, ticket_url, lat_echo, lon_echo, source_id
    FROM {{ ref('stg_culture_venues') }}
    UNION ALL
    SELECT title, status, raw_start_date, raw_end_date, observed_at_utc, start_time, venue, address, raw_city, category, price_eur, price_text, is_free, source_url, ticket_url, lat_echo, lon_echo, source_id
    FROM {{ ref('stg_events_vdl') }}
    UNION ALL
    SELECT title, status, raw_start_date, raw_end_date, observed_at_utc, start_time, venue, address, raw_city, category, price_eur, price_text, is_free, source_url, ticket_url, lat_echo, lon_echo, source_id
    FROM {{ ref('stg_events_visitlu') }}
    UNION ALL
    SELECT title, status, raw_start_date, raw_end_date, observed_at_utc, start_time, venue, address, raw_city, category, price_eur, price_text, is_free, source_url, ticket_url, lat_echo, lon_echo, source_id
    FROM {{ ref('stg_venues_luxexpo') }}
    UNION ALL
    SELECT title, status, raw_start_date, raw_end_date, observed_at_utc, start_time, venue, address, raw_city, category, price_eur, price_text, is_free, source_url, ticket_url, lat_echo, lon_echo, source_id
    FROM {{ ref('stg_venues_stade_coque') }}
    UNION ALL
    SELECT
        r.event_name AS title,
        'Confirmé' AS status,
        STRFTIME(CURRENT_DATE, '%Y-%m-%d 08:00:00') AS raw_start_date,
        STRFTIME(CURRENT_DATE, '%Y-%m-%d 18:00:00') AS raw_end_date,
        CURRENT_TIMESTAMP AS observed_at_utc,
        '08:00' AS start_time,
        r.location_name AS venue,
        r.location_name || ', ' || r.commune_lau AS address,
        r.commune_lau AS raw_city,
        r.category,
        0.0 AS price_eur,
        'Entrée libre' AS price_text,
        true AS is_free,
        r.source_url,
        NULL::VARCHAR AS ticket_url,
        NULL::DOUBLE AS lat_echo,
        NULL::DOUBLE AS lon_echo,
        'ref_recurring_events' AS source_id
    FROM {{ ref('ref_recurring_events') }} r
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
),
deduped_events AS (
    SELECT
        title,
        status,
        TRY_CAST(raw_start_date AS TIMESTAMP) AS start_date,
        TRY_CAST(raw_end_date AS TIMESTAMP) AS end_date,
        observed_at_utc,
        start_time,
        venue,
        address,
        raw_city,
        category,
        price_eur,
        price_text,
        is_free,
        source_url,
        ticket_url,
        lat_echo,
        lon_echo,
        source_id,
        ROW_NUMBER() OVER (
            PARTITION BY LOWER(TRIM(title)), TRY_CAST(raw_start_date AS TIMESTAMP)
            ORDER BY
                CASE WHEN source_id = 'culture_echo_lu' THEN 1 ELSE 2 END,
                CASE WHEN price_eur IS NOT NULL THEN 1 ELSE 2 END,
                CASE WHEN venue != 'Lieu non spécifié' THEN 1 ELSE 2 END
        ) AS rn
    FROM all_events
    WHERE title IS NOT NULL
)
SELECT
    d.title,
    d.status,
    d.start_date,
    COALESCE(d.end_date, d.start_date) AS end_date,
    d.observed_at_utc,
    COALESCE(d.start_time, STRFTIME(d.start_date, '%H:%M')) AS start_time,
    d.venue,
    COALESCE(d.address, d.venue || ', ' || COALESCE(c.commune_name, 'Luxembourg')) AS address,
    d.category,
    d.price_eur,
    d.price_text,
    d.is_free,
    d.source_url,
    d.ticket_url,
    COALESCE(c.code_lau, 'LU0000') AS commune_lau,
    COALESCE(c.canton, 'Luxembourg') AS canton,
    COALESCE(d.lat_echo, c.lat, 49.6117) AS lat,
    COALESCE(d.lon_echo, c.lon, 6.1319) AS lon,
    d.source_id
FROM deduped_events d
LEFT JOIN ref_communes c
    ON LOWER(TRIM(d.raw_city)) = LOWER(TRIM(c.commune_name))
    OR LOWER(TRIM(d.raw_city)) = LOWER(TRIM(c.code_lau))
WHERE d.rn = 1
