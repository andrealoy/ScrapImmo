import streamlit as st


st.set_page_config(page_title="Configuration", page_icon="⚙️")

st.title("⚙️ Configuration de l'application")
st.markdown("Ici, vous pouvez ajouter ou modifier votre clé API OpenAI.")


# -----------------------------------------------------------
# Champ pour ajouter la clé API
# -----------------------------------------------------------

st.subheader("🔑 Clé API OpenAI")

# Lecture de la clé existante (si déjà stockée)
existing_key = st.session_state.get("openai_api_key", "")

api_key = st.text_input(
    "Entrez votre clé OpenAI (elle sera masquée) :",
    value=existing_key,
    type="password",
    placeholder="sk-...",
)

save_clicked = st.button("💾 Enregistrer la clé API")

# -----------------------------------------------------------
# Sauvegarde en session
# -----------------------------------------------------------

if save_clicked:
    if not api_key:
        st.error("❌ Veuillez entrer une clé API valide.")
    else:
        st.session_state["openai_api_key"] = api_key
        st.success("✅ Clé API enregistrée avec succès !")


# -----------------------------------------------------------
# Afficher l'état actuel
# -----------------------------------------------------------

if "openai_api_key" in st.session_state:
    st.info("🔐 Une clé est actuellement enregistrée dans la session.")
else:
    st.warning("⚠️ Aucune clé API enregistrée pour le moment.")
