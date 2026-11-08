"""Effet de la météo (pluie, température) sur les vélos en station, d'après l'historique (issue #22).

L'API ne donne pas les trajets, seulement les vélos garés. On lit donc l'usage de façon indirecte :
- moins de gens roulent → plus de vélos restent en station → le taux de remplissage monte ;
- les gens préfèrent l'électrique → les électriques partent d'abord → la part d'électriques en station baisse.
"""
import pandas as pd

AVEC_PLUIE = "avec pluie"
SANS_PLUIE = "sans pluie"
# Tranches de température : bornes (en °C) et libellés
BORNES_TEMPERATURE = [-50, 5, 10, 15, 20, 60]
TRANCHES_TEMPERATURE = ["moins de 5 °C", "5 à 10 °C", "10 à 15 °C", "15 à 20 °C", "20 °C et plus"]


def par_releve(historique):
    """Résume chaque relevé de l'historique.

    Reçoit : l'historique de lire_historique() (une ligne par zone et par relevé).
    Renvoie : un DataFrame, une ligne par horodatage :
      - taux_moyen : moyenne des taux de remplissage des zones (%) ;
      - velos_dispo : total des vélos en station ;
      - part_electriques : électriques / vélos en station, toutes zones réunies (%) ;
      - pluie_mm, temperature_c ;
      - meteo : "avec pluie" si pluie_mm > 0, sinon "sans pluie" ;
      - creneau : jour (semaine ou week-end) et heure de Paris, ex. "semaine 08 h".
    Les relevés sans mesure de pluie sont écartés.
    """
    historique = historique.dropna(subset=["pluie_mm"]).copy()
    # part_electriques est un % par zone : on repasse en nombre de vélos pour faire le total
    historique["electriques"] = historique["velos_dispo"] * historique["part_electriques"] / 100
    releves = (
        historique.groupby("horodatage")
        .agg(
            taux_moyen=("taux_remplissage", "mean"),
            velos_dispo=("velos_dispo", "sum"),
            electriques=("electriques", "sum"),
            pluie_mm=("pluie_mm", "first"),
            temperature_c=("temperature_c", "first"),
        )
        .reset_index()
    )
    releves["taux_moyen"] = releves["taux_moyen"].round(1)
    releves["part_electriques"] = (100 * releves["electriques"] / releves["velos_dispo"]).round(1)
    releves = releves.drop(columns="electriques")
    releves["meteo"] = [AVEC_PLUIE if pluie > 0 else SANS_PLUIE for pluie in releves["pluie_mm"]]

    heure_paris = pd.to_datetime(releves["horodatage"], utc=True).dt.tz_convert("Europe/Paris")
    jour = ["week-end" if numero >= 5 else "semaine" for numero in heure_paris.dt.day_of_week]
    releves["creneau"] = [f"{j} {h:02d} h" for j, h in zip(jour, heure_paris.dt.hour)]
    return releves


def effet_pluie(historique):
    """Compare tous les relevés avec et sans pluie (sans tenir compte de l'heure).

    Reçoit : l'historique de lire_historique().
    Renvoie : un DataFrame indexé par "avec pluie" / "sans pluie" : nb_releves, taux_moyen (%),
    part_electriques (%), velos_dispo (moyenne par relevé). Une ligne manque si aucun relevé
    n'est dans ce cas.
    """
    return (
        par_releve(historique)
        .groupby("meteo")
        .agg(
            nb_releves=("horodatage", "count"),
            taux_moyen=("taux_moyen", "mean"),
            part_electriques=("part_electriques", "mean"),
            velos_dispo=("velos_dispo", "mean"),
        )
        .round(1)
    )


