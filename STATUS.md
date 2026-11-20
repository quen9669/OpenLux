# État de Santé des Sources OpenLux Hub

> Ce fichier est mis à jour à chaque exécution du pipeline (`openlux run`).

| Domaine | Source ID | État | Trust Score | Source Active | Lignes | Dernier contrôle (UTC) | Dernière mutation (UTC) | Licence |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| *weather* | `meteo_lux_obs` | 🟢 `GOOD` | 100.0 | primary | 3 | 2026-11-20T23:11:24.263641+00:00 | 2026-11-20T23:11:24.263641+00:00 | `CC0-1.0` |
| *traffic_cita* | `traffic_cita_datex2` | 🟢 `GOOD` | 100.0 | primary | 2 | 2026-11-20T23:11:24.284293+00:00 | 2026-11-20T23:11:24.284293+00:00 | `CC0-1.0` |
| *holidays_vacations* | `holidays_lu` | 🟢 `GOOD` | 100.0 | primary | 11 | 2026-11-20T23:11:24.314604+00:00 | 2026-11-20T23:11:24.314604+00:00 | `CC0-1.0` |

*Légende des états :*
- 🟢 `GOOD` (85-100) : Nominal.
- 🟡 `ATTENTION` (60-84) : Alerte mineure, source de secours active ou retard SLA.
- 🔴 `ERROR` (<60) : Erreur critique, pipeline bloqué ou schéma invalide.
- ⚪ `NOT_TESTED` : En intégration ou clé API absente en local.
