"""Tests de la gestion des erreurs : pas d'internet, réponse vide, commune introuvable."""
import pandas as pd
import pytest
import requests

import compare
from src import recuperation
from src.indicateurs import stats_commune
from src.nettoyage import CommuneIntrouvable, suggerer_zone


def pas_d_internet(*args, **kwargs):
    raise requests.ConnectionError("pas de réseau")


@pytest.mark.parametrize("tape, attendu", [
    ("montreuill", "Montreuil"),
    ("MONTREIL", "Montreuil"),
    ("paris 55", "Paris 5"),
    ("Lyon", None),
])
def test_suggestion(df_test, tape, attendu):
    assert suggerer_zone(df_test, tape) == attendu


def test_commune_introuvable_avec_suggestion(df_test):
    with pytest.raises(CommuneIntrouvable, match="Vouliez-vous dire Montreuil ?") as erreur:
        stats_commune(df_test, "montreuill")
    assert erreur.value.suggestion == "Montreuil"


def test_commune_introuvable_sans_suggestion(df_test):
    with pytest.raises(CommuneIntrouvable) as erreur:
        stats_commune(df_test, "Lyon")
    assert "Vouliez-vous dire" not in str(erreur.value)


def test_repli_sur_le_dernier_csv(monkeypatch, tmp_path):
    csv = tmp_path / "velib.csv"
    pd.DataFrame([station_brute()]).to_csv(csv, index=False)
    monkeypatch.setattr(recuperation, "CHEMIN_BRUT", csv)
    monkeypatch.setattr(recuperation.requests, "get", pas_d_internet)
    df, en_direct = recuperation.charger_velib_brut()
    assert en_direct is False
    assert df.loc[0, "stationcode"] == "01001"  # relu en texte


def test_ni_internet_ni_csv(monkeypatch, tmp_path):
    monkeypatch.setattr(recuperation, "CHEMIN_BRUT", tmp_path / "absent.csv")
    monkeypatch.setattr(recuperation.requests, "get", pas_d_internet)
    with pytest.raises(recuperation.DonneesIndisponibles):
        recuperation.charger_velib_brut()


def test_compare_message_clair(monkeypatch, capsys, df_test):
    monkeypatch.setattr(compare, "charger_velib_brut", lambda: (None, True))
    monkeypatch.setattr(compare, "nettoyer_velib", lambda df_brut: (df_test, {}))
    monkeypatch.setattr("sys.argv", ["compare.py", "Paris", "montreuill"])
    with pytest.raises(SystemExit) as sortie:
        compare.main()
    assert sortie.value.code == 1
    assert "Vouliez-vous dire Montreuil ?" in capsys.readouterr().err


def station_brute(code="01001"):
    return {"stationcode": code, "name": "Station test", "nom_arrondissement_communes": "Paris",
            "coordonnees_geo.lat": 48.85, "coordonnees_geo.lon": 2.35}


def test_verifier_velib_ok():
    recuperation.verifier_velib(pd.DataFrame([station_brute(), station_brute("01002")]))


def test_reponse_vide_rejetee():
    # Panne du 8 novembre 2026 : toutes les stations arrivent sans code ni position
    cassee = pd.DataFrame([dict(station_brute(), stationcode=None, **{"coordonnees_geo.lat": None})] * 3)
    with pytest.raises(recuperation.ReponseVelibInvalide):
        recuperation.verifier_velib(cassee)
    with pytest.raises(recuperation.ReponseVelibInvalide, match="colonnes absentes"):
        recuperation.verifier_velib(pd.DataFrame([{"stationcode": "1"}]))


class FausseReponse:
    def raise_for_status(self):
        pass

    def json(self):
        return [{"stationcode": None, "name": None, "coordonnees_geo": None,
                 "nom_arrondissement_communes": None, "numbikesavailable": 5}]


def test_reponse_vide_ne_remplace_pas_le_csv(monkeypatch, tmp_path):
    csv = tmp_path / "velib.csv"
    pd.DataFrame([station_brute()]).to_csv(csv, index=False)
    monkeypatch.setattr(recuperation, "CHEMIN_BRUT", csv)
    monkeypatch.setattr(recuperation.requests, "get", lambda *args, **kwargs: FausseReponse())
    df, en_direct = recuperation.charger_velib_brut()
    assert en_direct is False
    assert df.loc[0, "stationcode"] == "01001"                                 # repli sur le bon CSV
    assert pd.read_csv(csv, dtype={"stationcode": str}).loc[0, "stationcode"] == "01001"  # pas écrasé


def test_csv_de_secours_casse(monkeypatch, tmp_path):
    csv = tmp_path / "velib.csv"
    pd.DataFrame([dict(station_brute(), stationcode=None)]).to_csv(csv, index=False)
    monkeypatch.setattr(recuperation, "CHEMIN_BRUT", csv)
    monkeypatch.setattr(recuperation.requests, "get", pas_d_internet)
    with pytest.raises(recuperation.DonneesIndisponibles):
        recuperation.charger_velib_brut()
