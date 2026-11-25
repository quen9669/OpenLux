-- Zero-PII : aucun e-mail ni téléphone luxembourgeois dans les textes Gold : 0 ligne attendue
SELECT 'gold_traffic_events' AS gold_table, description AS sample FROM {{ ref('gold_traffic_events') }} WHERE regexp_matches(description, '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}|(\+|00)352[ .-]?[0-9]{4,}')
UNION ALL
SELECT 'gold_roadworks' AS gold_table, title AS sample FROM {{ ref('gold_roadworks') }} WHERE regexp_matches(title, '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}|(\+|00)352[ .-]?[0-9]{4,}')
UNION ALL
SELECT 'gold_transit_disruptions' AS gold_table, title AS sample FROM {{ ref('gold_transit_disruptions') }} WHERE regexp_matches(title, '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}|(\+|00)352[ .-]?[0-9]{4,}')
UNION ALL
SELECT 'gold_culture_events' AS gold_table, title AS sample FROM {{ ref('gold_culture_events') }} WHERE regexp_matches(title, '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}|(\+|00)352[ .-]?[0-9]{4,}')
UNION ALL
SELECT 'gold_strikes_news' AS gold_table, title AS sample FROM {{ ref('gold_strikes_news') }} WHERE regexp_matches(title, '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}|(\+|00)352[ .-]?[0-9]{4,}')
UNION ALL
SELECT 'gold_petitions' AS gold_table, title AS sample FROM {{ ref('gold_petitions') }} WHERE regexp_matches(title, '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}|(\+|00)352[ .-]?[0-9]{4,}')
UNION ALL
SELECT 'gold_equipment' AS gold_table, details AS sample FROM {{ ref('gold_equipment') }} WHERE regexp_matches(details, '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}|(\+|00)352[ .-]?[0-9]{4,}')
UNION ALL
SELECT 'gold_weather_warnings' AS gold_table, event AS sample FROM {{ ref('gold_weather_warnings') }} WHERE regexp_matches(event, '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}|(\+|00)352[ .-]?[0-9]{4,}')
