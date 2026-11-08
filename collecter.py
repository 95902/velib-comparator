"""Enregistre un relevé Vélib + météo toutes les 15 minutes dans data/historique/releves.csv.

Lance : python collecter.py              (Ctrl+C pour arrêter)
        python collecter.py --une-fois   (un seul relevé, pour tester)
        python collecter.py --minutes 5  (autre intervalle)
"""
import argparse
import time

import pandas as pd
import requests

from src.collecte import CHEMIN_HISTORIQUE, ajouter_a_historique, releve_zones
from src.meteo import CleMeteoAbsente, meteo_actuelle
from src.nettoyage import nettoyer_velib
from src.recuperation import telecharger_velib


def faire_un_releve():
    """Reçoit : rien. Télécharge Vélib et la météo, ajoute une ligne par zone à l'historique."""
    horodatage = pd.Timestamp.now(tz="UTC").floor("s")
    heure = horodatage.tz_convert("Europe/Paris")  # pour les messages seulement
    try:
        df, _ = nettoyer_velib(telecharger_velib())
    except requests.RequestException as erreur:
        # Pas de repli sur l'ancien CSV : un relevé daté doit contenir des données de ce moment
        print(f"{heure:%H:%M} relevé ignoré, API Vélib injoignable : {erreur}")
        return
    try:
        meteo = meteo_actuelle()
    except (CleMeteoAbsente, requests.RequestException) as erreur:
        print(f"{heure:%H:%M} météo indisponible ({erreur}) : relevé enregistré sans météo")
        meteo = None

    releve = releve_zones(df, meteo, horodatage)
    ajouter_a_historique(releve)
    print(f"{heure:%H:%M} relevé enregistré : {len(releve)} zones → {CHEMIN_HISTORIQUE}")


def main():
    parser = argparse.ArgumentParser(description="Collecte l'historique Vélib + météo.")
    parser.add_argument("--une-fois", action="store_true", help="un seul relevé puis arrêt")
    parser.add_argument("--minutes", type=float, default=15, help="intervalle entre deux relevés (15 par défaut)")
    args = parser.parse_args()

    while True:
        faire_un_releve()
        if args.une_fois:
            break
        time.sleep(args.minutes * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Collecte arrêtée.")
