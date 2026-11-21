-- Gold: Data Mart final de l'état des transports publics (CFL, Tram, RGTR, AVL)
SELECT
    line_id,
    network,
    observed_at_utc,
    delay_seconds,
    disruption_level,
    message,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_public_transit') }}
