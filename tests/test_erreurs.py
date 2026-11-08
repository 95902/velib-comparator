"""Tests de la gestion des erreurs : pas d'internet, commune introuvable."""
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
    csv.write_text("stationcode,name\n01001,Station test\n", encoding="utf-8")
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
