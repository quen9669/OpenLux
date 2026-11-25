"""Rôle : Libellés éditoriaux des tables Gold (domaine affiché, titre, standards appliqués).
Entrées/Sorties : Constante importée par le catalogue ; aucun chiffre (tout est mesuré ailleurs).
Hors-scope : Aucune logique.
"""

from __future__ import annotations

_D2, _GEO = "DATEX II (CEN/TS 16157)", "GeoJSON (EPSG:4326)"
# POURQUOI : (domaine affiché, titre, standards) — seule information éditoriale du catalogue
TABLE_INFO: dict[str, tuple[str, str, list[str]]] = {
    "gold_weather_observations": (
        "Environnement",
        "Météo horaire (station Findel + 12 cantons)",
        [_GEO],
    ),
    "gold_air_quality": ("Environnement", "Qualité de l'air et pollens (modèle CAMS)", [_GEO]),
    "gold_water_levels": ("Environnement", "Niveaux d'eau des rivières (15 min)", [_GEO]),
    "gold_bathing_water": ("Environnement", "Eaux de baignade", ["Directive 2006/7/CE", _GEO]),
    "gold_weather_warnings": ("Environnement", "Vigilances météo MeteoLux", ["CAP 1.2"]),
    "gold_traffic_events": ("Mobilité", "Événements trafic LU et frontaliers", [_D2, _GEO]),
    "gold_roadworks": ("Mobilité", "Chantiers routiers", [_D2, _GEO]),
    "gold_transit_disruptions": ("Mobilité", "Perturbations bus et trains", ["SIRI SX"]),
    "gold_mobility_veloh": ("Mobilité", "Disponibilités Vel'oh", ["GBFS 2.3", _GEO]),
    "gold_mobility_parkings": ("Mobilité", "Occupation des parkings (Ville)", [_GEO]),
    "gold_chargy_stations": ("Mobilité", "Bornes de recharge Chargy", [_GEO]),
    "gold_aviation": ("Mobilité", "Aéronefs au-dessus du Luxembourg", [_GEO]),
    "gold_fuel_prices": ("Économie", "Prix mensuels des carburants", []),
    "gold_inflation": ("Économie", "Indice des prix IPCN (STATEC)", ["SDMX"]),
    "gold_electricity_spot": ("Économie", "Prix spot électricité DE-LU", []),
    "gold_unemployment": ("Économie", "Demandeurs d'emploi par commune (ADEM)", []),
    "gold_building_permits": ("Logement", "Logements autorisés par canton (STATEC)", ["SDMX"]),
    "gold_housing_prices": ("Logement", "Prix annoncés par commune (Observatoire)", []),
    "gold_holidays": ("Calendrier", "Jours fériés LU/FR/BE/DE et vacances", []),
    "gold_equipment": ("Territoire", "Équipements : recyclage, DAE, vélo", [_GEO]),
    "gold_petitions": ("Vie civique", "Pétitions à la Chambre des Députés", []),
    "gold_culture_events": ("Culture", "Agenda culturel", [_GEO]),
    "gold_strikes_news": ("Actualité", "Articles de presse sur les grèves", ["RSS 2.0"]),
    "gold_luxembourg_daily_context": ("Synthèse", "Contexte quotidien par canton", []),
}
