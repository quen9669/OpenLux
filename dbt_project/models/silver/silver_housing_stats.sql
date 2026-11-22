-- Silver: Consolidation des statistiques officielles du logement (Observatoire de l'Habitat & STATEC)
WITH obs_raw AS (
    SELECT *
    FROM {{ ref('stg_housing_observatoire') }}
    WHERE raw_commune_name != 'Moyenne nationale'
),
obs AS (
    SELECT
        raw_commune_name || '_' || property_type || '_' || reference_period AS record_id,
        'STATISTIC_OBSERVATOIRE' AS record_type,
        property_type,
        'EXISTING' AS market_segment,
        reference_period,
        price_eur_m2,
        transactions_count AS units_count,
        NULL::INTEGER AS permits_count,
        'Statistique de prix médian observatoire officiel'::VARCHAR AS description,
        CASE
            WHEN raw_commune_name IN ('Bascharage', 'Clémency', 'Kaerjeng') THEN 'Käerjeng'
            WHEN raw_commune_name IN ('Boevange-sur-Attert', 'Tuntange') THEN 'Helperknapp'
            WHEN raw_commune_name IN ('Bous', 'Waldbredimus') THEN 'Bous-Waldbredimus'
            WHEN raw_commune_name IN ('Burmerange', 'Wellenstein') THEN 'Schengen'
            WHEN raw_commune_name IN ('Ermsdorf', 'Medernach') THEN 'Vallée de l''Ernz'
            WHEN raw_commune_name = 'Eschweiler' THEN 'Wiltz'
            WHEN raw_commune_name IN ('Grosbous', 'Wahl', 'Grosbus-Wal', 'Grosbous-Wal') THEN 'Groussbus-Wal'
            WHEN raw_commune_name IN ('Heiderscheid', 'Neunhausen') THEN 'Esch-sur-Sûre'
            WHEN raw_commune_name IN ('Heinerscheid', 'Munshausen') THEN 'Clervaux'
            WHEN raw_commune_name IN ('Hobscheid', 'Septfontaines') THEN 'Habscht'
            WHEN raw_commune_name IN ('Hoscheid', 'Hosingen') THEN 'Parc Hosingen'
            WHEN raw_commune_name IN ('Mompach', 'Rosport') THEN 'Rosport-Mompach'
            WHEN raw_commune_name = 'Petange' THEN 'Pétange'
            WHEN raw_commune_name = 'Erpeldange' THEN 'Erpeldange-sur-Sûre'
            WHEN raw_commune_name = 'Luxembourg-Ville' THEN 'Luxembourg'
            ELSE raw_commune_name
        END AS raw_commune_name,
        NULL::VARCHAR AS canton_override,
        NULL::TIMESTAMP AS observed_at_utc,
        source_id
    FROM obs_raw
),
statec AS (
    SELECT
        record_id,
        'STATISTIC_STATEC' AS record_type,
        property_type,
        'NEW_VEFA' AS market_segment,
        reference_period,
        NULL::DOUBLE AS price_eur_m2,
        units_authorized AS units_count,
        permits_count,
        'Statistique des autorisations de bâtir délivrées (STATEC)'::VARCHAR AS description,
        raw_commune_name,
        canton_name AS canton_override,
        TRY_CAST(raw_observed_at AS TIMESTAMP) AS observed_at_utc,
        source_id
    FROM {{ ref('stg_housing_statec') }}
),
unified AS (
    SELECT * FROM obs
    UNION ALL
    SELECT * FROM statec
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    u.record_id,
    u.record_type,
    u.property_type,
    u.market_segment,
    u.reference_period,
    u.price_eur_m2,
    u.units_count,
    u.permits_count,
    u.description,
    COALESCE(c.code_lau, u.raw_commune_name) AS commune_lau,
    COALESCE(c.commune_name, u.raw_commune_name) AS commune_name,
    COALESCE(c.canton, u.canton_override, 'Luxembourg') AS canton,
    c.lat,
    c.lon,
    COALESCE(u.observed_at_utc, '2026-01-01 00:00:00'::TIMESTAMP) AS observed_at_utc,
    u.source_id
FROM unified u
LEFT JOIN ref_communes c
    ON LOWER(u.raw_commune_name) = LOWER(c.commune_name)
    OR LOWER(u.raw_commune_name) = LOWER(c.commune_name_lb)
    OR u.raw_commune_name = c.code_lau
