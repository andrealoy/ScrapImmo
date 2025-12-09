# config.py
import pandas as pd
from pathlib import Path

# Chargement du CSV une seule fois
CITIES_LOC_PATH = Path("tools/cities_loc.csv")

_city_df_cache = None

def load_city_data():
    """Charge le CSV contenant les coordonnées des villes."""
    global _city_df_cache
    if _city_df_cache is None:
        if not CITIES_LOC_PATH.exists():
            raise FileNotFoundError(f"❌ Fichier non trouvé : {CITIES_LOC_PATH}")
        _city_df_cache = pd.read_csv(CITIES_LOC_PATH)
        _city_df_cache["city_norm"] = _city_df_cache["city"].str.strip().str.lower()
    return _city_df_cache


def get_city_coords(city_name: str):
    """
    Retourne les coordonnées lat/lon d'une ville en utilisant le CSV tools/cities_loc.csv.
    """
    df = load_city_data()
    
    city_norm = city_name.strip().lower()
    row = df[df["city_norm"] == city_norm]

    if row.empty:
        raise KeyError(f"❌ Ville '{city_name}' non trouvée dans {CITIES_LOC_PATH}")

    return {
        "lat": float(row.iloc[0]["lat"]),
        "lon": float(row.iloc[0]["lng"])
    }
