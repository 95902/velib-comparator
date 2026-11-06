"""Interface web du comparateur Vélib.

Lance : streamlit run app.py
Pour l'instant : page « Hello » qui vérifie que Streamlit s'ouvre et que la clé Météo-France est lue.
"""
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # lit le fichier .env (clé Météo-France) s'il existe

st.set_page_config(page_title="Comparateur Vélib", page_icon="🚲")

st.title("🚲 Comparateur Vélib")
st.write("Hello ! L'application Streamlit fonctionne.")

# On affiche seulement si la clé est présente, jamais sa valeur
if os.getenv("METEO_FRANCE_API_KEY"):
    st.success("Clé Météo-France trouvée dans .env")
else:
    st.warning("Clé Météo-France absente : copie .env.example en .env et colle ta clé (voir README).")
