-- Staging articles de presse mentionnant une grève (titre et lien uniquement)
{% set cols = {'article_id': 'VARCHAR', 'title': 'VARCHAR', 'published_at_utc': 'VARCHAR', 'country_code': 'VARCHAR', 'publisher': 'VARCHAR', 'url': 'VARCHAR'} %}
SELECT * FROM {{ bronze('strikes_news', cols) }}
