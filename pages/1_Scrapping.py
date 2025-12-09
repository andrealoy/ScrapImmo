import sys
from pathlib import Path
import threading
import pandas as pd
import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from streamlit_autorefresh import st_autorefresh

from scrapper import run_scraping, normalize_city
from get_loc import location_autocomplete

# ─────────────────────────────
# CONFIG PAGE
# ─────────────────────────────
st.set_page_config(page_title="Scraping", page_icon="🏠", layout="centered")

# Flag pour arrêter le scraping côté scraper
STOP_FLAG = Path("stop_scraping.flag")

# ─────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────
if "is_scraping" not in st.session_state:
    st.session_state.is_scraping = False

if "scraping_city1" not in st.session_state:
    st.session_state.scraping_city1 = None  # slug (nom dossier)

if "scraping_city2" not in st.session_state:
    st.session_state.scraping_city2 = None  # slug (nom dossier)

if "scraping_city1_raw" not in st.session_state:
    st.session_state.scraping_city1_raw = None  # nom API pour affichage

if "scraping_city2_raw" not in st.session_state:
    st.session_state.scraping_city2_raw = None  # nom API pour affichage
    
# Rafraîchit toutes les 2 secondes (2000 ms)
if st.session_state.is_scraping:
    st_autorefresh(interval=2000, key="scrape_refresh")
# ─────────────────────────────
# DATA : liste des communes
# ─────────────────────────────
@st.cache_data
def load_communes():
    df = pd.read_csv("tools/cleaned_communes_francaises.csv")
    return df["cleaned_city_name"].unique().tolist()

communes = load_communes()

# ─────────────────────────────
# UI : Titre + sélecteurs villes
# ─────────────────────────────
st.title("🏠 Scraping SeLoger")

col1, col2, col3 = st.columns([2, 1, 2])

with col1:
    city1 = st.selectbox(
        "Ville 1",
        options=[""] + communes,
        index=0,
        key="city1",
        disabled=st.session_state.is_scraping,
    )

with col2:
    st.markdown(
        "<div style='text-align: center; padding-top: 30px; "
        "font-size: 24px; font-weight: bold;'>VS</div>",
        unsafe_allow_html=True,
    )

with col3:
    city2 = st.selectbox(
        "Ville 2",
        options=[""] + communes,
        index=0,
        key="city2",
        disabled=st.session_state.is_scraping,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────
# BOUTON START / STOP
# ─────────────────────────────
col_btn = st.columns([1, 2, 1])
with col_btn[1]:

    # ── STOP ─────────────────
    if st.session_state.is_scraping:
        with stylable_container(
            "red_button",
            css_styles="""
            button {
                background-color: #CE0E00;
                color: white;
            }
            """,
        ):
            if st.button("🛑 STOP", use_container_width=True, key="stop_btn"):
                # On demande l'arrêt au scraper via le flag
                STOP_FLAG.touch()
                # On indique à l'UI qu'on a demandé l'arrêt
                st.session_state.is_scraping = False
                st.rerun()

    # ── START ────────────────
    else:
        with stylable_container(
            "green_button",
            css_styles="""
            button {
                background-color: #00AE00;
                color: white;
            }
            """,
        ):
            if st.button("▶️ START", use_container_width=True, key="start_btn"):
                if city1 and city2:
                    # 1) récupérer ID + nom renvoyé par l'API
                    id1, api_name1 = location_autocomplete(city1)
                    id2, api_name2 = location_autocomplete(city2)

                    # 2) normaliser les noms pour les dossiers
                    clean_name1 = normalize_city(api_name1)
                    clean_name2 = normalize_city(api_name2)

                    # 3) stocker les noms pour l'affichage ET les dossiers
                    st.session_state.scraping_city1 = clean_name1        # slug / dossier
                    st.session_state.scraping_city2 = clean_name2
                    st.session_state.scraping_city1_raw = api_name1      # affichage humain
                    st.session_state.scraping_city2_raw = api_name2
                    st.session_state.is_scraping = True

                    # 4) effacer le flag d'arrêt si existant
                    STOP_FLAG.unlink(missing_ok=True)

                    # 5) préparer les villes pour le scraper (avec noms normalisés)
                    cities = {clean_name1: id1, clean_name2: id2}

                    # 6) lancer le scraping dans un thread
                    def scrape_thread():
                        run_scraping(cities, size=30, max_page=100)
                        # Quand le scraping est fini (ou stoppé), on met à jour l'état
                        st.session_state.is_scraping = False

                    threading.Thread(target=scrape_thread, daemon=True).start()

                    st.rerun()
                else:
                    st.error("⚠️ Veuillez renseigner les deux villes")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────
# STATUT GLOBAL
# ─────────────────────────────
if st.session_state.is_scraping:
    label1 = st.session_state.scraping_city1_raw or st.session_state.scraping_city1 or "?"
    label2 = st.session_state.scraping_city2_raw or st.session_state.scraping_city2 or "?"
    st.success(f"✅ Scraping en cours: {label1} vs {label2}")
    st.info("Le scraping est actif...")
else:
    st.info("En attente de démarrage...")

# ─────────────────────────────
# FONCTION UTILITAIRE : comptage
# ─────────────────────────────
def count_annonces(city_slug: str) -> int:
    """Compte les JSON dans jsons/<city_slug>/annonces"""
    if not city_slug:
        return 0
    city_path = Path("jsons") / city_slug / "annonces"
    if city_path.exists():
        return len(list(city_path.glob("*.json")))
    return 0

# ─────────────────────────────
# MÉTRIQUES POUR LES VILLES EN COURS
# ─────────────────────────────
st.markdown("---")
col_header = st.columns([3, 1])
with col_header[0]:
    st.subheader("📊 Statistiques")

col_m1, col_m2 = st.columns(2)

city1_slug = st.session_state.scraping_city1
city2_slug = st.session_state.scraping_city2
city1_label = st.session_state.scraping_city1_raw or city1_slug
city2_label = st.session_state.scraping_city2_raw or city2_slug

count1 = count_annonces(city1_slug)
count2 = count_annonces(city2_slug)

with col_m1:
    st.metric("Annonces scrapées - Ville 1", count1)
    if city1_label:
        st.caption(f"📍 {city1_label}")

with col_m2:
    st.metric("Annonces scrapées - Ville 2", count2)
    if city2_label:
        st.caption(f"📍 {city2_label}")

# ─────────────────────────────
# LISTE DES VILLES DÉJÀ SCRAPÉES
# ─────────────────────────────
st.markdown("---")
st.subheader("🗂️ Villes déjà scrapées")

jsons_path = Path("jsons")
if jsons_path.exists():
    cities = [d.name for d in jsons_path.iterdir() if d.is_dir()]
    
    if cities:
        city_data = []
        for city_slug in sorted(cities):
            count = count_annonces(city_slug)
            # Affichage un peu plus joli : slug -> capitalisation simple
            pretty_name = city_slug.replace("_", " ").title()
            city_data.append({"Ville": pretty_name, "Dossier": city_slug, "Annonces": count})
        
        st.dataframe(city_data, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune ville scrapée pour le moment")
else:
    st.info("Aucune ville scrapée pour le moment")
