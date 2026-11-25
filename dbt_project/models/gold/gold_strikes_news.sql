-- Gold articles de presse sur les grèves (titre, éditeur, date, lien)
SELECT * EXCLUDE (published_at_utc), {{ utc('published_at_utc') }} AS published_at_utc
FROM {{ ref('stg_strikes_news') }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY article_id ORDER BY collected_at_utc DESC) = 1
