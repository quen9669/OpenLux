-- Staging pétitions de la Chambre des Députés (intitulé, statut, signatures)
{% set cols = {'petition_id': 'VARCHAR', 'filing_date': 'VARCHAR', 'title': 'VARCHAR', 'petition_type': 'VARCHAR', 'status': 'VARCHAR', 'signatures': 'DOUBLE'} %}
SELECT * FROM {{ bronze('petitions_chd', cols) }}
