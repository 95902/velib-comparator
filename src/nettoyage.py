"""Nettoyage des données Vélib : du tableau brut au tableau du contrat (issue #4)."""
import unicodedata

import pandas as pd

# Colonnes du tableau nettoyé, dans l'ordre du contrat
COLONNES_CONTRAT = [
    "stationcode", "name", "commune", "commune_norm", "en_service",
    "capacity", "numbikesavailable", "numdocksavailable", "mechanical", "ebike",
    "lat", "lon", "duedate",
]
COLONNES_ENTIERES = ["capacity", "numbikesavailable", "numdocksavailable", "mechanical", "ebike"]


def normaliser(texte):
    """Met un nom de commune sous une forme comparable.

    Reçoit : un texte (ex. "Saint-Denis", "  CRÉTEIL ").
    Renvoie : le texte en minuscules, sans accents, tirets et apostrophes remplacés
    par des espaces, sans espaces en trop (ex. "saint denis", "creteil").
    """
    texte = unicodedata.normalize("NFKD", str(texte))
    # NFKD sépare « é » en « e » + accent : on garde seulement les lettres de base
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    texte = texte.lower().replace("-", " ").replace("'", " ").replace("’", " ")
    return " ".join(texte.split())


def nettoyer_velib(df_brut):
    """Transforme le tableau brut en tableau nettoyé.

    Reçoit : le DataFrame brut renvoyé par telecharger_velib() (ou relu depuis le CSV).
    Renvoie : (df, rapport)
      - df : le tableau nettoyé, colonnes de COLONNES_CONTRAT ;
      - rapport : dict avec stations_brutes, doublons_retires, hors_service,
        capacite_nulle, stations_finales.
    Les stations hors service ne sont pas supprimées : elles ont en_service = False.
    """
    df = df_brut.copy()
    df["stationcode"] = df["stationcode"].astype(str)
    stations_brutes = len(df)

    # 1. Doublons : une seule ligne par station
    df = df.drop_duplicates(subset="stationcode")
    doublons_retires = stations_brutes - len(df)

    # 2. Noms du contrat (station_opening_hours, vide partout, disparaît à l'étape 5)
    df = df.rename(columns={
        "coordonnees_geo.lat": "lat",
        "coordonnees_geo.lon": "lon",
        "nom_arrondissement_communes": "commune",
    })

    # 3. Types : entiers pour les compteurs
    for colonne in COLONNES_ENTIERES:
        df[colonne] = pd.to_numeric(df[colonne], errors="coerce").fillna(0).astype(int)
    df["duedate"] = pd.to_datetime(df["duedate"], utc=True, errors="coerce")

    # 4. En service : installée, prête et rend les vélos, avec au moins une borne
    capacite_nulle = df["capacity"] == 0
    df["en_service"] = (
        (df["is_installed"] == "OUI")
        & (df["is_renting"] == "OUI")
        & (df["is_returning"] == "OUI")
        & ~capacite_nulle
    )
    df["commune_norm"] = df["commune"].map(normaliser)

    # 5. On ne garde que les colonnes du contrat
    df = df[COLONNES_CONTRAT].reset_index(drop=True)

    rapport = {
        "stations_brutes": stations_brutes,
        "doublons_retires": doublons_retires,
        "hors_service": int((~df["en_service"]).sum()),
        "capacite_nulle": int(capacite_nulle.sum()),
        "stations_finales": len(df),
    }
    return df, rapport


if __name__ == "__main__":
    from src.recuperation import CHEMIN_BRUT

    df, rapport = nettoyer_velib(pd.read_csv(CHEMIN_BRUT, dtype={"stationcode": str}))
    print(rapport)
    print(df.head())
