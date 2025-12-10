import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import os 

from pathlib import Path
from services.gpt_assistant import GPTAssistant
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
    # Ville 2 exclut automatiquement la sélection de Ville 1
    remaining_cities = [c for c in cities if c != city1]

    # Si la ville2 précédente est toujours valide on la garde
    default_index = (
        remaining_cities.index(st.session_state.get("viz_city2", remaining_cities[0]))
        if st.session_state.get("viz_city2") in remaining_cities
        else 0
    )

    city2 = st.selectbox(
        "Ville 2",
        options=remaining_cities,
        index=default_index,
        key="viz_city2"
    )

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
    # 📊 Aperçu global : répartition + métriques
    # ----------------------------------------------
    st.header("📊 Aperçu global des deux villes")

    # Nombre d'annonces
    count1 = len(df1)
    count2 = len(df2)

    # Prix médian
    median1 = df1["price_m2"].median()
    median2 = df2["price_m2"].median()

    # Prix moyen
    mean1 = df1["price_m2"].mean()
    mean2 = df2["price_m2"].mean()

    # --- Mise en page ---
    colA, colB = st.columns([1, 2])

    # ---------------------
    # 🥧 Diagramme circulaire des annonces
    # ---------------------
    with colA:
        pie_df = pd.DataFrame({
            "Ville": [city1, city2],
            "Nombre": [count1, count2]
        })

        fig_pie = px.pie(
            pie_df,
            names="Ville",
            values="Nombre",
            title="Répartition des annonces",
            color="Ville",
            color_discrete_map={
                city1: "#ffa64d",  # orange clair
                city2: "#66b3ff",  # bleu clair
            }
        )

        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    # ---------------------
    # 📐 Métriques
    # ---------------------
    with colB:
        st.subheader("📌 Indicateurs principaux")
        m1, m2 = st.columns(2)

        with m1:
            st.metric(label=f"Prix médian – {city1}", value=f"{median1:,.0f} € / m²")
            st.metric(label=f"Prix moyen – {city1}", value=f"{mean1:,.0f} € / m²")

        with m2:
            st.metric(label=f"Prix médian – {city2}", value=f"{median2:,.0f} € / m²")
            st.metric(label=f"Prix moyen – {city2}", value=f"{mean2:,.0f} € / m²")

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
        color_discrete_map={
        city1: "#ffa64d",  
        city2: "#66b3ff", 
    }
    )

    fig.update_traces(marker=dict(size=8))
    fig.update_layout(height=500)

    st.plotly_chart(fig, use_container_width=True)

    # ----------------------------------------------
    # Évolution du PRIX MÉDIAN au m² dans le temps (hebdo + smoothing)
    # ----------------------------------------------
    st.header("📈 Évolution du prix MÉDIAN au m² dans le temps")

    # Choisir la meilleure colonne date
    date_col1 = "update_date" if "update_date" in df1.columns else "creation_date"
    date_col2 = "update_date" if "update_date" in df2.columns else "creation_date"

    # Conversion en datetime
    df1[date_col1] = pd.to_datetime(df1[date_col1], errors="coerce")
    df2[date_col2] = pd.to_datetime(df2[date_col2], errors="coerce")

    # Suppression dates invalides
    df1 = df1.dropna(subset=[date_col1])
    df2 = df2.dropna(subset=[date_col2])

    # Tri obligatoire
    df1 = df1.sort_values(date_col1)
    df2 = df2.sort_values(date_col2)

    # ------------------------
    # 1️⃣ Regroupement HEBDOMADAIRE
    # ------------------------
    df1["week"] = df1[date_col1].dt.to_period("W").apply(lambda r: r.start_time)
    df2["week"] = df2[date_col2].dt.to_period("W").apply(lambda r: r.start_time)

    weekly1 = (
        df1.groupby("week")["price_m2"]
            .median()
            .reset_index()
            .rename(columns={"price_m2": "median_price_m2"})
    )
    weekly1["city"] = city1

    weekly2 = (
        df2.groupby("week")["price_m2"]
            .median()
            .reset_index()
            .rename(columns={"price_m2": "median_price_m2"})
    )
    weekly2["city"] = city2

    weekly_all = pd.concat([weekly1, weekly2], ignore_index=True)

    # ------------------------
    # 2️⃣ Lissage Rolling-Median (fenêtre 3 semaines)
    # ------------------------
    weekly_all["smooth"] = (
        weekly_all
        .sort_values("week")
        .groupby("city")["median_price_m2"]
        .transform(lambda s: s.rolling(window=3, center=True, min_periods=1).median())
    )

    # ------------------------
    # Graphique
    # ------------------------
    fig_weekly = px.line(
        weekly_all,
        x="week",
        y="smooth",  # courbe lissée
        color="city",
        markers=False,
        title="Évolution du prix MÉDIAN au m² (hebdomadaire, lissé)",
        labels={
            "week": "Semaine",
            "smooth": "Prix médian au m² (€)",
            "city": "Ville"
        },
        color_discrete_map={
            city1: "#ffa64d",   # orange clair
            city2: "#66b3ff",   # bleu clair
        }
    )

    fig_weekly.update_layout(height=450)

    st.plotly_chart(fig_weekly, use_container_width=True)




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
        
    # -------------------------------------------------------------------
    # 🤖 ASSISTANT IA — Analyse automatique
    # -------------------------------------------------------------------
    st.markdown("---")
    st.header("🤖 Assistant IA — Analyse automatique du marché immobilier")

    # Vérifier qu’une clé API a bien été enregistrée dans la page Config
    if "openai_api_key" not in st.session_state:
        st.warning("🔑 Ajoutez d'abord votre clé API dans la page **Configuration**.")
        st.stop()
    # Injecte la clé dans les variables d’environnement pour le SDK OpenAI
    os.environ["OPENAI_API_KEY"] = st.session_state["openai_api_key"]
    assistant = GPTAssistant()

    user_question = st.text_area(
        "Posez votre question à l’assistant IA :",
        placeholder="Exemples :\n- Résume les tendances observées.\n- Compare les deux villes.\n- Que montrent les cartes géographiques ?",
    )

    if st.button("Analyser avec l’IA"):
        
        # -----------------------------
        # 1️⃣ Préparation des statistiques
        # -----------------------------
        stats_city1 = {
            "prix_median": float(median1),
            "prix_moyen": float(mean1),
            "annonces": int(count1),
        }

        stats_city2 = {
            "prix_median": float(median2),
            "prix_moyen": float(mean2),
            "annonces": int(count2),
        }

        # Tendances hebdomadaires lissées
        weekly_city1 = weekly1["median_price_m2"].tolist()
        weekly_city2 = weekly2["median_price_m2"].tolist()

        # -----------------------------
        # 2️⃣ Résumé géographique simple
        # -----------------------------
        geo_city1 = {
            "lat_mean": float(df1["lat"].mean()),
            "lon_mean": float(df1["lon"].mean()),
            "prix_median": float(median1)
        }

        geo_city2 = {
            "lat_mean": float(df2["lat"].mean()),
            "lon_mean": float(df2["lon"].mean()),
            "prix_median": float(median2)
        }

        # -----------------------------
        # 3️⃣ Appel à l’assistant GPT
        # -----------------------------
        with st.spinner("Analyse en cours…"):
            result = assistant.analyze(
                city1, city2,
                stats_city1, stats_city2,
                weekly_city1, weekly_city2,
                geo_city1, geo_city2,
                user_question
            )

        st.subheader("🧠 Analyse de l’Assistant IA")
        st.write(result)

