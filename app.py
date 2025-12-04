import streamlit as st
import pandas as pd
import pydeck as pdk

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
# PYDECK MAP GENERATOR
# -------------------------------------------------------------------
def make_map(df_city, lat, lon, title, color):
    st.markdown(f"### {title}")

    layer = pdk.Layer(
        "ScatterplotLayer",
        df_city,
        pickable=True,
        get_position='[lon, lat]',
        get_radius=40,
        get_fill_color=color,
        get_line_color=[0, 0, 0],
        line_width_min_pixels=1,
    )

    view_state = pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=11,
        pitch=0,
    )

    r = pdk.Deck(
        map_style=None,
        initial_view_state=view_state,
        layers=[layer],
        tooltip={
            "html": "<b>Prix:</b> {price_value} €<br><b>Surface:</b> {livingSpace} m²",
            "style": {"color": "white"}
        }
    )

    st.pydeck_chart(r)

# -------------------------------------------------------------------
# TWO MAPS SIDE BY SIDE
# -------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    make_map(df_paris, 48.8566, 2.3522, "🗼 Paris", [0, 122, 255, 180])

with col2:
    make_map(df_lyon, 45.7640, 4.8357, "🦁 Lyon", [255, 80, 0, 180])
