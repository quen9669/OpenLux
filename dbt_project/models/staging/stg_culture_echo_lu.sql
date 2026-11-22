-- Staging: Extraction brute des sorties culturelles Echo.lu depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto(
        'data/bronze/culture_echo_lu/**/*.json.gz', union_by_name = true,
        columns={
            'title': 'VARCHAR',
            'status': 'VARCHAR',
            'start_date': 'VARCHAR',
            'end_date': 'VARCHAR',
            'start_time': 'VARCHAR',
            'venue': 'VARCHAR',
            'address': 'VARCHAR',
            'city': 'VARCHAR',
            'category': 'VARCHAR',
            'price_eur': 'DOUBLE',
            'price_text': 'VARCHAR',
            'is_free': 'BOOLEAN',
            'source_url': 'VARCHAR',
            'ticket_url': 'VARCHAR',
            'lat': 'DOUBLE',
            'lon': 'DOUBLE'
        }
    )
)
SELECT DISTINCT
    raw_source.title::VARCHAR AS title,
    COALESCE(raw_source.status::VARCHAR, 'Confirmé') AS status,
    raw_source.start_date::VARCHAR AS raw_start_date,
    raw_source.end_date::VARCHAR AS raw_end_date,
    CURRENT_TIMESTAMP AS observed_at_utc,
    raw_source.start_time::VARCHAR AS start_time,
    raw_source.venue::VARCHAR AS venue,
    raw_source.address::VARCHAR AS address,
    raw_source.city::VARCHAR AS raw_city,
    raw_source.category::VARCHAR AS category,
    TRY_CAST(raw_source.price_eur AS DOUBLE) AS price_eur,
    COALESCE(raw_source.price_text::VARCHAR, CASE WHEN TRY_CAST(raw_source.price_eur AS DOUBLE) = 0.0 THEN 'Gratuit' ELSE NULL END) AS price_text,
    COALESCE(TRY_CAST(raw_source.is_free AS BOOLEAN), TRY_CAST(raw_source.price_eur AS DOUBLE) = 0.0, false) AS is_free,
    raw_source.source_url::VARCHAR AS source_url,
    raw_source.ticket_url::VARCHAR AS ticket_url,
    TRY_CAST(raw_source.lat AS DOUBLE) AS lat_echo,
    TRY_CAST(raw_source.lon AS DOUBLE) AS lon_echo,
    'culture_echo_lu' AS source_id
FROM raw_source
