"""Comparaison de deux communes, indicateur par indicateur."""

EGALITE = "Égalité"

# Pour chaque indicateur de stats_commune() : (libellé affiché, True si « plus » est meilleur)
INDICATEURS = {
    "nb_stations": ("Stations en service", True),
    "velos_dispo": ("Vélos disponibles", True),
    "taux_remplissage": ("Taux de remplissage (%)", True),
    "stations_vides": ("Stations vides", False),
}


def comparer(stats_a, stats_b, nom_a, nom_b):
    """Désigne le gagnant de chaque indicateur.

    Reçoit : deux dicts renvoyés par stats_commune() et les noms des deux communes.
    Renvoie : une liste de dicts, un par indicateur, avec les clés
      indicateur (libellé), valeur_a, valeur_b, gagnant (nom_a, nom_b ou EGALITE).
    """
    lignes = []
    for cle, (libelle, plus_est_mieux) in INDICATEURS.items():
        valeur_a, valeur_b = stats_a[cle], stats_b[cle]
        if valeur_a == valeur_b:
            gagnant = EGALITE
        elif (valeur_a > valeur_b) == plus_est_mieux:
            gagnant = nom_a
        else:
            gagnant = nom_b
        lignes.append({"indicateur": libelle, "valeur_a": valeur_a, "valeur_b": valeur_b, "gagnant": gagnant})
    return lignes


def bilan(lignes, nom_a, nom_b):
    """Donne le gagnant global : la commune qui gagne le plus d'indicateurs.

    Reçoit : la liste renvoyée par comparer() et les deux noms.
    Renvoie : nom_a, nom_b ou EGALITE.
    """
    victoires_a = sum(ligne["gagnant"] == nom_a for ligne in lignes)
    victoires_b = sum(ligne["gagnant"] == nom_b for ligne in lignes)
    if victoires_a == victoires_b:
        return EGALITE
    return nom_a if victoires_a > victoires_b else nom_b
