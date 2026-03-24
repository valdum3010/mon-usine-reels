import streamlit as st
import os
import time
import zipfile
from utilisateurs import USERS
from generateur import lancer_production_serie # Assure-toi que ton fichier s'appelle bien generateur.py

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="OR D'USINE - Traffic Machine", page_icon="🚀")

# --- INITIALISATION DES DOSSIERS (Le correctif pour l'erreur de ton pote) ---
for folder in ["uploads", "outputs"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- SYSTÈME DE LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

def login():
    st.title("🔒 Accès Privé - OR D'USINE")
    user = st.text_input("Utilisateur")
    pw = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if user in USERS and USERS[user] == pw:
            st.session_state.auth = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Identifiants incorrects")

if not st.session_state.auth:
    login()
else:
    # --- INTERFACE PRINCIPALE ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.auth = False
        st.rerun()

    st.title("🚀 Générateur de Reels Furtifs")
    st.write("L'usine est prête. Poste en masse, reste indétectable.")

    # 1. Upload de la vidéo source
    video_file = st.file_uploader("Étape 1 : Choisis ta vidéo source", type=["mp4", "mov", "avi"])

    # 2. Captions (Textes)
    st.subheader("Étape 2 : Tes Textes (Captions)")
    caption_text = st.text_area("Écris tes textes ici (sépare chaque texte par une ligne vide)", 
                                height=150, 
                                placeholder="Texte du Reel 1\n\nTexte du Reel 2\n\n...")

    # 3. Paramètres de l'usine
    st.subheader("Étape 3 : Réglages de production")
    col1, col2 = st.columns(2)
    with col1:
        n_reels = st.number_input("Nombre de Reels à générer", min_value=1, max_value=50, value=5)
    with col2:
        mode_furtif = st.checkbox("Pack Anti-Ban (Mirror + Zoom + Metadata)", value=True)

    # --- LANCEMENT DE L'USINE ---
    if st.button("🔥 LANCER LA PRODUCTION", use_container_width=True):
        if video_file and caption_text:
            # Sauvegarde temporaire de la vidéo
            path_in = os.path.join("uploads", video_file.name)
            with open(path_in, "wb") as f:
                f.write(video_file.getbuffer())

            # Sauvegarde des captions
            path_captions = os.path.join("uploads", "temp_captions.txt")
            with open(path_captions, "w", encoding="utf-8") as f:
                f.write(caption_text)

            # Dossier de sortie spécifique pour l'utilisateur
            user_output = os.path.join("outputs", st.session_state.user)
            if not os.path.exists(user_output):
                os.makedirs(user_output)

            # Barre de progression
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # APPEL AU GÉNÉRATEUR (Celui que tu as déjà dans generateur.py)
                lancer_production_serie(
                    path_in, 
                    path_captions, 
                    user_output, 
                    n_reels, 
                    st.session_state.user,
                    progress_bar=progress_bar,
                    status_text=status_text
                )

                st.success("✅ Production terminée !")

                # Création du ZIP pour le téléchargement
                zip_path = os.path.join("outputs", f"reels_{st.session_state.user}.zip")
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for root, dirs, files in os.walk(user_output):
                        for file in files:
                            zipf.write(os.path.join(root, file), file)

                with open(zip_path, "rb") as f:
                    st.download_button("⬇️ TÉLÉCHARGER TOUS LES REELS (ZIP)", f, file_name=f"mes_reels_{int(time.time())}.zip")

            except Exception as e:
                st.error(f"Erreur d'usine : {e}")
        else:
            st.warning("⚠️ Oublie pas la vidéo et les textes !")

    st.markdown("---")
    st.caption("Propulsé par OR D'USINE - Spécial OFM Traffic Machine.")
