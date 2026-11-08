import json
from pathlib import Path

import pandas as pd
import requests

URL_VELIB = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/exports/json"
CHEMIN_BRUT = Path(__file__).resolve().parent.parent / "data" / "brut" / "velib.csv"
CHEMIN_UTILISATEURS = Path(__file__).resolve().parent.parent / "data" / "utilisateurs.json"
# Sans ces colonnes remplies, une station ne peut être ni comptée ni placée sur la carte
COLONNES_ESSENTIELLES = ["stationcode", "name", "nom_arrondissement_communes", "coordonnees_geo.lat", "coordonnees_geo.lon"]


class DonneesIndisponibles(RuntimeError):
    """Ni l'API Vélib ni le dernier CSV téléchargé ne sont disponibles."""


class ReponseVelibInvalide(requests.RequestException):
    """L'API a répondu, mais sans les informations des stations (code, nom, commune, position).

    Hérite de requests.RequestException : partout où l'on gère « l'API ne répond pas »,
    une réponse vide est gérée de la même façon (repli sur le dernier CSV, relevé ignoré).
    """


def verifier_velib(df):
    """Vérifie qu'un tableau brut contient de vraies stations.

    Reçoit : un DataFrame brut (réponse de l'API ou CSV relu).
    Renvoie : rien.
    Lève ReponseVelibInvalide si une colonne essentielle manque, ou si plus de la moitié
    des stations n'ont pas leurs informations essentielles (panne de l'open data).
    """
    manquantes = [colonne for colonne in COLONNES_ESSENTIELLES if colonne not in df.columns]
    if manquantes:
        raise ReponseVelibInvalide(f"Données Vélib incomplètes : colonnes absentes {manquantes}.")
    incompletes = df[COLONNES_ESSENTIELLES].isna().any(axis=1)
    if df.empty or incompletes.mean() > 0.5:
        raise ReponseVelibInvalide(
            f"Données Vélib inutilisables : {int(incompletes.sum())} stations sur {len(df)} "
            "sans code, nom, commune ou position."
        )


def telecharger_velib():
    """Télécharge la disponibilité en temps réel de toutes les stations Vélib.

    Reçoit : rien.
    Renvoie : un DataFrame brut (une ligne par station), aussi enregistré dans data/brut/velib.csv.
    Lève requests.HTTPError si l'API répond une erreur, ReponseVelibInvalide si sa réponse
    est vide ou cassée (le CSV précédent n'est alors pas écrasé).
    """
    reponse = requests.get(URL_VELIB, timeout=30)
    reponse.raise_for_status()

    # json_normalize sépare coordonnees_geo en coordonnees_geo.lon / coordonnees_geo.lat
    df = pd.json_normalize(reponse.json())
    verifier_velib(df)  # avant d'écrire : on garde le dernier bon CSV comme secours

    CHEMIN_BRUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CHEMIN_BRUT, index=False)
    return df


def charger_velib_brut():
    """Télécharge les données Vélib, ou relit le dernier CSV si l'API ne répond pas.

    Reçoit : rien.
    Renvoie : (df_brut, en_direct) ; en_direct vaut False si on a dû relire data/brut/velib.csv.
    Lève DonneesIndisponibles si l'API ne répond pas (ou renvoie des données vides) et que
    le CSV n'existe pas ou n'est pas utilisable.
    """
    try:
        return telecharger_velib(), True
    except requests.RequestException as erreur:
        message = (
            "L'API Vélib ne répond pas (pas de connexion internet ?) ou renvoie des données vides, "
            "et aucun téléchargement précédent n'est utilisable."
        )
        if not CHEMIN_BRUT.exists():
            raise DonneesIndisponibles(message) from erreur
        df = pd.read_csv(CHEMIN_BRUT, dtype={"stationcode": str})
        try:
            verifier_velib(df)
        except ReponseVelibInvalide:
            raise DonneesIndisponibles(message) from erreur
        return df, False


def charger_utilisateurs():
    """Lit les utilisateurs (inventés) et leurs lieux habituels.

    Reçoit : rien (lit data/utilisateurs.json).
    Renvoie : une liste de dicts {"nom": ..., "lieux": {"domicile": {"lat": ..., "lon": ...}, ...}}.
    Lève FileNotFoundError avec un message clair si le fichier manque.
    """
    if not CHEMIN_UTILISATEURS.exists():
        raise FileNotFoundError(f"Fichier des utilisateurs introuvable : {CHEMIN_UTILISATEURS}")
    with open(CHEMIN_UTILISATEURS, encoding="utf-8") as fichier:
        return json.load(fichier)


if __name__ == "__main__":
    df = telecharger_velib()
    print("Nombre de stations :", len(df))
    print(df.head())
