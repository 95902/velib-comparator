"""Nettoyage des données Vélib : du tableau brut au tableau du contrat (issue #4)."""
import difflib
import unicodedata

import pandas as pd

# Colonnes du tableau nettoyé, dans l'ordre du contrat
COLONNES_CONTRAT = [
    "stationcode", "name", "commune", "commune_norm", "zone", "en_service",
    "capacity", "numbikesavailable", "numdocksavailable", "mechanical", "ebike",
    "lat", "lon", "duedate",
]
COLONNES_ENTIERES = ["capacity", "numbikesavailable", "numdocksavailable", "mechanical", "ebike"]


class CommuneIntrouvable(ValueError):
    """Le nom demandé n'est ni une commune ni un arrondissement du tableau.

    Attributs : nom (le nom tapé) et suggestion (le nom proche à proposer, ou None).
    """

    def __init__(self, nom, suggestion=None):
        message = f"Commune introuvable : « {nom} »."
        if suggestion:
            message += f" Vouliez-vous dire {suggestion} ?"
        super().__init__(message)
        self.nom = nom
        self.suggestion = suggestion


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


def zone_station(stationcode, commune_norm):
    """Donne la zone d'une station : sa commune, ou son arrondissement à Paris.

    Reçoit : le stationcode (texte) et la commune normalisée.
    Renvoie : la zone normalisée, ex. "montreuil", "paris 11".
    À Paris, le code commence par le numéro d'arrondissement : "10202" → "paris 10",
    "3012" → "paris 3". Un code hors de cette règle (ex. "60001") donne "paris".
    """
    if commune_norm != "paris":
        return commune_norm
    debut = stationcode[:-3]  # on enlève les 3 derniers chiffres
    if debut.isdigit() and 1 <= int(debut) <= 20:
        return f"paris {int(debut)}"
    return "paris"


def zones_disponibles(df):
    """Liste les noms qu'on peut comparer, pour les listes déroulantes.

    Reçoit : le tableau nettoyé.
    Renvoie : les communes triées (« Paris » compris), puis « Paris 1 » à « Paris 20 ».
    """
    communes = sorted(df["commune"].unique())
    arrondissements = sorted(
        (z for z in df["zone"].unique() if z.startswith("paris ")),
        key=lambda z: int(z.split()[1]),
    )
    return communes + [z.title() for z in arrondissements]


def suggerer_zone(df, nom):
    """Cherche le nom de commune ou d'arrondissement le plus proche d'une faute de frappe.

    Reçoit : le tableau nettoyé et le nom tapé (ex. "montreuill").
    Renvoie : le nom tel qu'affiché (ex. "Montreuil"), ou None si rien n'est assez proche.
    """
    noms = {normaliser(zone): zone for zone in zones_disponibles(df)}
    proches = difflib.get_close_matches(normaliser(nom), list(noms), n=1, cutoff=0.6)
    return noms[proches[0]] if proches else None


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
    df["zone"] = [zone_station(code, commune) for code, commune in zip(df["stationcode"], df["commune_norm"])]

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
