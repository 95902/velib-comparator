"""Tests de l'analyse météo / usage sur un petit historique inventé."""
import pandas as pd

from src.analyse_pluie import (
    AVEC_PLUIE, SANS_PLUIE, conclusion, effet_pluie, effet_pluie_heure_egale, effet_temperature, par_releve,
)


def historique(*releves):
    """Chaque relevé : (heure UTC, pluie_mm, température, [taux zone a, taux zone b], part d'électriques)."""
    lignes = []
    for heure, pluie, temperature, taux, part in releves:
        for zone, valeur in zip(["a", "b"], taux):
            lignes.append({"horodatage": pd.Timestamp(heure, tz="UTC"), "zone": zone, "taux_remplissage": valeur,
                           "velos_dispo": 10, "part_electriques": part, "pluie_mm": pluie, "temperature_c": temperature})
    return pd.DataFrame(lignes)


# Mardi 10 et mercredi 11 novembre 2026 (semaine), 7 h UTC = 8 h à Paris
SEC_8H = ("2026-11-10 07:00", 0.0, 6.0, [40, 60], 40.0)
PLUIE_8H = ("2026-11-11 07:00", 0.8, 8.0, [60, 80], 30.0)
SEC_18H = ("2026-11-10 17:00", 0.0, 12.0, [20, 30], 50.0)


def test_par_releve():
    releves = par_releve(historique(SEC_8H, PLUIE_8H))
    assert releves["taux_moyen"].tolist() == [50.0, 70.0]
    assert releves["part_electriques"].tolist() == [40.0, 30.0]
    assert releves["meteo"].tolist() == [SANS_PLUIE, AVEC_PLUIE]
    assert releves["creneau"].tolist() == ["semaine 08 h", "semaine 08 h"]


def test_part_electriques_ponderee():
    # Zone a : 10 vélos dont 20 % électriques ; zone b : 30 vélos dont 60 % → 2 + 18 = 20 sur 40 = 50 %
    h = historique(SEC_8H)
    h.loc[h["zone"] == "a", "part_electriques"] = 20.0
    h.loc[h["zone"] == "b", ["velos_dispo", "part_electriques"]] = [30, 60.0]
    assert par_releve(h)["part_electriques"].tolist() == [50.0]


def test_week_end():
    # Samedi 14 novembre 2026, 9 h UTC = 10 h à Paris
    releves = par_releve(historique(("2026-11-14 09:00", 0.0, 8.0, [50, 50], 40.0)))
    assert releves["creneau"].tolist() == ["week-end 10 h"]


def test_effet_pluie_global():
    effet = effet_pluie(historique(SEC_8H, PLUIE_8H, SEC_18H))
    assert effet.loc[SANS_PLUIE, "nb_releves"] == 2
    assert effet.loc[SANS_PLUIE, "taux_moyen"] == 37.5   # (50 + 25) / 2
    assert effet.loc[AVEC_PLUIE, "taux_moyen"] == 70.0


def test_heure_egale():
    # Seul le créneau « semaine 08 h » a des relevés avec et sans pluie ; 18 h est ignoré
    resultat = effet_pluie_heure_egale(historique(SEC_8H, PLUIE_8H, SEC_18H))
    assert resultat.index.tolist() == ["semaine 08 h"]
    assert resultat.loc["semaine 08 h", "ecart_taux"] == 20.0    # 70 - 50
    assert resultat.loc["semaine 08 h", "ecart_elec"] == -10.0   # 30 - 40


def test_conclusion_heure_egale():
    texte = conclusion(historique(SEC_8H, PLUIE_8H, SEC_18H))
    assert "À heure égale" in texte
    assert "plus remplies (+20.0 points)" in texte
    assert "les électriques partent davantage sous la pluie" in texte


def test_conclusion_sans_meme_heure():
    # Pluie à 8 h, temps sec seulement à 18 h : on prévient que l'heure peut fausser
    texte = conclusion(historique(PLUIE_8H, SEC_18H))
    assert "Pas encore de relevés avec et sans pluie **à la même heure**" in texte


def test_pas_assez_de_donnees():
    assert "Pas encore de conclusion" in conclusion(historique(SEC_8H))
    assert effet_pluie_heure_egale(historique(SEC_8H)).empty


def test_temperature():
    effet = effet_temperature(historique(SEC_8H, PLUIE_8H, SEC_18H))
    assert effet.index.tolist() == ["5 à 10 °C", "10 à 15 °C"]
    assert effet.loc["5 à 10 °C", "nb_releves"] == 2
    assert effet.loc["5 à 10 °C", "taux_moyen"] == 60.0   # (50 + 70) / 2


def test_releve_sans_meteo_ecarte():
    h = historique(SEC_8H, ("2026-11-10 07:15", None, None, [40, 60], 40.0))
    assert len(par_releve(h)) == 1
