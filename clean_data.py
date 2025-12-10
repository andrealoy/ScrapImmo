import ast
import json
import pandas as pd
import numpy as np
from pathlib import Path
from shapely.geometry import shape


class SeLogerDataProcessor:
    """Pipeline complet de nettoyage des données SeLoger par ville."""

    # ------------------------------------------------------------------
    # INITIALISATION
    # ------------------------------------------------------------------
    def __init__(self):
        """Définit une fois pour toutes les configurations du pipeline."""

        # Colonnes catégorielles
        self.cat_cols = [
            "brand", "city", "zip_code", "country", "geometry_type",
            "title", "headline"
        ]

        # Colonnes numériques
        self.num_cols = [
            "price_value",
            "numberOfRooms",
            "livingSpace",
            "numberOfFloors",
            "numberOfBedrooms"
        ]

        # Mapping pour renommer les champs JSON → DataFrame propre
        self.rename = {
            "metadata.creationDate": "creation_date",
            "metadata.updateDate": "update_date",
            "sections.location.address.city": "city",
            "sections.location.address.zipCode": "zip_code",
            "sections.location.address.country": "country",
            "sections.location.geometry.type": "geometry_type",
            "sections.location.geometry.coordinates": "geometry_coords",
            "sections.description.description": "description",
            "sections.description.headline": "headline",
            "sections.hardFacts.title": "title",
            "sections.hardFacts.keyfacts": "keyfacts",
            "sections.hardFacts.facts": "facts",
            "sections.hardFacts.price.value": "price_value"
        }

        # Champs à extraire dans chaque JSON
        self.fields = list(self.rename.keys()) + ["brand", "id"]

        # Champ qui contient la liste à désimbriquer
        self.unnest = "sections.hardFacts.facts"

    # ------------------------------------------------------------------
    # FONCTIONS GÉNÉRALES
    # ------------------------------------------------------------------
    @staticmethod
    def _read_json(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _deep_get(d, key_path):
        """Accède à une clé imbriquée type 'a.b.c'."""
        for key in key_path.split("."):
            if not isinstance(d, dict):
                return None
            d = d.get(key)
            if d is None:
                return None
        return d

    # ------------------------------------------------------------------
    # EXTRACTION JSON → DataFrame
    # ------------------------------------------------------------------
    def _json_to_df(self, json_path):
        data = self._read_json(json_path)

        # Extraction simple
        row = {f: self._deep_get(data, f) for f in self.fields}
        df = pd.DataFrame([row])

        # Désimbriquer les facts
        # Désimbriquer les facts
        facts = df[self.unnest].iloc[0]

        if isinstance(facts, list):
            for item in facts:
                if isinstance(item, dict):
                    fact_type = item.get("type")
                    fact_value = item.get("value")

                    if fact_type:
                        df[fact_type] = fact_value 

        if isinstance(facts, list):
            for item in facts:
                if isinstance(item, dict):
                    df[f"fact_{item.get('type')}"] = item.get("value")

        df.drop(columns=[self.unnest], errors="ignore", inplace=True)

        return df

    # ------------------------------------------------------------------
    # COLLECTE DES JSON
    # ------------------------------------------------------------------
    def _list_jsons(self, city_name):
        """Récupère la liste des JSON pour une ville ou toutes les villes."""

        if city_name:
            folder = Path(f"jsons/{city_name.lower()}/annonces")
            if not folder.exists():
                print(f"⚠️ Dossier {folder} introuvable")
                return []
            return list(folder.glob("*.json"))

        # ALL CITIES MODE
        root = Path("jsons")
        all_jsons = []
        for city_dir in root.iterdir():
            annonces = city_dir / "annonces"
            if annonces.exists():
                all_jsons.extend(annonces.glob("*.json"))
        return all_jsons

    # ------------------------------------------------------------------
    # FUSION DES JSON
    # ------------------------------------------------------------------
    def _merge_jsons(self, json_list):
        dfs = []
        for p in json_list:
            try:
                dfs.append(self._json_to_df(p))
            except Exception as e:
                print(f"❌ Erreur JSON {p}: {e}")
        if not dfs:
            return pd.DataFrame()
        return pd.concat(dfs, ignore_index=True)

    # ------------------------------------------------------------------
    # NETTOYAGE
    # ------------------------------------------------------------------
    @staticmethod
    def _clean_numeric(series):
        return (
            series.astype(str)
            .str.replace(r"[^\d,\.]", "", regex=True)
            .str.replace(",", ".", regex=False)
            .replace({"": np.nan, ".": np.nan})
            .astype(float)
        )

    @staticmethod
    def _centroid(row):
        coords = row["geometry_coords"]
        if isinstance(coords, str):
            try:
                coords = ast.literal_eval(coords)
            except Exception:
                return pd.Series([np.nan, np.nan])
        geom = {"type": row["geometry_type"], "coordinates": coords}
        try:
            c = shape(geom).centroid
            return pd.Series([c.x, c.y])
        except Exception:
            return pd.Series([np.nan, np.nan])

    @staticmethod
    def _infer_city(zip_code):
        return None 

    def _clean_dataframe(self, df, output_path):
        df = df.rename(columns=self.rename)
        df.drop_duplicates(subset=["id"], inplace=True)
        df.dropna(subset=["livingSpace"], inplace=True)

        # Dates
        df["creation_date"] = pd.to_datetime(df["creation_date"], errors="coerce")
        df["update_date"] = pd.to_datetime(df["update_date"], errors="coerce")

        # Géométrie
        df[["lon", "lat"]] = df.apply(self._centroid, axis=1)

        # Catégories
        for c in self.cat_cols:
            if c in df.columns:
                df[c] = df[c].astype("category")

        # Numériques
        for c in self.num_cols:
            if c in df.columns:
                df[c] = self._clean_numeric(df[c])

        # Prix au m²
        df["price_m2"] = (df["price_value"] / df["livingSpace"]).round(0)

        df = df[df["city"].notna()]

        # Export
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        # Forcer geometry_coords en string pour éviter PyArrow
        if "geometry_coords" in df.columns:
            df["geometry_coords"] = df["geometry_coords"].astype(str)

        df.to_csv(output_path, index=False)

        return df
    def _process_and_save(self, json_files, output_path):
        df_raw = self._merge_jsons(json_files)
        print(f"🔢 DataFrame brut : {df_raw.shape}")

        df_clean = self._clean_dataframe(df_raw, output_path)
        print(f"✨ DataFrame nettoyé : {df_clean.shape}")
        print(f"💾 Sauvegardé -> {output_path}")

        return df_clean

    # ------------------------------------------------------------------
    # PIPELINE FINAL
    # ------------------------------------------------------------------
    def run(self, city_name=None, output_path="data/cleaned.csv"):
        """
        Ne nettoie que si nécessaire :
        - CSV non existant
        - un JSON plus récent que le CSV
        Sinon, charge directement le CSV.
        """

        print(f"📂 Vérification de : {city_name}")

        json_files = self._list_jsons(city_name)
        if not json_files:
            print("⚠️ Aucun fichier JSON trouvé.")
            return pd.DataFrame()

        json_files = list(json_files)
        last_json_time = max(f.stat().st_mtime for f in json_files)

        csv_path = Path(output_path)

        # ------------------------------
        # 1. CSV inexistant → nettoyer
        # ------------------------------
        if not csv_path.exists():
            print("📄 Aucun CSV existant → nettoyage obligatoire.")
            return self._process_and_save(json_files, output_path)

        # ------------------------------
        # 2. Vérifier si un JSON est plus récent que le CSV
        # ------------------------------
        csv_time = csv_path.stat().st_mtime

        if last_json_time > csv_time:
            print("🔄 JSON plus récents détectés → re-clean nécessaire.")
            return self._process_and_save(json_files, output_path)

        # ------------------------------
        # 3. Sinon, on charge le CSV directement
        # ------------------------------
        print("✅ CSV déjà propre et à jour → chargement direct.")
        return pd.read_csv(output_path)



# ----------------------------------------------------------------------
# MAIN SIMPLIFIÉ
# ----------------------------------------------------------------------
if __name__ == "__main__":
    processor = SeLogerDataProcessor()
    df = processor.run(city_name="paris")
    print(df.head())
