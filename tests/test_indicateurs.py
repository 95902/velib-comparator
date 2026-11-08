"""Tests de stats_commune() sur les stations figées (résultats vérifiés à la main)."""
import pytest

from src.indicateurs import etat_station, pourcentage, stats_commune


def test_paris(df_test):
    # En service : Lacépède - Monge (0 vélo), Lacépède - Linné (33 dont 13 électriques),
    # Saint-Sulpice (11 dont 9 électriques). Raspail - Bac est hors service : ignorée.
    assert stats_commune(df_test, "Paris") == {
        "nb_stations": 3,
        "velos_dispo": 44,
        "taux_remplissage": 49.4,     # 44 / (44 + 22 + 17 + 6) = 44 / 89
        "stations_vides": 1,
        "pct_stations_vides": 33.3,   # 1 / 3
        "velos_par_station": 14.7,    # 44 / 3
        "part_electriques": 50.0,     # 22 / 44
    }


def test_montreuil(df_test):
    assert stats_commune(df_test, "Montreuil") == {
        "nb_stations": 2,
        "velos_dispo": 28,
        "taux_remplissage": 35.9,     # 28 / 78
        "stations_vides": 0,
        "pct_stations_vides": 0.0,
        "velos_par_station": 14.0,
        "part_electriques": 82.1,     # 23 / 28
    }


def test_arrondissement(df_test):
    # Paris 5 : Lacépède - Monge et Lacépède - Linné seulement
    stats = stats_commune(df_test, "Paris 5")
    assert (stats["nb_stations"], stats["velos_dispo"], stats["stations_vides"]) == (2, 33, 1)
    assert stats["taux_remplissage"] == 45.8   # 33 / 72


def test_nom_sans_accent_ni_majuscule(df_test):
    assert stats_commune(df_test, "  MONTREUIL ") == stats_commune(df_test, "Montreuil")
    assert stats_commune(df_test, "paris  5") == stats_commune(df_test, "Paris 5")


def test_seulement_hors_service(df_test):
    # Paris 7 n'a que Raspail - Bac, hors service : tout vaut 0, sans division par zéro
    assert set(stats_commune(df_test, "Paris 7").values()) == {0}


def test_commune_introuvable(df_test):
    with pytest.raises(ValueError):
        stats_commune(df_test, "Lyon")


def test_pourcentage():
    assert pourcentage(1, 3) == 33.3
    assert pourcentage(5, 0) == 0.0


def test_etat_station(df_test):
    etats = dict(zip(df_test["name"], etat_station(df_test)))
    assert etats["Lacépède - Monge"] == "vide"
    assert etats["Raspail - Bac"] == "hors service"   # 0 vélo, mais hors service d'abord
    assert etats["Saint-Sulpice"] == "disponible"


def test_etat_station_par_type(df_test):
    # Lacépède - Linné : 20 mécaniques, 13 électriques ; Saint-Sulpice : 2 et 9
    df = df_test.copy()
    df.loc[df["name"] == "Saint-Sulpice", "ebike"] = 0
    etats = dict(zip(df["name"], etat_station(df, "ebike")))
    assert etats["Saint-Sulpice"] == "vide"          # plus d'électrique, même s'il reste des mécaniques
    assert etats["Lacépède - Linné"] == "disponible"
    assert dict(zip(df["name"], etat_station(df)))["Saint-Sulpice"] == "disponible"
