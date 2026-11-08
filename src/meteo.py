"""Météo du moment à Paris, depuis l'API Météo-France (Données Publiques d'Observation)."""
import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# La clé est abonnée à la version 2 de l'API (la v1 répond « Resource forbidden »)
URL_METEO = "https://public-api.meteofrance.fr/public/DPObs/v2/station/infrahoraire-6m"
STATION_MONTSOURIS = "75114001"  # Paris-Montsouris : une mesure toutes les 6 minutes
CHEMIN_ENV = Path(__file__).resolve().parent.parent / ".env"


class CleMeteoAbsente(RuntimeError):
    """La clé METEO_FRANCE_API_KEY n'est pas dans le fichier .env."""


def kelvin_vers_celsius(kelvin):
    """Reçoit une température en kelvins (ou None). Renvoie des °C arrondis à 0,1 (ou None)."""
    return None if kelvin is None else round(kelvin - 273.15, 1)


def ms_vers_kmh(vitesse):
    """Reçoit une vitesse en m/s (ou None). Renvoie des km/h arrondis à 0,1 (ou None)."""
    return None if vitesse is None else round(vitesse * 3.6, 1)


def meteo_actuelle():
    """Récupère la dernière mesure de la station Paris-Montsouris.

    Reçoit : rien (la clé est lue dans .env).
    Renvoie : dict avec temperature_c (°C), vent_kmh (km/h), pluie_mm (mm tombés
    sur les 6 dernières minutes) et heure_releve (date UTC de la mesure).
    Une valeur que la station n'a pas mesurée vaut None.
    Lève CleMeteoAbsente si la clé manque, requests.RequestException si l'API ne répond pas.
    """
    load_dotenv(CHEMIN_ENV)
    cle = os.getenv("METEO_FRANCE_API_KEY")
    if not cle:
        raise CleMeteoAbsente("Clé Météo-France absente : copie .env.example en .env et colle ta clé (voir README).")

    reponse = requests.get(
        URL_METEO,
        params={"id_station": STATION_MONTSOURIS, "format": "json"},
        headers={"apikey": cle},
        timeout=30,
    )
    reponse.raise_for_status()
    mesure = reponse.json()[0]  # l'API renvoie une liste d'une seule mesure

    return {
        "temperature_c": kelvin_vers_celsius(mesure.get("t")),
        "vent_kmh": ms_vers_kmh(mesure.get("ff")),
        "pluie_mm": mesure.get("rr_per"),
        "heure_releve": pd.Timestamp(mesure["validity_time"]),
    }


if __name__ == "__main__":
    print(meteo_actuelle())
