from pathlib import Path

import pandas as pd
import requests

URL_VELIB = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/exports/json"
CHEMIN_BRUT = Path(__file__).resolve().parent.parent / "data" / "brut" / "velib.csv"


def telecharger_velib():
    """Télécharge la disponibilité en temps réel de toutes les stations Vélib.

    Reçoit : rien.
    Renvoie : un DataFrame brut (une ligne par station), aussi enregistré dans data/brut/velib.csv.
    Lève requests.HTTPError si l'API répond une erreur.
    """
    reponse = requests.get(URL_VELIB, timeout=30)
    reponse.raise_for_status()

    # json_normalize sépare coordonnees_geo en coordonnees_geo.lon / coordonnees_geo.lat
    df = pd.json_normalize(reponse.json())

    CHEMIN_BRUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CHEMIN_BRUT, index=False)
    return df


if __name__ == "__main__":
    df = telecharger_velib()
    print("Nombre de stations :", len(df))
    print(df.head())
