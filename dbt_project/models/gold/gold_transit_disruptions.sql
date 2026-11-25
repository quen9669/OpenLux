-- Gold perturbations transports publics : dernier état de chaque message
SELECT
    * EXCLUDE (start_time_utc, end_time_utc, observed_at),
    {{ utc('start_time_utc') }} AS start_time_utc,
    {{ utc('end_time_utc') }} AS end_time_utc,
    {{ utc('observed_at') }} AS published_at_utc
FROM {{ ref('stg_transit_disruptions') }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY source_id, disruption_id ORDER BY collected_at_utc DESC) = 1
