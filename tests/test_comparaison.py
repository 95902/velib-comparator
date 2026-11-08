"""Tests de comparer() et bilan() : A gagne, B gagne, égalité."""
from src.comparaison import EGALITE, bilan, comparer
from src.indicateurs import stats_commune


def stats(nb, velos, taux, vides):
    return {"nb_stations": nb, "velos_dispo": velos, "taux_remplissage": taux, "stations_vides": vides}


def gagnants(lignes):
    return {ligne["indicateur"]: ligne["gagnant"] for ligne in lignes}


def test_a_gagne_tout():
    lignes = comparer(stats(10, 100, 50.0, 1), stats(5, 20, 10.0, 4), "A", "B")
    assert set(gagnants(lignes).values()) == {"A"}
    assert bilan(lignes, "A", "B") == "A"


def test_b_gagne_tout():
    lignes = comparer(stats(5, 20, 10.0, 4), stats(10, 100, 50.0, 1), "A", "B")
    assert set(gagnants(lignes).values()) == {"B"}
    assert bilan(lignes, "A", "B") == "B"


def test_egalite():
    lignes = comparer(stats(5, 20, 10.0, 2), stats(5, 20, 10.0, 2), "A", "B")
    assert set(gagnants(lignes).values()) == {EGALITE}
    assert bilan(lignes, "A", "B") == EGALITE


def test_stations_vides_moins_est_mieux():
    lignes = comparer(stats(5, 20, 10.0, 0), stats(5, 20, 10.0, 3), "A", "B")
    assert gagnants(lignes)["Stations vides"] == "A"


def test_valeurs_recopiees():
    ligne = comparer(stats(1, 2, 3.0, 4), stats(5, 6, 7.0, 8), "A", "B")[0]
    assert (ligne["valeur_a"], ligne["valeur_b"]) == (1, 5)


def test_paris_montreuil_donnees_test(df_test):
    lignes = comparer(stats_commune(df_test, "Paris"), stats_commune(df_test, "Montreuil"), "Paris", "Montreuil")
    assert gagnants(lignes) == {
        "Stations en service": "Paris",      # 3 contre 2
        "Vélos disponibles": "Paris",        # 44 contre 28
        "Taux de remplissage (%)": "Paris",  # 49,4 contre 35,9
        "Stations vides": "Montreuil",       # 1 contre 0
    }
    assert bilan(lignes, "Paris", "Montreuil") == "Paris"
