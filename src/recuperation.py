from pathlib import Path

import pandas as pd
import requests

URL_VELIB = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/exports/json"
CHEMIN_BRUT = Path(__file__).resolve().parent.parent / "data" / "brut" / "velib.csv"


class DonneesIndisponibles(RuntimeError):
    """Ni l'API Vélib ni le dernier CSV téléchargé ne sont disponibles."""


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


def charger_velib_brut():
    """Télécharge les données Vélib, ou relit le dernier CSV si l'API ne répond pas.

    Reçoit : rien.
    Renvoie : (df_brut, en_direct) ; en_direct vaut False si on a dû relire data/brut/velib.csv.
    Lève DonneesIndisponibles si l'API ne répond pas et que le CSV n'existe pas.
    """
    try:
        return telecharger_velib(), True
    except requests.RequestException as erreur:
        if not CHEMIN_BRUT.exists():
            raise DonneesIndisponibles(
                "Impossible de joindre l'API Vélib (pas de connexion internet ?) "
                "et aucun téléchargement précédent n'est disponible."
            ) from erreur
        return pd.read_csv(CHEMIN_BRUT, dtype={"stationcode": str}), False


if __name__ == "__main__":
    df = telecharger_velib()
    print("Nombre de stations :", len(df))
    print(df.head())
