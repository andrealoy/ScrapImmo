import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# -------------------------------------------------------------------
# 1. LOAD DATA
# -------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/cleaned.csv")

    # S'assurer que lon/lat sont bien en numérique
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')

    df = df.dropna(subset=['lon', 'lat'])  # garder les points valides
    return df

df = load_data()

st.title("🏡 Real Estate Data Explorer")
st.markdown("Visualisation des biens + carte interactive + filtres")

# -------------------------------------------------------------------
# 2. SIDEBAR FILTERS
# -------------------------------------------------------------------
st.sidebar.header("Filtres")

cities = df['city'].dropna().unique()
selected_city = st.sidebar.selectbox("Ville", ["Toutes"] + list(cities))

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
# 3. APPLY FILTERS
# -------------------------------------------------------------------
df_filtered = df.copy()

if selected_city != "Toutes":
    df_filtered = df_filtered[df_filtered['city'] == selected_city]

df_filtered = df_filtered[
    (df_filtered['price_value'].between(min_price, max_price)) &
    (df_filtered['livingSpace'].between(min_space, max_space))
]

st.subheader(f"📊 {len(df_filtered)} biens trouvés")

# -------------------------------------------------------------------
# 4. MAP
# -------------------------------------------------------------------
st.subheader("🗺️ Carte interactive")

center = [df_filtered['lat'].mean(), df_filtered['lon'].mean()]

m = folium.Map(location=center, zoom_start=12)

for _, row in df_filtered.iterrows():
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=3,
        color="blue",
        fill=True,
        fill_opacity=0.7,
        popup=f"{row['price_value']} € - {row['livingSpace']} m²"
    ).add_to(m)

st_folium(m, width=800, height=500)

# -------------------------------------------------------------------
# 5. HISTOGRAMS
# -------------------------------------------------------------------
st.subheader("📈 Histogrammes")

st.write("Distribution des prix (€)")
st.bar_chart(df_filtered['price_value'])

st.write("Distribution des surfaces (m²)")
st.bar_chart(df_filtered['livingSpace'])
