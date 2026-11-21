# État de Santé des Sources OpenLux Hub

> Ce fichier est mis à jour à chaque exécution du pipeline (`openlux run`).

| Domaine | Source ID | État | Trust Score | Source Active | Lignes | Dernier contrôle (UTC) | Dernière mutation (UTC) | Licence |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| *weather* | `meteo_lux_obs` | 🟢 `GOOD` | 100.0 | primary | 3 | 2026-11-20T23:57:22.497496+00:00 | 2026-11-20T23:57:22.497496+00:00 | `CC0-1.0` |
| *traffic_cita* | `traffic_cita_datex2` | 🟢 `GOOD` | 100.0 | primary | 2 | 2026-11-20T23:57:22.510522+00:00 | 2026-11-20T23:57:22.510522+00:00 | `CC0-1.0` |
| *holidays_vacations* | `holidays_lu` | 🟢 `GOOD` | 100.0 | primary | 11 | 2026-11-20T23:57:22.521834+00:00 | 2026-11-20T23:57:22.521834+00:00 | `CC0-1.0` |
| *air_quality* | `air_quality_lu` | 🟢 `GOOD` | 100.0 | primary | 4 | 2026-11-20T23:57:22.531838+00:00 | 2026-11-20T23:57:22.531838+00:00 | `CC0-1.0` |
| *water_levels* | `water_levels_lu` | 🟢 `GOOD` | 100.0 | primary | 4 | 2026-11-20T23:57:22.542691+00:00 | 2026-11-20T23:57:22.542691+00:00 | `CC0-1.0` |
| *economy_fuel* | `fuel_prices_lu` | 🟢 `GOOD` | 100.0 | primary | 4 | 2026-11-20T23:57:22.553217+00:00 | 2026-11-20T23:57:22.553217+00:00 | `CC0-1.0` |
| *economy_fuel* | `statec_inflation` | 🟢 `GOOD` | 100.0 | primary | 3 | 2026-11-20T23:57:22.563131+00:00 | 2026-11-20T23:57:22.563131+00:00 | `CC0-1.0` |
| *energy_climate* | `electricity_spot_delu` | 🟢 `GOOD` | 100.0 | primary | 4 | 2026-11-20T23:57:22.572702+00:00 | 2026-11-20T23:57:22.572702+00:00 | `CC0-1.0` |
| *energy_climate* | `radioactivity_lu` | 🟢 `GOOD` | 100.0 | primary | 4 | 2026-11-20T23:57:22.582290+00:00 | 2026-11-20T23:57:22.582290+00:00 | `CC0-1.0` |
| *energy_climate* | `bathing_water_lu` | 🟢 `GOOD` | 100.0 | primary | 4 | 2026-11-20T23:57:22.591952+00:00 | 2026-11-20T23:57:22.591952+00:00 | `CC0-1.0` |

*Légende des états :*
- 🟢 `GOOD` (85-100) : Nominal.
- 🟡 `ATTENTION` (60-84) : Alerte mineure, source de secours active ou retard SLA.
- 🔴 `ERROR` (<60) : Erreur critique, pipeline bloqué ou schéma invalide.
- ⚪ `NOT_TESTED` : En intégration ou clé API absente en local.
