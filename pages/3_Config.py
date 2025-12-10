import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="Configuration", page_icon="⚙️")

st.title("⚙️ Configuration de l'application")
st.markdown("Ici, vous pouvez ajouter ou modifier votre clé API OpenAI.")

KEY_FILE = Path("config/api_key.json")
KEY_FILE.parent.mkdir(exist_ok=True)   # crée /config s’il n’existe pas


# -----------------------------------------------------------
# Charger la clé existante (si déjà enregistrée)
# -----------------------------------------------------------
existing_key = ""
if KEY_FILE.exists():
    try:
        existing_key = json.loads(KEY_FILE.read_text()).get("openai_api_key", "")
    except:
        existing_key = ""


# -----------------------------------------------------------
# Champ pour entrer la clé API
# -----------------------------------------------------------
api_key = st.text_input(
    "Entrez votre clé OpenAI :",
    value=existing_key,
    type="password",
    placeholder="sk-...",
)

if st.button("💾 Enregistrer la clé API"):
    if not api_key:
        st.error("❌ Veuillez entrer une clé API valide.")
    else:
        KEY_FILE.write_text(json.dumps({"openai_api_key": api_key}))
        st.success("✅ Clé API enregistrée définitivement !")


# -----------------------------------------------------------
# Feedback visuel
# -----------------------------------------------------------
if existing_key:
    st.info("🔐 Une clé est déjà enregistrée.")
else:
    st.warning("⚠️ Aucune clé enregistrée.")
