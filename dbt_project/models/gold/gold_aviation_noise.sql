-- Gold: Data Mart final des mouvements aéroportuaires et zones de bruit Findel
SELECT
    record_id,
    record_type,
    callsign_or_zone,
    observed_at_utc,
    altitude_m_or_dba,
    status,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_aviation_noise') }}
