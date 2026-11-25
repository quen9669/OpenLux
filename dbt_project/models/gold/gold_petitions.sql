-- Gold pétitions de la Chambre des Députés
SELECT * EXCLUDE (filing_date), CAST({{ utc('filing_date') }} AS DATE) AS filing_date
FROM {{ ref('stg_petitions') }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY petition_id ORDER BY collected_at_utc DESC) = 1
