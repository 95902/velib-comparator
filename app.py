"""Interface web du comparateur Vélib.

Lance : streamlit run app.py
"""
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

from src.comparaison import EGALITE, bilan, comparer
from src.indicateurs import etat_station, stations_de, stats_commune
from src.meteo import CleMeteoAbsente, meteo_actuelle
from src.nettoyage import nettoyer_velib, zones_disponibles
from src.recuperation import DonneesIndisponibles, charger_velib_brut

# Couleur de chaque état de station sur la carte (rouge, vert, bleu, opacité)
COULEURS = {
    "disponible": [40, 167, 69, 200],
    "vide": [220, 53, 69, 200],
    "pleine": [255, 153, 0, 200],
    "hors service": [150, 150, 150, 160],
}
TOUTES = "Toutes les stations"


@st.cache_data(ttl=60, show_spinner="Téléchargement des données Vélib…")
def charger_velib():
    """Reçoit : rien. Renvoie : (df nettoyé, rapport, en_direct), gardés en mémoire 1 minute."""
    df_brut, en_direct = charger_velib_brut()
    df, rapport = nettoyer_velib(df_brut)
    return df, rapport, en_direct


@st.cache_data(ttl=600, show_spinner="Lecture de la météo…")
def charger_meteo():
    """Reçoit : rien. Renvoie : le dict de meteo_actuelle(), gardé en mémoire 10 minutes."""
    return meteo_actuelle()


def heure_paris(date):
    """Reçoit : une date UTC (ou NaT). Renvoie : l'heure de Paris au format « 10 h 48 »."""
    if pd.isna(date):
        return "heure inconnue"
    return date.tz_convert("Europe/Paris").strftime("%H h %M")


st.set_page_config(page_title="Comparateur Vélib", page_icon="🚲", layout="wide")
st.title("🚲 Comparateur Vélib")

if st.sidebar.button("🔄 Actualiser", help="Vide le cache : retélécharge les données Vélib et la météo"):
    st.cache_data.clear()
    st.rerun()

try:
    df, rapport, en_direct = charger_velib()
except DonneesIndisponibles as erreur:
    st.error(str(erreur))
    st.stop()
if not en_direct:
    st.warning("Pas de connexion : les données affichées sont celles du dernier téléchargement.")
st.sidebar.caption(f"🚲 Vélib mis à jour à {heure_paris(df['duedate'].max())}")
zones = zones_disponibles(df)  # communes, puis « Paris 1 » à « Paris 20 »

onglet_duel, onglet_carte, onglet_meteo, onglet_nettoyage = st.tabs(
    ["⚔️ Duel", "🗺️ Carte", "🌦️ Météo", "🧹 Nettoyage"]
)

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

with onglet_carte:
    choix = st.selectbox("Zone à afficher", [TOUTES] + zones)
    carte = (df if choix == TOUTES else stations_de(df, choix)).copy()
    carte["etat"] = etat_station(carte)
    carte["couleur"] = carte["etat"].map(COULEURS)

    st.caption("🟢 disponible · 🔴 vide · 🟠 pleine · ⚪ hors service — survole un point pour le détail")
    st.pydeck_chart(pdk.Deck(
        map_style=None,  # fond de carte par défaut de Streamlit, sans clé
        initial_view_state=pdk.ViewState(
            latitude=carte["lat"].mean(), longitude=carte["lon"].mean(),
            zoom=11 if choix == TOUTES else 13,
        ),
        layers=[pdk.Layer(
            "ScatterplotLayer",
            data=carte[["name", "etat", "numbikesavailable", "numdocksavailable", "lat", "lon", "couleur"]],
            get_position="[lon, lat]",
            get_fill_color="couleur",
            get_radius=40,
            radius_min_pixels=3,
            pickable=True,
        )],
        tooltip={"text": "{name}\n{etat}\n{numbikesavailable} vélos · {numdocksavailable} bornes libres"},
    ))
    st.write(carte["etat"].value_counts().rename("stations"))

with onglet_meteo:
    st.subheader("Météo du moment à Paris (station Montsouris)")
    try:
        meteo = charger_meteo()
    except CleMeteoAbsente as erreur:
        st.warning(str(erreur))
    except requests.RequestException:
        st.error("L'API Météo-France ne répond pas pour l'instant. Réessaie avec « Actualiser ».")
    else:
        temperature, vent, pluie = st.columns(3)
        temperature.metric("🌡️ Température", f"{meteo['temperature_c']} °C")
        vent.metric("💨 Vent", f"{meteo['vent_kmh']} km/h")
        pluie.metric("🌧️ Pluie (6 dernières min)", f"{meteo['pluie_mm']} mm")
        st.caption(f"Météo relevée à {heure_paris(meteo['heure_releve'])} (mise à jour toutes les 6 minutes)")

with onglet_nettoyage:
    st.subheader("Rapport de nettoyage")
    st.write(
        f"Sur **{rapport['stations_brutes']}** stations téléchargées : "
        f"**{rapport['doublons_retires']}** doublon(s) retiré(s), "
        f"**{rapport['hors_service']}** station(s) hors service (gardées, en gris sur la carte, "
        f"mais exclues des indicateurs), dont **{rapport['capacite_nulle']}** à capacité nulle."
    )
    st.metric("Stations dans le tableau nettoyé", rapport["stations_finales"])
    st.dataframe(df[~df["en_service"]][["stationcode", "name", "commune", "capacity"]], hide_index=True)
