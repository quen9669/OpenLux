-- Staging: Extraction brute des stations Vel'oH depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto(
        'data/bronze/veloh_stations/**/*.json.gz', union_by_name = true,
        columns={
            'facility_id': 'VARCHAR',
            'facility_name': 'VARCHAR',
            'available_bikes': 'INTEGER',
            'total_capacity': 'INTEGER',
            'available_stands': 'INTEGER',
            'broken_stands': 'INTEGER',
            'is_installed': 'BOOLEAN',
            'is_renting': 'BOOLEAN',
            'observed_at': 'VARCHAR',
            'lat': 'DOUBLE',
            'lon': 'DOUBLE',
            'commune_name': 'VARCHAR'
        }
    )
)
SELECT DISTINCT
    facility_id::VARCHAR AS station_id,
    facility_name::VARCHAR AS station_name,
    COALESCE(available_bikes::INTEGER, 0) AS available_bikes,
    COALESCE(total_capacity::INTEGER, 15) AS total_capacity,
    COALESCE(
        available_stands::INTEGER,
        GREATEST(COALESCE(total_capacity::INTEGER, 15) - COALESCE(available_bikes::INTEGER, 0), 0)
    ) AS available_stands,
    COALESCE(
        broken_stands::INTEGER,
        GREATEST(
            COALESCE(total_capacity::INTEGER, 15) - (
                COALESCE(available_bikes::INTEGER, 0) +
                COALESCE(
                    available_stands::INTEGER,
                    GREATEST(COALESCE(total_capacity::INTEGER, 15) - COALESCE(available_bikes::INTEGER, 0), 0)
                )
            ),
            0
        )
    ) AS broken_stands,
    COALESCE(is_installed::BOOLEAN, true) AS is_installed,
    COALESCE(is_renting::BOOLEAN, true) AS is_renting,
    '24/7' AS opening_hours,
    observed_at::VARCHAR AS raw_observed_at,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'veloh_stations' AS source_id
FROM raw_source
WHERE facility_name IS NOT NULL
