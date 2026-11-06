"""Exploration du CSV brut Vélib, avant d'écrire le nettoyage.

Lance : python explorer_velib.py
Lit data/brut/velib.csv (créé par telecharger_velib()) et affiche les constats
à partager dans l'issue #5. Ne modifie aucun fichier.
"""
import pandas as pd

from src.recuperation import CHEMIN_BRUT


def titre(texte):
    """Affiche un titre de section pour rendre la sortie lisible."""
    print(f"\n=== {texte} ===")


df = pd.read_csv(CHEMIN_BRUT, dtype={"stationcode": str})

titre("Taille et colonnes")
print(f"{len(df)} stations, {len(df.columns)} colonnes")
df.info()

titre("Valeurs manquantes (colonnes concernées)")
manquantes = df.isna().sum()
print(manquantes[manquantes > 0])

titre("Doublons")
print("Lignes identiques :", df.duplicated().sum())
print("stationcode en double :", df.duplicated("stationcode").sum())

titre("Stations hors service")
for colonne in ["is_installed", "is_renting", "is_returning"]:
    print(colonne, df[colonne].value_counts().to_dict())
hors_service = (df["is_installed"] != "OUI") | (df["is_renting"] != "OUI") | (df["is_returning"] != "OUI")
print("Au moins un des trois à NON :", hors_service.sum())

titre("Capacités")
print("Capacité nulle :", (df["capacity"] == 0).sum())
print(df["capacity"].describe())

titre("Vélos + bornes libres comparés à la capacité")
somme = df["numbikesavailable"] + df["numdocksavailable"]
print("Égal à capacity :", (somme == df["capacity"]).sum())
print("Inférieur (bornes hors service) :", (somme < df["capacity"]).sum())
print("Supérieur :", (somme > df["capacity"]).sum())

titre("Vélos mécaniques + électriques comparés aux vélos disponibles")
print("Différent :", (df["mechanical"] + df["ebike"] != df["numbikesavailable"]).sum())

titre("Stations vides et pleines")
print("Vides (0 vélo) :", (df["numbikesavailable"] == 0).sum())
print("Pleines (0 borne libre) :", (df["numdocksavailable"] == 0).sum())

titre("Communes")
communes = df["nom_arrondissement_communes"].value_counts()
print(f"{len(communes)} communes différentes")
print(communes.head(10))

titre("Coordonnées")
print(df[["coordonnees_geo.lat", "coordonnees_geo.lon"]].describe().loc[["min", "max"]])
