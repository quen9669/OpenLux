-- Staging: Extraction brute des stations Vel'oH depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto(
        'data/bronze/veloh_stations/**/*.json.gz', union_by_name = true,
        columns={
            'facility_id': 'VARCHAR',
            'station_number': 'INTEGER',
            'facility_name': 'VARCHAR',
            'address': 'VARCHAR',
            'available_bikes': 'INTEGER',
            'available_electrical_bikes': 'INTEGER',
            'available_mechanical_bikes': 'INTEGER',
            'total_capacity': 'INTEGER',
            'available_stands': 'INTEGER',
            'broken_stands': 'INTEGER',
            'status': 'VARCHAR',
            'is_connected': 'BOOLEAN',
            'is_installed': 'BOOLEAN',
            'is_renting': 'BOOLEAN',
            'has_banking': 'BOOLEAN',
            'is_bonus': 'BOOLEAN',
            'observed_at': 'VARCHAR',
            'lat': 'DOUBLE',
            'lon': 'DOUBLE',
            'commune_name': 'VARCHAR'
        }
    )
)
SELECT DISTINCT
    facility_id::VARCHAR AS station_id,
    COALESCE(station_number::INTEGER, TRY_CAST(REGEXP_EXTRACT(facility_id, '[0-9]+') AS INTEGER)) AS station_number,
    facility_name::VARCHAR AS station_name,
    COALESCE(address::VARCHAR, '') AS address,
    COALESCE(available_bikes::INTEGER, 0) AS available_bikes,
    COALESCE(available_electrical_bikes::INTEGER, COALESCE(available_bikes::INTEGER, 0)) AS available_electrical_bikes,
    COALESCE(available_mechanical_bikes::INTEGER, 0) AS available_mechanical_bikes,
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
    COALESCE(status::VARCHAR, 'OPEN') AS status,
    COALESCE(is_connected::BOOLEAN, true) AS is_connected,
    COALESCE(is_installed::BOOLEAN, true) AS is_installed,
    COALESCE(is_renting::BOOLEAN, true) AS is_renting,
    COALESCE(has_banking::BOOLEAN, false) AS has_banking,
    COALESCE(is_bonus::BOOLEAN, false) AS is_bonus,
    '24/7' AS opening_hours,
    observed_at::VARCHAR AS raw_observed_at,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'veloh_stations' AS source_id
FROM raw_source
WHERE facility_name IS NOT NULL
