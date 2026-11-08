"""Interface web du comparateur Vélib.

Lance : streamlit run app.py
"""
import os

import streamlit as st
from dotenv import load_dotenv

from src.comparaison import EGALITE, bilan, comparer
from src.indicateurs import stats_commune
from src.nettoyage import nettoyer_velib, zones_disponibles
from src.recuperation import telecharger_velib

load_dotenv()  # lit le fichier .env (clé Météo-France) s'il existe

st.set_page_config(page_title="Comparateur Vélib", page_icon="🚲", layout="wide")
st.title("🚲 Comparateur Vélib")

# On affiche seulement si la clé est présente, jamais sa valeur
if not os.getenv("METEO_FRANCE_API_KEY"):
    st.sidebar.warning("Clé Météo-France absente : copie .env.example en .env et colle ta clé (voir README).")

df, rapport = nettoyer_velib(telecharger_velib())
zones = zones_disponibles(df)  # communes, puis « Paris 1 » à « Paris 20 »

(onglet_duel,) = st.tabs(["⚔️ Duel"])

with onglet_duel:
    colonne_a, colonne_b = st.columns(2)
    nom_a = colonne_a.selectbox("Commune A", zones, index=zones.index("Paris"))
    nom_b = colonne_b.selectbox("Commune B", zones, index=zones.index("Montreuil"))

    stats_a, stats_b = stats_commune(df, nom_a), stats_commune(df, nom_b)
    lignes = comparer(stats_a, stats_b, nom_a, nom_b)

    # Une colonne par commune : chaque indicateur, avec 🏆 pour le gagnant
    for colonne, nom, cle_valeur in [(colonne_a, nom_a, "valeur_a"), (colonne_b, nom_b, "valeur_b")]:
        with colonne:
            st.subheader(nom)
            for ligne in lignes:
                trophee = " 🏆" if ligne["gagnant"] == nom else ""
                st.metric(ligne["indicateur"] + trophee, ligne[cle_valeur])

    gagnant = bilan(lignes, nom_a, nom_b)
    if nom_a == nom_b:
        st.info("Choisis deux communes différentes.")
    elif gagnant == EGALITE:
        st.info("Égalité : chaque commune gagne autant d'indicateurs.")
    else:
        st.success(f"🏆 {gagnant} gagne le duel.")

    st.dataframe(
        [{"Indicateur": l["indicateur"], f"A : {nom_a}": l["valeur_a"], f"B : {nom_b}": l["valeur_b"], "Gagnant": l["gagnant"]}
         for l in lignes],
        hide_index=True,
    )
