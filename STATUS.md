# État de Santé des Sources OpenLux Hub

> Ce fichier est automatiquement mis à jour à chaque exécution du pipeline (`openlux run`).
> Dernière mise à jour : *Initialisation socle (Phase 0)*.

| Domaine | Source ID | État | Trust Score | Source Active | Lignes | Dernier contrôle (UTC) | Dernière mutation (UTC) | Licence |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| *weather* | `meteo_lux_obs` | `NOT_TESTED` | - | - | - | - | - | `CC0-1.0` |
| *traffic_cita* | `traffic_cita_datex2` | `NOT_TESTED` | - | - | - | - | - | `CC0-1.0` |
| *holidays_vacations* | `holidays_lu` | `NOT_TESTED` | - | - | - | - | - | `CC0-1.0` |

*Légende des états :*
- 🟢 `GOOD` (85-100) : Nominal.
- 🟡 `ATTENTION` (60-84) : Alerte mineure, source de secours active ou retard SLA.
- 🔴 `ERROR` (<60) : Erreur critique, pipeline bloqué ou schéma invalide.
- ⚪ `NOT_TESTED` : Source en cours d'intégration ou clé API absente en environnement local.
