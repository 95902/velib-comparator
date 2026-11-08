"""Tests de normaliser() et nettoyer_velib() sur un petit tableau brut inventé."""
import pandas as pd
import pytest

from src.nettoyage import COLONNES_CONTRAT, nettoyer_velib, normaliser, zone_station, zones_disponibles


def station(code, commune="Paris", installee="OUI", pret="OUI", capacite=20, velos=5, bornes=15):
    """Une ligne au format brut de l'API (comme telecharger_velib())."""
    return {
        "stationcode": code, "name": f"Station {code}",
        "is_installed": installee, "is_renting": pret, "is_returning": pret,
        "capacity": capacite, "numdocksavailable": bornes, "numbikesavailable": velos,
        "mechanical": velos, "ebike": 0,
        "duedate": "2026-11-06T10:42:40+00:00",
        "nom_arrondissement_communes": commune, "code_insee_commune": 75056,
        "station_opening_hours": None,
        "coordonnees_geo.lon": 2.35, "coordonnees_geo.lat": 48.85,
    }


@pytest.fixture
def brut():
    return pd.DataFrame([
        station("1001"),
        station("1001"),                          # doublon
        station("2002", pret="NON"),              # hors service
        station("3003", installee="NON", pret="NON", capacite=0, velos=0, bornes=0),  # non installée
        station("31022", commune="Montreuil"),
    ])


@pytest.mark.parametrize("texte, attendu", [
    ("Montreuil", "montreuil"),
    ("  CRÉTEIL ", "creteil"),
    ("Saint-Denis", "saint denis"),
    ("L'Île-Saint-Denis", "l ile saint denis"),
    ("Paris  11", "paris 11"),
])
def test_normaliser(texte, attendu):
    assert normaliser(texte) == attendu


def test_doublons_supprimes(brut):
    df, rapport = nettoyer_velib(brut)
    assert df["stationcode"].is_unique
    assert rapport["doublons_retires"] == 1
    assert len(df) == rapport["stations_finales"] == 4


def test_hors_service_gardees_mais_marquees(brut):
    df, rapport = nettoyer_velib(brut)
    en_service = dict(zip(df["stationcode"], df["en_service"]))
    assert en_service == {"1001": True, "2002": False, "3003": False, "31022": True}
    assert rapport["hors_service"] == 2


def test_capacite_nulle_jamais_en_service(brut):
    brut.loc[0, "capacity"] = 0  # installée et ouverte, mais 0 borne
    df, rapport = nettoyer_velib(brut)
    assert not df.loc[df["capacity"] == 0, "en_service"].any()
    assert rapport["capacite_nulle"] == 2


def test_colonnes_et_types(brut):
    brut["stationcode"] = [1001, 1001, 2002, 3003, 31022]  # comme un CSV relu sans dtype
    df, _ = nettoyer_velib(brut)
    assert list(df.columns) == COLONNES_CONTRAT
    assert df["stationcode"].tolist() == ["1001", "2002", "3003", "31022"]
    assert df["capacity"].dtype.kind == "i"
    assert df.loc[3, "commune_norm"] == "montreuil"


@pytest.mark.parametrize("code, commune, attendu", [
    ("10202", "paris", "paris 10"),
    ("3012", "paris", "paris 3"),
    ("20106", "paris", "paris 20"),
    ("60001", "paris", "paris"),        # Invalides - Quai d'Orsay : hors règle
    ("31022", "montreuil", "montreuil"),
])
def test_zone_station(code, commune, attendu):
    assert zone_station(code, commune) == attendu


def test_zone_dans_le_tableau(brut):
    df, _ = nettoyer_velib(brut)
    assert dict(zip(df["stationcode"], df["zone"])) == {
        "1001": "paris 1", "2002": "paris 2", "3003": "paris 3", "31022": "montreuil",
    }
    assert zones_disponibles(df) == ["Montreuil", "Paris", "Paris 1", "Paris 2", "Paris 3"]


def test_brut_inchange(brut):
    copie = brut.copy()
    nettoyer_velib(brut)
    pd.testing.assert_frame_equal(brut, copie)


def test_vraies_donnees():
    """Le CSV brut du dépôt (data/brut/velib.csv) se nettoie sans erreur."""
    from src.recuperation import CHEMIN_BRUT

    df, rapport = nettoyer_velib(pd.read_csv(CHEMIN_BRUT, dtype={"stationcode": str}))
    assert rapport["stations_finales"] == len(df) > 1000
    assert df["stationcode"].is_unique
    assert not df.loc[df["capacity"] == 0, "en_service"].any()
