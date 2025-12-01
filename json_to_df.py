import pandas as pd 
import json
import os 
from pathlib import Path 

fields = [
    "brand",
    "id",
    "metadata.creationDate",
    "metadata.updateDate",
    "sections.location.address.city",
    "sections.location.address.zipCode",
    "sections.location.address.country",
    "sections.location.geometry.type",
    "sections.location.geometry.coordinates",
    "sections.description.description",
    "sections.description.headline",
    "sections.hardFacts.title",
    "sections.hardFacts.keyfacts",
    "sections.hardFacts.facts",
    "sections.hardFacts.price.value"
    
]
unnest = "sections.hardFacts.facts"

def get_nested(data, path):
    keys = path.split(".")
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
        if data is None:
            return None
    return data

def read_json(json_path):
    with open(json_path,"r", encoding="utf-8") as f: 
        return json.load(f)
        
def json_to_df(json_path, fields, unnest):
    d = read_json(json_path)

    # Construire le DataFrame principal
    result = {field: get_nested(d, field) for field in fields}
    df = pd.DataFrame([result])

    # Extraire la liste "facts"
    extr = df[unnest].iloc[0]

    # Si "facts" n'existe pas → on logue mais on ne plante pas
    if not isinstance(extr, list):
        print(f"⚠️  Pas de facts dans {json_path.name}")
        df = df.drop(columns=[unnest], errors='ignore')
        return df

    # Transformer les facts en colonnes
    extr_dict = {
        item.get("type"): item.get("value")
        for item in extr
        if isinstance(item, dict)
    }

    for k, v in extr_dict.items():
        df[k] = v

    # Nettoyage
    df = df.drop([unnest], axis=1)
    return df

    
def list_jsons(path="jsons/details"): 
    folder = Path(path)
    return list(folder.rglob("*.json"))

if __name__ == "__main__":
    json_paths = list_jsons()
    dfs = []
    
    for j in json_paths: 
        print(f"Reading... {j}")
        df = json_to_df(j,fields,unnest)
        print("   → type retourné :", type(df))
        if not isinstance(df, pd.DataFrame):
            print("❌ PROBLÈME : ce fichier ne retourne pas un DataFrame !")
            print("Contenu retourné :", df)
            raise SystemExit("Arrêt du script pour diagnostic.")
        dfs.append(df)
        
final_df = pd.concat(dfs,ignore_index=True)

print(final_df)
output_path = "scraped_results.csv"
final_df.to_csv(output_path, index=False, encoding="utf-8-sig")