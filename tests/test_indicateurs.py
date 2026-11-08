"""Tests de stats_commune() sur les stations figées (résultats vérifiés à la main)."""
import pytest

from src.indicateurs import stats_commune


def test_paris(df_test):
    # En service : Lacépède - Monge (0 vélo), Lacépède - Linné (33), Saint-Sulpice (11).
    # Raspail - Bac est hors service : ignorée.
    # Taux : 44 / (44 + 22 + 17 + 6) = 44 / 89 = 49,4 %
    assert stats_commune(df_test, "Paris") == {
        "nb_stations": 3,
        "velos_dispo": 44,
        "taux_remplissage": 49.4,
        "stations_vides": 1,
    }


def test_montreuil(df_test):
    # 28 vélos / (28 + 50 bornes libres) = 35,9 %
    assert stats_commune(df_test, "Montreuil") == {
        "nb_stations": 2,
        "velos_dispo": 28,
        "taux_remplissage": 35.9,
        "stations_vides": 0,
    }


def test_nom_sans_accent_ni_majuscule(df_test):
    assert stats_commune(df_test, "  MONTREUIL ") == stats_commune(df_test, "Montreuil")


def test_seulement_hors_service(df_test):
    df = df_test[df_test["name"] == "Raspail - Bac"]
    assert stats_commune(df, "Paris") == {
        "nb_stations": 0, "velos_dispo": 0, "taux_remplissage": 0.0, "stations_vides": 0,
    }


def test_commune_introuvable(df_test):
    with pytest.raises(ValueError):
        stats_commune(df_test, "Lyon")
