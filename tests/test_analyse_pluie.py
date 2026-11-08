"""Tests de l'analyse « effet de la pluie » sur un petit historique inventé."""
import pandas as pd

from src.analyse_pluie import AVEC_PLUIE, SANS_PLUIE, conclusion, effet_pluie, par_releve


def historique(*releves):
    """Chaque relevé : (heure, pluie_mm, [taux de la zone a, taux de la zone b])."""
    lignes = []
    for heure, pluie, taux in releves:
        for zone, valeur in zip(["a", "b"], taux):
            lignes.append({"horodatage": pd.Timestamp(heure, tz="UTC"), "zone": zone,
                           "taux_remplissage": valeur, "velos_dispo": 10, "pluie_mm": pluie})
    return pd.DataFrame(lignes)


def test_par_releve():
    releves = par_releve(historique(("2026-11-08 10:00", 0.0, [40, 60]), ("2026-11-08 10:15", 0.4, [70, 90])))
    assert releves["taux_moyen"].tolist() == [50.0, 80.0]
    assert releves["meteo"].tolist() == [SANS_PLUIE, AVEC_PLUIE]
    assert releves["velos_dispo"].tolist() == [20, 20]


def test_effet_et_conclusion():
    effet = effet_pluie(historique(
        ("2026-11-08 10:00", 0.0, [40, 60]),
        ("2026-11-08 10:15", 0.0, [50, 70]),
        ("2026-11-08 10:30", 1.2, [70, 90]),
    ))
    assert effet.loc[SANS_PLUIE, "nb_releves"] == 2
    assert effet.loc[SANS_PLUIE, "taux_moyen"] == 55.0
    assert effet.loc[AVEC_PLUIE, "taux_moyen"] == 80.0
    assert "plus remplies" in conclusion(effet)
    assert "+25.0 points" in conclusion(effet)


def test_pas_assez_de_donnees():
    effet = effet_pluie(historique(("2026-11-08 10:00", 0.0, [40, 60])))
    assert "Pas encore de conclusion" in conclusion(effet)


def test_releve_sans_meteo_ecarte():
    h = historique(("2026-11-08 10:00", None, [40, 60]), ("2026-11-08 10:15", 0.0, [50, 50]))
    assert len(par_releve(h)) == 1
