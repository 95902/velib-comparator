"""Collecte d'un historique Vélib + météo, une ligne par zone et par relevé (issue #21)."""
from pathlib import Path

import pandas as pd

from src.indicateurs import stats_commune

CHEMIN_HISTORIQUE = Path(__file__).resolve().parent.parent / "data" / "historique" / "releves.csv"
METEO_VIDE = {"temperature_c": None, "vent_kmh": None, "pluie_mm": None}


def releve_zones(df, meteo, horodatage):
    """Résume l'état de chaque zone à un instant donné.

    Reçoit : le tableau nettoyé, le dict de meteo_actuelle() (ou None si la météo
    n'a pas répondu) et l'horodatage du relevé.
    Renvoie : un DataFrame, une ligne par zone : horodatage, zone, les indicateurs de
    stats_commune(), temperature_c, vent_kmh, pluie_mm.
    """
    meteo = meteo or METEO_VIDE
    lignes = []
    for zone in sorted(df["zone"].unique()):
        lignes.append({
            "horodatage": horodatage,
            "zone": zone,
            **stats_commune(df, zone),
            "temperature_c": meteo["temperature_c"],
            "vent_kmh": meteo["vent_kmh"],
            "pluie_mm": meteo["pluie_mm"],
        })
    return pd.DataFrame(lignes)


def ajouter_a_historique(releve, chemin=CHEMIN_HISTORIQUE):
    """Ajoute un relevé à la fin du CSV d'historique (créé avec ses en-têtes s'il n'existe pas).

    Reçoit : le DataFrame de releve_zones() et le chemin du CSV.
    Renvoie : rien.
    """
    chemin.parent.mkdir(parents=True, exist_ok=True)
    releve.to_csv(chemin, mode="a", header=not chemin.exists(), index=False)


def lire_historique(chemin=CHEMIN_HISTORIQUE):
    """Reçoit : le chemin du CSV. Renvoie : l'historique (horodatage en date), ou None s'il n'existe pas."""
    if not chemin.exists():
        return None
    return pd.read_csv(chemin, parse_dates=["horodatage"])
