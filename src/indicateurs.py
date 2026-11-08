"""Calcul des indicateurs d'une commune à partir du tableau nettoyé."""
from src.nettoyage import normaliser


def stats_commune(df, nom):
    """Calcule les indicateurs Vélib d'une commune.

    Reçoit : le tableau nettoyé (colonnes du contrat) et un nom de commune
    (n'importe quelle casse, avec ou sans accents).
    Renvoie : dict avec
      - nb_stations : stations en service ;
      - velos_dispo : vélos disponibles dans ces stations ;
      - taux_remplissage : vélos / (vélos + bornes libres), en %, arrondi à 0,1 ;
      - stations_vides : stations en service sans aucun vélo.
    Les stations hors service (en_service faux) ne comptent pas.
    Lève ValueError si la commune n'existe pas dans le tableau.
    """
    nom_norm = normaliser(nom)
    commune = df[df["commune_norm"] == nom_norm]
    if commune.empty:
        raise ValueError(f"Commune introuvable : {nom}")

    en_service = commune[commune["en_service"]]
    velos = int(en_service["numbikesavailable"].sum())
    bornes_libres = int(en_service["numdocksavailable"].sum())
    # Seules les bornes qui fonctionnent comptent (décision #4) ; 0 station → 0 %
    places = velos + bornes_libres
    taux = round(100 * velos / places, 1) if places else 0.0

    return {
        "nb_stations": len(en_service),
        "velos_dispo": velos,
        "taux_remplissage": taux,
        "stations_vides": int((en_service["numbikesavailable"] == 0).sum()),
    }
