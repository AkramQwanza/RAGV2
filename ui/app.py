import streamlit as st
import requests
import os
import tempfile

st.set_page_config(page_title="e-QWANZA", layout="centered")
# st.markdown("<h2 style='text-align: center;'>🤖 AIQWANZA</h2>", unsafe_allow_html=True)
# st.markdown("<p style='text-align: center;'>Posez vos questions sur l'entreprise ou chargez un PDF personnalisé à interroger !</p>", unsafe_allow_html=True)

# API URL configuration
API_URL = "http://127.0.0.1:8000"

# Title
st.markdown("<h2 style='text-align: center;'>e-QWANZA</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Gagnez du temps, accédez à la bonne info en un instant. Votre assistant IA est à votre service.</p>", unsafe_allow_html=True)


# Section : Uploader un PDF
st.markdown("### 📎 Uploader un fichier PDF ou PowerPoint")

uploaded_files = st.file_uploader(
    "Chargez un ou plusieurs fichiers PDF/PPT/PPTX :", 
    type=["pdf", "ppt", "pptx"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} fichier(s) chargé(s) avec succès !")

    if st.button("Confirmer"):
        with st.spinner("Indexation en cours..."):
            for uploaded_file in uploaded_files:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.read())
                        temp_pdf_path = tmp.name

                    index_response = requests.post(
                        f"{API_URL}/index_pdf", 
                        files={"pdf_file": open(temp_pdf_path, "rb")}
                    )

                    if index_response.status_code == 200:
                        st.success(f"📚 Document '{uploaded_file.name}' indexé avec succès !")
                    else:
                        st.error(f"❌ Erreur pour '{uploaded_file.name}' : {index_response.status_code}")
                except Exception as e:
                    st.error(f"⚠️ Problème avec '{uploaded_file.name}' : {e}")

st.markdown("### 🧠 Choix du modèle de génération")
model_choice = st.selectbox("Choisissez le modèle LLM :", ["llama3.2", "mistral", "deepseek-r1:7b"])

# Input field for the user's legal question
question = st.text_area("🔍 Entrez votre question :", placeholder="Exemple: Qu'est-ce que Qwanza ?")

# Button to submit the question
if st.button("Obtenir une réponse"):
    if question.strip():
        # Prepare request payload
        payload = {
            "text": question, 
            "model": model_choice
        }

        with st.spinner("Analyse de votre question... ⏳"):
            try:
                # Send request to API
                response = requests.post(f"{API_URL}/predict", json=payload)

                # Process response
                if response.status_code == 200:
                    result = response.json()
                    st.success("✅ Réponse obtenue avec succès !")
                    st.markdown(f"**📌 Question :** {question}")
                    st.markdown(f"**📝 Réponse :** {result['result']}")

                else:
                    st.error(f"🚨 Erreur API : {response.status_code}")

            except requests.exceptions.RequestException as e:
                st.error(f"❌ Problème de connexion avec l'API : {e}")

    else:
        st.warning("⚠️ Veuillez entrer une question avant de soumettre.")

# Button to check API status
if st.button("📡 Vérifier l'état de l'API"):
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            st.success(f"🟢 API en ligne : {response.json()['status']}")
        else:
            st.error(f"🔴 Problème avec l'API : {response.status_code}")
    except Exception as e:
        st.error(f"❌ Impossible de contacter l'API : {e}")