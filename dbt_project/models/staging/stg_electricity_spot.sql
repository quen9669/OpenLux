-- Staging prix spot day-ahead DE-LU
{% set cols = {'observed_at': 'VARCHAR', 'price_eur_per_mwh': 'DOUBLE', 'bidding_zone': 'VARCHAR'} %}
SELECT * FROM {{ bronze('electricity_spot_delu', cols) }}
