"""Tests de comparer() et bilan() : A gagne, B gagne, égalité."""
from src.comparaison import EGALITE, INDICATEURS, bilan, comparer
from src.indicateurs import stats_commune

# Une commune « bonne » et une « mauvaise » sur tous les indicateurs
BONNE = {"nb_stations": 10, "velos_dispo": 100, "taux_remplissage": 50.0, "stations_vides": 1,
         "pct_stations_vides": 10.0, "velos_par_station": 10.0, "part_electriques": 40.0}
MAUVAISE = {"nb_stations": 5, "velos_dispo": 20, "taux_remplissage": 10.0, "stations_vides": 4,
            "pct_stations_vides": 80.0, "velos_par_station": 4.0, "part_electriques": 20.0}


def gagnants(lignes):
    return {ligne["indicateur"]: ligne["gagnant"] for ligne in lignes}


def test_une_ligne_par_indicateur():
    assert len(comparer(BONNE, MAUVAISE, "A", "B")) == len(INDICATEURS)


def test_a_gagne_tout():
    lignes = comparer(BONNE, MAUVAISE, "A", "B")
    assert set(gagnants(lignes).values()) == {"A"}
    assert bilan(lignes, "A", "B") == "A"


def test_b_gagne_tout():
    lignes = comparer(MAUVAISE, BONNE, "A", "B")
    assert set(gagnants(lignes).values()) == {"B"}
    assert bilan(lignes, "A", "B") == "B"


def test_egalite():
    lignes = comparer(BONNE, dict(BONNE), "A", "B")
    assert set(gagnants(lignes).values()) == {EGALITE}
    assert bilan(lignes, "A", "B") == EGALITE


def test_moins_de_stations_vides_est_mieux():
    lignes = comparer(dict(MAUVAISE, stations_vides=0, pct_stations_vides=0.0), MAUVAISE, "A", "B")
    assert gagnants(lignes)["Stations vides"] == "A"
    assert gagnants(lignes)["Stations vides (%)"] == "A"
    assert gagnants(lignes)["Vélos disponibles"] == EGALITE


def test_valeurs_recopiees():
    ligne = comparer(BONNE, MAUVAISE, "A", "B")[0]
    assert (ligne["valeur_a"], ligne["valeur_b"]) == (10, 5)


def test_paris_montreuil_donnees_test(df_test):
    lignes = comparer(stats_commune(df_test, "Paris"), stats_commune(df_test, "Montreuil"), "Paris", "Montreuil")
    assert gagnants(lignes) == {
        "Stations en service": "Paris",          # 3 contre 2
        "Vélos disponibles": "Paris",            # 44 contre 28
        "Taux de remplissage (%)": "Paris",      # 49,4 contre 35,9
        "Stations vides": "Montreuil",           # 1 contre 0
        "Stations vides (%)": "Montreuil",       # 33,3 contre 0
        "Vélos par station": "Paris",            # 14,7 contre 14,0
        "Part d'électriques (%)": "Montreuil",   # 50,0 contre 82,1
    }
    assert bilan(lignes, "Paris", "Montreuil") == "Paris"  # 4 indicateurs contre 3
