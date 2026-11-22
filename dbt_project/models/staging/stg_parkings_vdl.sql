-- Staging: Extraction brute des parkings et P+R VDL depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto(
        'data/bronze/parkings_vdl/**/*.json.gz', union_by_name = true,
        columns={
            'facility_id': 'VARCHAR',
            'facility_name': 'VARCHAR',
            'available_spaces': 'INTEGER',
            'total_capacity': 'INTEGER',
            'trend': 'INTEGER',
            'is_open': 'BOOLEAN',
            'is_full': 'BOOLEAN',
            'is_out_of_order': 'BOOLEAN',
            'observed_at': 'VARCHAR',
            'lat': 'DOUBLE',
            'lon': 'DOUBLE',
            'commune_name': 'VARCHAR'
        }
    )
)
SELECT DISTINCT
    facility_id::VARCHAR AS parking_id,
    facility_name::VARCHAR AS parking_name,
    available_spaces::INTEGER AS available_spaces,
    total_capacity::INTEGER AS total_capacity,
    COALESCE(trend::INTEGER, 0) AS trend,
    COALESCE(is_open::BOOLEAN, true) AS is_open,
    COALESCE(is_full::BOOLEAN, (total_capacity::INTEGER > 0 AND available_spaces::INTEGER = 0)) AS is_full,
    COALESCE(is_out_of_order::BOOLEAN, false) AS is_out_of_order,
    (facility_name LIKE '%Bouillon%' OR facility_name LIKE '%P+R%') AS is_free_pr,
    '24/7' AS opening_hours,
    observed_at::VARCHAR AS raw_observed_at,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'parkings_vdl' AS source_id
FROM raw_source
WHERE facility_name IS NOT NULL
