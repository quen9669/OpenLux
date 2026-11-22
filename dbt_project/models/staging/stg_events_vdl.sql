-- Staging: Extraction brute des événements Ville de Luxembourg depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/events_vdl/latest.json.gz')
)
SELECT
    raw_source.event_id::VARCHAR AS event_id,
    raw_source.title::VARCHAR AS title,
    'Confirmé' AS status,
    raw_source.start_date::VARCHAR AS raw_start_date,
    raw_source.end_date::VARCHAR AS raw_end_date,
    CURRENT_TIMESTAMP AS observed_at_utc,
    NULL::VARCHAR AS start_time,
    raw_source.venue::VARCHAR AS venue,
    NULL::VARCHAR AS address,
    raw_source.city::VARCHAR AS raw_city,
    raw_source.category::VARCHAR AS category,
    TRY_CAST(raw_source.price_eur AS DOUBLE) AS price_eur,
    COALESCE(raw_source.price_text::VARCHAR, CASE WHEN TRY_CAST(raw_source.price_eur AS DOUBLE) = 0.0 THEN 'Gratuit' ELSE NULL END) AS price_text,
    COALESCE(TRY_CAST(raw_source.is_free AS BOOLEAN), TRY_CAST(raw_source.price_eur AS DOUBLE) = 0.0, false) AS is_free,
    raw_source.source_url::VARCHAR AS source_url,
    NULL::VARCHAR AS ticket_url,
    NULL::DOUBLE AS lat_echo,
    NULL::DOUBLE AS lon_echo,
    'events_vdl' AS source_id
FROM raw_source
