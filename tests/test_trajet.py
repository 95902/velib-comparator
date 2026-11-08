"""Tests de distance_m(), station_conseillee() et charger_utilisateurs()."""
import pandas as pd
import pytest

from src import recuperation
from src.trajet import distance_m, station_conseillee, stations_proches

# Coordonnées des stations figées (tests/donnees_test.csv)
MONGE = (48.843893, 2.351966)        # Lacépède - Monge : vide
RASPAIL_BAC = (48.855629, 2.32566)   # hors service
SAINT_SULPICE = (48.851654, 2.330808)


def test_distance_meme_point():
    assert distance_m(48.85, 2.35, 48.85, 2.35) == 0


def test_distance_connue():
    # Un degré de latitude fait environ 111,2 km
    assert distance_m(48.0, 2.35, 49.0, 2.35) == pytest.approx(111_195, rel=1e-3)
    # Notre-Dame → tour Eiffel : environ 4,1 km
    assert distance_m(48.8530, 2.3499, 48.8584, 2.2945) == pytest.approx(4_100, rel=0.02)


def test_prendre_un_velo_a_cote(df_test):
    station = station_conseillee(df_test, *SAINT_SULPICE, "velo")
    assert (station["name"], station["distance_m"], station["nombre"]) == ("Saint-Sulpice", 0, 11)
    assert (station["mechanical"], station["ebike"]) == (2, 9)


def test_station_vide_ignoree(df_test):
    # Lacépède - Monge n'a aucun vélo : on va à Lacépède - Linné, à environ 200 m
    station = station_conseillee(df_test, *MONGE, "velo")
    assert station["name"] == "Lacépède - Linné"
    assert 150 < station["distance_m"] < 250


def test_station_hors_service_ignoree(df_test):
    # Raspail - Bac a 52 bornes libres mais est hors service
    station = station_conseillee(df_test, *RASPAIL_BAC, "borne")
    assert station["name"] == "Saint-Sulpice"


def test_egalite_de_distance(df_test):
    # Deux stations au même endroit : celle qui a le plus de vélos gagne
    jumelle = df_test[df_test["name"] == "Saint-Sulpice"].assign(name="Jumelle", numbikesavailable=3, numdocksavailable=20)
    df = pd.concat([jumelle, df_test], ignore_index=True)
    assert station_conseillee(df, *SAINT_SULPICE, "velo")["name"] == "Saint-Sulpice"   # 11 vélos contre 3
    assert station_conseillee(df, *SAINT_SULPICE, "borne")["name"] == "Jumelle"        # 20 bornes contre 6


def test_aucune_station(df_test):
    assert station_conseillee(df_test[~df_test["en_service"]], *RASPAIL_BAC, "borne") is None


def test_besoin_inconnu(df_test):
    with pytest.raises(ValueError):
        station_conseillee(df_test, *MONGE, "trottinette")


def test_charger_utilisateurs():
    utilisateurs = recuperation.charger_utilisateurs()
    assert len(utilisateurs) == 3
    for utilisateur in utilisateurs:
        assert len(utilisateur["lieux"]) >= 2
        for lieu in utilisateur["lieux"].values():
            assert set(lieu) == {"lat", "lon"}


def test_utilisateurs_absents(monkeypatch, tmp_path):
    monkeypatch.setattr(recuperation, "CHEMIN_UTILISATEURS", tmp_path / "absent.json")
    with pytest.raises(FileNotFoundError, match="utilisateurs"):
        recuperation.charger_utilisateurs()


def test_stations_proches(df_test):
    # Autour de Lacépède - Monge : elle-même (0 m) puis Lacépède - Linné (~200 m)
    proches = stations_proches(df_test, *MONGE, rayon_m=500)
    assert proches["name"].tolist() == ["Lacépède - Monge", "Lacépède - Linné"]
    assert proches["distance_m"].iloc[0] == 0
    # Saint-Sulpice et Raspail - Bac (hors service) sont dans un rayon de 2 km
    assert len(stations_proches(df_test, *SAINT_SULPICE, rayon_m=2000)) == 4


def test_type_de_velo(df_test):
    # Près de Saint-Sulpice : 2 mécaniques et 9 électriques
    electrique = station_conseillee(df_test, *SAINT_SULPICE, "velo", "electrique")
    assert (electrique["name"], electrique["nombre"]) == ("Saint-Sulpice", 9)
    mecanique = station_conseillee(df_test, *SAINT_SULPICE, "velo", "mecanique")
    assert (mecanique["name"], mecanique["nombre"]) == ("Saint-Sulpice", 2)


def test_station_sans_le_type_voulu_ignoree(df_test):
    # Saint-Sulpice n'a plus d'électrique : on va à la plus proche qui en a (Lacépède - Linné)
    df = df_test.copy()
    df.loc[df["name"] == "Saint-Sulpice", "ebike"] = 0
    assert station_conseillee(df, *SAINT_SULPICE, "velo", "electrique")["name"] == "Lacépède - Linné"
    assert station_conseillee(df, *SAINT_SULPICE, "velo")["name"] == "Saint-Sulpice"


def test_type_ignore_pour_les_bornes(df_test):
    assert station_conseillee(df_test, *SAINT_SULPICE, "borne", "electrique") == station_conseillee(df_test, *SAINT_SULPICE, "borne")


def test_type_inconnu(df_test):
    with pytest.raises(ValueError):
        station_conseillee(df_test, *SAINT_SULPICE, "velo", "tandem")
