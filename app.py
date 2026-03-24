import streamlit as st
import os
import time
import zipfile
from utilisateurs import USERS
from generateur import lancer_production_serie # Ton moteur avec MirrorX, Zoom et Face Detection

# --- 1. CONFIGURATION ET STYLES ---
st.set_page_config(page_title="OR D'USINE - Traffic Machine", page_icon="💎")

# --- 2. LE FIX "ZÉRO ERREUR" (Crée les dossiers au démarrage) ---
for d in ["uploads", "outputs"]:
    if not os.path.exists(d):
        os.makedirs(d)

# --- 3. SYSTÈME DE LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔑 Connexion Usine")
    u = st.text_input("Identifiant")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Entrer dans l'Usine"):
        if u in USERS and USERS[u] == p:
            st.session_state.auth = True
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Accès refusé.")
else:
    # --- 4. L'INTERFACE QUE TU AIMES ---
    st.sidebar.title(f"🛠️ Admin: {st.session_state.user}")
    if st.sidebar.button("Déconnexion"):
        st.session_state.auth = False
        st.rerun()

    st.title("💎 OR D'USINE : Traffic Machine")
    
    # Dossier Archives / Modèle
    modele_nom = st.text_input("📁 Nom de la Modèle (pour les archives)", placeholder="ex: Clara_D")

    # Upload
    vid_file = st.file_uploader("🎬 Upload ta vidéo source", type=["mp4", "mov"])

    # Captions (le coeur du système)
    st.subheader("📝 Tes Captions (Sépare par deux entrées)")
    cap_text = st.text_area("Colle tes textes ici", height=200, placeholder="Texte 1\n\nTexte 2...")

    # Réglages
    n_reels = st.number_input("🔢 Nombre de variantes à sortir", min_value=1, max_value=50, value=5)

    # --- 5. LE BOUTON DE FEU ---
    if st.button("🔥 GÉNÉRER LES REELS", use_container_width=True):
        if vid_file and cap_text and modele_nom:
            
            # Chemin de sauvegarde (C'est ici qu'on a réparé l'erreur !)
            path_in = os.path.join("uploads", vid_file.name)
            
            # --- LE PETIT FIX DE SÉCURITÉ ---
            if not os.path.exists("uploads"): os.makedirs("uploads")
            
            with open(path_in, "wb") as f:
                f.write(vid_file.getbuffer())

            # Sauvegarde des captions temporaires
            path_caps = os.path.join("uploads", "temp_caps.txt")
            with open(path_caps, "w", encoding="utf-8") as f:
                f.write(cap_text)

            # Création du dossier ARCHIVES spécifique à la modèle
            dossier_modele = os.path.join("outputs", modele_nom)
            if not os.path.exists(dossier_modele):
                os.makedirs(dossier_modele)

            # Barre de progression et Statut
            prog = st.progress(0)
            status = st.empty()

            try:
                # On lance ton moteur (generateur.py)
                lancer_production_serie(
                    path_in, 
                    path_caps, 
                    dossier_modele, 
                    n_reels, 
                    modele_nom,
                    progress_bar=prog,
                    status_text=status
                )

                st.success(f"✅ {n_reels} Reels archivés dans le dossier {modele_nom} !")

                # Préparation du ZIP pour le téléchargement direct
                zip_name = f"reels_{modele_nom}.zip"
                with zipfile.ZipFile(zip_name, 'w') as z:
                    for root, dirs, files in os.walk(dossier_modele):
                        for file in files:
                            z.write(os.path.join(root, file), file)

                with open(zip_name, "rb") as f:
                    st.download_button("📥 TÉLÉCHARGER LE PACK", f, file_name=zip_name)

            except Exception as e:
                st.error(f"Erreur technique : {e}")
        else:
            st.warning("⚠️ Remplis tout : Nom de modèle, Vidéo et Captions !")

    st.markdown("---")
    st.info("💡 Tes vidéos sont stockées dans le dossier 'outputs' sur le serveur.")