def effet_pluie_heure_egale(historique):
    """Compare pluie et temps sec à créneau égal (même heure, même type de jour).

    Reçoit : l'historique de lire_historique().
    Renvoie : un DataFrame, une ligne par créneau qui a des relevés avec ET sans pluie :
    taux_sans, taux_avec, ecart_taux, elec_sans, elec_avec, ecart_elec (en points de %),
    nb_avec, nb_sans. Vide si aucun créneau n'a les deux.
    Évite le piège : une station se vide le matin en semaine qu'il pleuve ou non.
    """
    moyennes = (
        par_releve(historique)
        .groupby(["creneau", "meteo"])
        .agg(taux=("taux_moyen", "mean"), elec=("part_electriques", "mean"), nb=("horodatage", "count"))
        .unstack("meteo")
        .dropna()  # on ne garde que les créneaux qui ont les deux météos
    )
    deux_meteos = {AVEC_PLUIE, SANS_PLUIE} <= set(moyennes.columns.get_level_values("meteo"))
    if moyennes.empty or not deux_meteos:
        return pd.DataFrame(columns=["taux_sans", "taux_avec", "ecart_taux", "elec_sans", "elec_avec", "ecart_elec", "nb_avec", "nb_sans"])
    resultat = pd.DataFrame({
        "taux_sans": moyennes[("taux", SANS_PLUIE)],
        "taux_avec": moyennes[("taux", AVEC_PLUIE)],
        "elec_sans": moyennes[("elec", SANS_PLUIE)],
        "elec_avec": moyennes[("elec", AVEC_PLUIE)],
        "nb_avec": moyennes[("nb", AVEC_PLUIE)].astype(int),
        "nb_sans": moyennes[("nb", SANS_PLUIE)].astype(int),
    })
    resultat["ecart_taux"] = resultat["taux_avec"] - resultat["taux_sans"]
    resultat["ecart_elec"] = resultat["elec_avec"] - resultat["elec_sans"]
    colonnes = ["taux_sans", "taux_avec", "ecart_taux", "elec_sans", "elec_avec", "ecart_elec", "nb_avec", "nb_sans"]
    return resultat[colonnes].round(1)


def effet_temperature(historique):
    """Regroupe les relevés par tranche de température.

    Reçoit : l'historique de lire_historique().
    Renvoie : un DataFrame indexé par tranche ("moins de 5 °C"…), seulement celles qui ont des
    relevés : nb_releves, taux_moyen (%), part_electriques (%).
    """
    releves = par_releve(historique).dropna(subset=["temperature_c"])
    releves["tranche"] = pd.cut(releves["temperature_c"], BORNES_TEMPERATURE, labels=TRANCHES_TEMPERATURE, right=False)
    return (
        releves.groupby("tranche", observed=True)
        .agg(nb_releves=("horodatage", "count"), taux_moyen=("taux_moyen", "mean"), part_electriques=("part_electriques", "mean"))
        .round(1)
    )


def sens(ecart, plus, moins):
    """Reçoit un écart et deux mots. Renvoie plus, moins ou « autant » selon le signe de l'écart."""
    return plus if ecart > 0 else moins if ecart < 0 else "autant"


def conclusion(historique):
    """Rédige la conclusion sur la pluie.

    Reçoit : l'historique de lire_historique().
    Renvoie : un texte. La comparaison à créneau égal est préférée ; sans elle, on donne la
    comparaison globale en prévenant qu'elle mélange les heures.
    """
    heure_egale = effet_pluie_heure_egale(historique)
    if not heure_egale.empty:
        poids = heure_egale["nb_avec"]  # un créneau souvent pluvieux compte davantage
        ecart_taux = round((heure_egale["ecart_taux"] * poids).sum() / poids.sum(), 1)
        ecart_elec = round((heure_egale["ecart_elec"] * poids).sum() / poids.sum(), 1)
        return (
            f"**À heure égale** ({len(heure_egale)} créneau(x) comparé(s)), quand il pleut, les stations sont "
            f"{sens(ecart_taux, 'plus', 'moins')} remplies ({ecart_taux:+} points) : "
            f"{sens(ecart_taux, 'moins', 'plus')} de vélos sont en circulation. "
            f"La part d'électriques en station est {sens(ecart_elec, 'plus haute', 'plus basse')} ({ecart_elec:+} points)"
            + (" : les électriques partent davantage sous la pluie." if ecart_elec < 0 else ".")
        )

    effet = effet_pluie(historique)
    if AVEC_PLUIE not in effet.index or SANS_PLUIE not in effet.index:
        return ("Pas encore de conclusion possible : il faut des relevés avec **et** sans pluie, "
                "si possible aux mêmes heures. Laisse tourner `python collecter.py` plusieurs jours.")
    ecart = round(effet.loc[AVEC_PLUIE, "taux_moyen"] - effet.loc[SANS_PLUIE, "taux_moyen"], 1)
    return (
        f"Tous relevés confondus, les stations sont {sens(ecart, 'plus', 'moins')} remplies quand il pleut "
        f"({ecart:+} points). ⚠️ Pas encore de relevés avec et sans pluie **à la même heure** : "
        "l'écart peut venir de l'heure de la journée plutôt que de la pluie."
    )
