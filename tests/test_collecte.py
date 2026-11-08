"""Tests de la collecte de l'historique (sans appel réseau)."""
import pandas as pd

from src.collecte import ajouter_a_historique, lire_historique, releve_zones

HEURE = pd.Timestamp("2026-11-08T10:00:00Z")
METEO = {"temperature_c": 4.2, "vent_kmh": 5.8, "pluie_mm": 0.3, "heure_releve": HEURE}


def test_une_ligne_par_zone(df_test):
    releve = releve_zones(df_test, METEO, HEURE)
    assert releve["zone"].tolist() == ["montreuil", "paris 5", "paris 6", "paris 7"]
    montreuil = releve.iloc[0]
    assert (montreuil["velos_dispo"], montreuil["taux_remplissage"], montreuil["pluie_mm"]) == (28, 35.9, 0.3)


def test_sans_meteo(df_test):
    releve = releve_zones(df_test, None, HEURE)
    assert releve["pluie_mm"].isna().all()


def test_historique_ajoute_sans_ecraser(df_test, tmp_path):
    chemin = tmp_path / "historique" / "releves.csv"
    assert lire_historique(chemin) is None
    ajouter_a_historique(releve_zones(df_test, METEO, HEURE), chemin)
    ajouter_a_historique(releve_zones(df_test, METEO, HEURE + pd.Timedelta(minutes=15)), chemin)
    historique = lire_historique(chemin)
    assert len(historique) == 8
    assert historique["horodatage"].nunique() == 2
