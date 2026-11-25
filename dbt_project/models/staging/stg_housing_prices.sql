-- Staging prix annoncés par commune (Observatoire de l'Habitat), appartements et maisons
{% set cols = {'reference_year': 'INTEGER', 'property_type': 'VARCHAR', 'commune_name': 'VARCHAR', 'offers_count': 'DOUBLE', 'avg_price_eur': 'DOUBLE', 'avg_price_eur_m2': 'DOUBLE'} %}
SELECT * FROM {{ bronze('housing_prices_apartments', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('housing_prices_houses', cols) }}
