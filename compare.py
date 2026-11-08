"""Compare la disponibilité Vélib de deux communes dans le terminal.

Lance : python compare.py Paris Montreuil
        python compare.py "Paris 11" Montreuil   (arrondissements : "Paris 1" à "Paris 20")
"""
import argparse

from rich.console import Console
from rich.table import Table

from src.comparaison import EGALITE, bilan, comparer
from src.indicateurs import stats_commune
from src.nettoyage import nettoyer_velib
from src.recuperation import telecharger_velib


def lire_arguments():
    """Reçoit : rien (lit la ligne de commande). Renvoie : les deux noms de communes."""
    parser = argparse.ArgumentParser(description="Compare les Vélib de deux communes.")
    parser.add_argument("commune_a", help='première commune ou arrondissement, ex. Paris ou "Paris 11"')
    parser.add_argument("commune_b", help='seconde commune ou arrondissement, ex. Montreuil')
    return parser.parse_args()


def afficher(lignes, nom_a, nom_b):
    """Reçoit : la liste renvoyée par comparer() et les deux noms. Affiche le tableau rich."""
    table = Table(title=f"🚲 Vélib : {nom_a} contre {nom_b}")
    table.add_column("Indicateur")
    table.add_column(nom_a, justify="right")
    table.add_column(nom_b, justify="right")
    table.add_column("Gagnant", style="bold")
    for ligne in lignes:
        # La valeur gagnante est en vert
        valeur_a = f"[green]{ligne['valeur_a']}[/green]" if ligne["gagnant"] == nom_a else str(ligne["valeur_a"])
        valeur_b = f"[green]{ligne['valeur_b']}[/green]" if ligne["gagnant"] == nom_b else str(ligne["valeur_b"])
        table.add_row(ligne["indicateur"], valeur_a, valeur_b, ligne["gagnant"])

    console = Console()
    console.print(table)
    gagnant = bilan(lignes, nom_a, nom_b)
    console.print("Résultat : égalité" if gagnant == EGALITE else f"Résultat : [bold green]{gagnant}[/bold green] gagne")


def main():
    args = lire_arguments()
    df, _ = nettoyer_velib(telecharger_velib())
    lignes = comparer(
        stats_commune(df, args.commune_a),
        stats_commune(df, args.commune_b),
        args.commune_a,
        args.commune_b,
    )
    afficher(lignes, args.commune_a, args.commune_b)


if __name__ == "__main__":
    main()
