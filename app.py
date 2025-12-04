import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px 


# -------------------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/cleaned.csv")

    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')

    return df.dropna(subset=['lon', 'lat'])

df = load_data()

st.title("🏡 Real Estate Data Explorer — PyDeck Edition ⚡️")
st.markdown("Deux cartes super rapides (Paris & Lyon) basées sur WebGL")

# -------------------------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------------------------
st.sidebar.header("Filtres")

min_price, max_price = st.sidebar.slider(
    "Prix (€)",
    int(df['price_value'].min()),
    int(df['price_value'].max()),
    (int(df['price_value'].min()), int(df['price_value'].max()))
)

min_space, max_space = st.sidebar.slider(
    "Surface (m²)",
    0,
    int(df['livingSpace'].max()),
    (0, int(df['livingSpace'].max()))
)

# -------------------------------------------------------------------
# APPLY FILTERS
# -------------------------------------------------------------------
df_filtered = df[
    (df['price_value'].between(min_price, max_price)) &
    (df['livingSpace'].between(min_space, max_space))
]

st.subheader(f"📊 {len(df_filtered)} biens filtrés")

df_paris = df_filtered[df_filtered['city'].str.contains("paris", case=False, na=False)]
df_lyon = df_filtered[df_filtered['city'].str.contains("lyon", case=False, na=False)]

# -------------------------------------------------------------------
# SCATTERPLOT PRICE PER M SQUARED
# -------------------------------------------------------------------

st.subheader("📉 Prix au mètre carré — Paris vs Lyon")

df_plot = df_filtered.copy()

fig = px.scatter(
    df_plot,
    x="livingSpace",
    y="price_m2",
    color="city",
    labels={
        "livingSpace": "Surface (m²)",
        "price_m2": "Prix au m² (€)",
        "city_clean": "Ville"
    },
    title="Prix au mètre carré en fonction de la surface",
    opacity=0.7,
)

fig.update_traces(marker=dict(size=8))
fig.update_layout(height=500)

st.plotly_chart(fig, use_container_width=True)


# -------------------------------------------------------------------
# PYDECK MAP GENERATOR
# -------------------------------------------------------------------
def make_map(df_city, lat, lon, title):
    st.markdown(f"### {title}")

    # Color mapping for scatter points
    p_min, p_max = df_city["price_m2"].min(), df_city["price_m2"].max()

    def price_to_color(p):
        t = (p - p_min) / (p_max - p_min + 1e-9)

        # couleurs plus saturées / néon
        r = int(255 * t)
        g = int(30 * (1 - t))
        b = int(255 * (1 - t))  # plus de bleu
        return [r, g, b, 255]   # alpha max = hyper visible


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
# TWO MAPS SIDE BY SIDE
# -------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    make_map(df_paris, 48.8566, 2.3522, "Paris")

with col2:
    make_map(df_lyon, 45.7640, 4.8357, "Lyon")
