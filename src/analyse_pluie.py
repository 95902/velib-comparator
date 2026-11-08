"""Analyse « effet de la pluie sur le remplissage » à partir de l'historique (issue #22)."""

AVEC_PLUIE = "avec pluie"
SANS_PLUIE = "sans pluie"


def par_releve(historique):
    """Résume chaque relevé de l'historique.

    Reçoit : l'historique de lire_historique() (une ligne par zone et par relevé).
    Renvoie : un DataFrame, une ligne par horodatage : taux_moyen (moyenne des zones, en %),
    velos_dispo (total), pluie_mm, et meteo ("avec pluie" si pluie_mm > 0, sinon "sans pluie").
    Les relevés sans mesure de pluie sont écartés.
    """
    releves = (
        historique.dropna(subset=["pluie_mm"])
        .groupby("horodatage")
        .agg(taux_moyen=("taux_remplissage", "mean"), velos_dispo=("velos_dispo", "sum"), pluie_mm=("pluie_mm", "first"))
        .reset_index()
    )
    releves["taux_moyen"] = releves["taux_moyen"].round(1)
    releves["meteo"] = [AVEC_PLUIE if pluie > 0 else SANS_PLUIE for pluie in releves["pluie_mm"]]
    return releves


def effet_pluie(historique):
    """Compare les relevés avec et sans pluie.

    Reçoit : l'historique de lire_historique().
    Renvoie : un DataFrame indexé par "avec pluie" / "sans pluie" : nb_releves, taux_moyen (%),
    velos_dispo (moyenne par relevé). Une ligne manque si aucun relevé n'est dans ce cas.
    """
    return (
        par_releve(historique)
        .groupby("meteo")
        .agg(nb_releves=("horodatage", "count"), taux_moyen=("taux_moyen", "mean"), velos_dispo=("velos_dispo", "mean"))
        .round(1)
    )


def conclusion(effet):
    """Reçoit : le DataFrame de effet_pluie(). Renvoie : une phrase de conclusion."""
    if AVEC_PLUIE not in effet.index or SANS_PLUIE not in effet.index:
        return ("Pas encore de conclusion possible : il faut des relevés avec **et** sans pluie. "
                "Laisse tourner python collecter.py plusieurs jours.")
    sans, avec = effet.loc[SANS_PLUIE, "taux_moyen"], effet.loc[AVEC_PLUIE, "taux_moyen"]
    ecart = round(avec - sans, 1)
    sens = "plus remplies" if ecart > 0 else "moins remplies" if ecart < 0 else "aussi remplies"
    return (
        f"Quand il pleut, les stations sont {sens} : taux moyen de {avec} % contre {sans} % sans pluie "
        f"(écart de {ecart:+} points), sur {int(effet['nb_releves'].sum())} relevés. "
        "Attention : l'heure de la journée joue aussi, il faut beaucoup de relevés pour conclure."
    )
