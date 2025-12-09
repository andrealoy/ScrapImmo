import streamlit as st
from pathlib import Path
import pandas as pd
import pydeck as pdk
import plotly.express as px

from streamlit_extras.stylable_container import stylable_container
from clean_data import SeLogerDataProcessor
from config import get_city_coords


# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
st.set_page_config(page_title="Visualisation", page_icon="📊", layout="wide")
st.title("📊 Visualisation des données")


# -------------------------------------------------------------------
# FONCTION POUR RÉCUPÉRER LES VILLES SCRAPÉES
# -------------------------------------------------------------------
def get_scraped_cities():
    jsons_path = Path("jsons")
    if jsons_path.exists():
        return sorted([d.name for d in jsons_path.iterdir() if d.is_dir()])
    return []


cities = get_scraped_cities()

if not cities:
    st.warning("⚠️ Aucune ville scrapée. Allez dans l'onglet Scraping pour commencer.")
    st.stop()


# -------------------------------------------------------------------
# UI – Sélection villes + bouton
# -------------------------------------------------------------------
st.markdown("---")
col1, col2, col3, col4 = st.columns([2, 2, 1, 2])

with col1:
    city1 = st.selectbox("Ville 1", options=cities, index=0, key="viz_city1")

with col2:
    city2 = st.selectbox("Ville 2", options=cities, index=min(1, len(cities)-1), key="viz_city2")

with col3:
    st.markdown("<div style='padding-top: 27px; text-align: center;'>👉</div>", unsafe_allow_html=True)

with col4:
    st.markdown("<div style='padding-top: 5px;'></div>", unsafe_allow_html=True)
    with stylable_container(
        "blue_button",
        css_styles="""
        button {
            background-color: #0068C9 !important;
            color: white !important;
        }"""
    ):
        if st.button("Visualiser", use_container_width=True, key="viz_btn"):

            processor = SeLogerDataProcessor()

            # Nettoyage ville 1
            with st.spinner(f"Nettoyage des données pour {city1}..."):
                df1 = processor.run(city_name=city1, output_path=f"data/{city1}_clean.csv")

            # Nettoyage ville 2
            with st.spinner(f"Nettoyage des données pour {city2}..."):
                df2 = processor.run(city_name=city2, output_path=f"data/{city2}_clean.csv")

            st.session_state.df_city1 = df1
            st.session_state.df_city2 = df2
            st.session_state.show_viz = True
            st.success("Données nettoyées !")

            st.rerun()

st.markdown("---")


# -------------------------------------------------------------------
# FONCTION CARTE PYDECK
# -------------------------------------------------------------------
def make_map(df_city, lat, lon, title):
    st.markdown(f"### 🗺️ {title}")

    # Normaliser couleur prix
    p_min, p_max = df_city["price_m2"].min(), df_city["price_m2"].max()

    def price_to_color(p):
        t = (p - p_min) / (p_max - p_min + 1e-9)
        return [
            int(255 * t),
            int(30 * (1 - t)),
            int(255 * (1 - t)),
            255
        ]

    df_city["color"] = df_city["price_m2"].apply(price_to_color)

 # ---------------------------
    # 1. HEATMAP LAYER
    # ---------------------------
    heat = pdk.Layer(
        "HeatmapLayer",
        df_city,
        get_position='[lon, lat]',
        get_weight="price_m2",
        aggregation="MEAN",
        color_range=[
            [0, 0, 30],
            [20, 0, 80],
            [80, 0, 150],
            [200, 0, 120],
            [255, 50, 50],
            [255, 200, 0],
        ],
        radiusPixels=40,
        opacity = 0.35,
    )

    # ---------------------------
    # 2. SCATTER LAYER
    # ---------------------------
    points = pdk.Layer(
        "ScatterplotLayer",
        df_city,
        get_position='[lon, lat]',
        get_fill_color="color",
        get_radius=30,
        stroked=False,
        opacity=1,
        pickable=True,
    )

    # ---------------------------
    # VIEW
    # ---------------------------
    view_state = pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=11,
        pitch=45,
        bearing=20,
    )

    # ---------------------------
    # RENDER
    # ---------------------------
    r = pdk.Deck(
        layers=[heat, points],
        initial_view_state=view_state,
        # map_style="mapbox://styles/mapbox/dark-v11",
        tooltip={
            "html": "<b>Prix/m²:</b> {price_m2} €<br><b>Surface:</b> {livingSpace} m²",
            "style": {"color": "white"}
        }
    )

    st.pydeck_chart(r)


# -------------------------------------------------------------------
# AFFICHAGE DES VISUALISATIONS APRÈS CLIC
# -------------------------------------------------------------------
if st.session_state.get("show_viz", False):

    df1 = st.session_state.df_city1
    df2 = st.session_state.df_city2

    st.success(f"📊 Visualisation : {city1} vs {city2}")

    # ----------------------------------------------
    # Scatter Plot – Prix/m² vs Surface
    # ----------------------------------------------
    st.header("📉 Prix au m² selon la surface — Comparaison")
    df_all = pd.concat([df1.assign(city=city1), df2.assign(city=city2)])

    fig = px.scatter(
        df_all,
        x="livingSpace",
        y="price_m2",
        color="city",
        opacity=0.7,
        labels={
            "livingSpace": "Surface (m²)",
            "price_m2": "Prix au m² (€)",
            "city": "Ville"
        },
        title="Prix au mètre carré en fonction de la surface",
    )

    fig.update_traces(marker=dict(size=8))
    fig.update_layout(height=500)

    st.plotly_chart(fig, use_container_width=True)

    # ----------------------------------------------
    # CARTES PYDECK — 1 colonne ou 2 colonnes
    # ----------------------------------------------
    st.header("🗺️ Cartes — Vue géographique des biens")
    colA, colB = st.columns(2)

    # Carte ville 1
    with colA:
        coords1 = get_city_coords(city1)
        make_map(df1, coords1["lat"], coords1["lon"], city1)

    # Carte ville 2
    with colB:
        coords2 = get_city_coords(city2)
        make_map(df2, coords2["lat"], coords2["lon"], city2)
