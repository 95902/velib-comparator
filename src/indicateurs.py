"""Calcul des indicateurs d'une commune (ou d'un arrondissement) à partir du tableau nettoyé."""
import pandas as pd

from src.nettoyage import CommuneIntrouvable, normaliser, suggerer_zone


def pourcentage(partie, total):
    """Reçoit deux nombres. Renvoie partie / total en %, arrondi à 0,1 (0.0 si total vaut 0)."""
    return round(100 * partie / total, 1) if total else 0.0


def stations_de(df, nom):
    """Sélectionne les stations d'une commune ou d'une zone.

    Reçoit : le tableau nettoyé et un nom (« Paris », « Paris 11 », « montreuil »…).
    Renvoie : les lignes dont commune_norm ou zone correspond au nom normalisé
    (« Paris » donne tout Paris, « Paris 11 » seulement le 11ᵉ).
    """
    nom_norm = normaliser(nom)
    return df[(df["commune_norm"] == nom_norm) | (df["zone"] == nom_norm)]


def etat_station(df):
    """Donne l'état de chaque station, pour colorer la carte.

    Reçoit : le tableau nettoyé.
    Renvoie : une Series de textes alignée sur df : "hors service", "vide" (0 vélo),
    "pleine" (0 borne libre) ou "disponible".
    """
    etat = pd.Series("disponible", index=df.index)
    etat[df["numdocksavailable"] == 0] = "pleine"
    etat[df["numbikesavailable"] == 0] = "vide"
    etat[~df["en_service"]] = "hors service"
    return etat


def stats_commune(df, nom):
    """Calcule les indicateurs Vélib d'une commune ou d'une zone.

    Reçoit : le tableau nettoyé (colonnes du contrat) et un nom de commune ou de zone
    (n'importe quelle casse, avec ou sans accents).
    Renvoie : dict avec
      - nb_stations : stations en service ;
      - velos_dispo : vélos disponibles dans ces stations ;
      - taux_remplissage : vélos / (vélos + bornes libres), en % ;
      - stations_vides : stations en service sans aucun vélo ;
      - pct_stations_vides : stations vides / stations en service, en % ;
      - velos_par_station : vélos disponibles / stations en service, arrondi à 0,1 ;
      - part_electriques : vélos électriques / vélos disponibles, en %.
    Les stations hors service (en_service faux) ne comptent pas.
    Lève CommuneIntrouvable (avec une suggestion) si le nom n'existe pas dans le tableau.
    """
    stations = stations_de(df, nom)
    if stations.empty:
        raise CommuneIntrouvable(nom, suggerer_zone(df, nom))

    en_service = stations[stations["en_service"]]
    nb_stations = len(en_service)
    velos = int(en_service["numbikesavailable"].sum())
    bornes_libres = int(en_service["numdocksavailable"].sum())
    vides = int((en_service["numbikesavailable"] == 0).sum())

    return {
        "nb_stations": nb_stations,
        "velos_dispo": velos,
        # Seules les bornes qui fonctionnent comptent (décision #4)
        "taux_remplissage": pourcentage(velos, velos + bornes_libres),
        "stations_vides": vides,
        "pct_stations_vides": pourcentage(vides, nb_stations),
        "velos_par_station": round(velos / nb_stations, 1) if nb_stations else 0.0,
        "part_electriques": pourcentage(int(en_service["ebike"].sum()), velos),
    }
