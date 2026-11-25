-- Staging autorisations de bâtir STATEC (logements autorisés par canton)
{% set cols = {'canton': 'VARCHAR', 'canton_label': 'VARCHAR', 'product_bcs': 'VARCHAR', 'product_bcs_label': 'VARCHAR', 'indicator_bcs_label': 'VARCHAR', 'time_period': 'VARCHAR', 'obs_value': 'DOUBLE'} %}
SELECT * FROM {{ bronze('building_permits_statec', cols) }}
