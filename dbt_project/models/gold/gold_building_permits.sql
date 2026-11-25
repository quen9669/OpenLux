-- Gold logements autorisés par canton et type de bâtiment (STATEC)
SELECT
    canton AS canton_code, REPLACE(canton_label, 'Canton ', '') AS canton,
    product_bcs AS building_type_code, product_bcs_label AS building_type,
    indicator_bcs_label AS indicator, TRY_CAST(time_period AS INTEGER) AS reference_year,
    obs_value AS dwellings, collected_at_utc, source_id
FROM {{ ref('stg_building_permits') }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY canton, product_bcs, time_period ORDER BY collected_at_utc DESC) = 1
