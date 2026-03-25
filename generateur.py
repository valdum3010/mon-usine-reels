import streamlit as st
import os
import time
import generateur  # Importe ton fichier de logique
from PIL import Image

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="OR-DUSINE AI PRO", page_icon="💎", layout="wide")

# --- DESIGN LUXURY GOLD & DARK (CSS CUSTOM) ---
st.markdown("""
    <style>
    /* Fond et texte global */
    .stApp { background-color: #0E1117; color: white; }
    
    /* Bouton de production massif et doré */
    div.stButton > button:first-child {
        background: linear-gradient(45deg, #FFD700, #B8860B);
        color: black;
        border: none;
        font-weight: bold;
        font-size: 20px;
        height: 3em;
        width: 100%;
        border-radius: 12px;
        box-shadow: 0px 4px 15px rgba(255, 215, 0, 0.3);
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        transform: scale(1.02);
        box-shadow: 0px 6px 20px rgba(255, 215, 0, 0.5);
        color: white;
    }

    /* Style des barres de progression */
    .stProgress > div > div > div > div { background-color: #FFD700; }
    
    /* Sidebar premium */
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #FFD700; }
    
    /* Titres dorés */
    h1, h2, h3 { color: #FFD700 !important; font-family: 'Arial Rounded MT Bold', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
with st.sidebar:
    st.title("💎 OR-DUSINE PRO")
    st.markdown("---")
    menu = st.radio("MENU NAVIGATION", ["✍️ ÉDITEUR CAPTIONS", "🚀 CENTRE DE PRODUCTION", "📂 MES VIDÉOS"])
    st.markdown("---")
    st.info("Statut Serveur : ✅ Opérationnel")

# --- ONGLET 1 : ÉDITEUR DE CAPTIONS ---
if menu == "✍️ ÉDITEUR CAPTIONS":
    st.header("✍️ Création de Scripts")
    st.write("Règle : 1 Entrée = Ligne suivante | 2 Entrées = Espace | 3 Entrées = Nouvelle Vidéo")
    
    nom_script = st.text_input("Nom du script (ex: Campagne_Lundi)", "mon_script")
    contenu_script = st.text_area("Colle ton texte ici...", height=300)
    
    if st.button("💾 SAUVEGARDER LE SCRIPT"):
        with open(f"{nom_script}.txt", "w", encoding="utf-8") as f:
            f.write(contenu_script)
        st.success(f"Script '{nom_script}' prêt pour la production !")

# --- ONGLET 2 : CENTRE DE PRODUCTION (DYNAMIQUE) ---
elif menu == "🚀 CENTRE DE PRODUCTION":
    st.header("🚀 Lancement de la Production")
    
    col1, col2 = st.columns(2)
    with col1:
        video_file = st.file_uploader("🎥 Vidéo de fond (MP4)", type=["mp4", "mov"])
    with col2:
        scripts = [f for f in os.listdir() if f.endswith(".txt")]
        script_choisi = st.selectbox("📄 Choisir un Script", scripts)
    
    nb_reels = st.number_input("Quantité de variantes à générer", min_value=1, max_value=50, value=5)
    nom_projet = st.text_input("Nom du projet", "Production_Alpha")

    if st.button("⚡ LANCER LA MACHINE"):
        if video_file and script_choisi:
            # Sauvegarde temporaire de la vidéo uploadée
            with open("temp_video.mp4", "wb") as f:
                f.write(video_file.read())
            
            # --- ZONE DE SUIVI EN TEMPS RÉEL ---
            st.markdown("---")
            status_placeholder = st.empty()
            progress_placeholder = st.empty()
            
            with st.status("🏗️ Analyse et rendu en cours...", expanded=True) as status:
                bar = progress_placeholder.progress(0)
                
                # Création du dossier de sortie si besoin
                os.makedirs(nom_projet, exist_ok=True)
                
                # APPEL DU GÉNÉRATEUR AVEC LES WIDGETS LIVE
                generateur.lancer_production_serie(
                    chemin_video="temp_video.mp4",
                    chemin_captions=script_choisi,
                    dossier_sortie=nom_projet,
                    n_to_make=nb_reels,
                    modele_nom=nom_projet,
                    progress_bar=bar,
                    status_text=status_placeholder
                )
                
                status.update(label="✅ PRODUCTION TERMINÉE !", state="complete", expanded=False)
            
            st.balloons()
            st.success(f"Bravo ! Tes {nb_reels} vidéos sont prêtes dans l'onglet 'MES VIDÉOS'.")
        else:
            st.error("N'oublie pas d'ajouter une vidéo et un script !")

# --- ONGLET 3 : MES VIDÉOS ---
elif menu == "📂 MES VIDÉOS":
    st.header("📂 Bibliothèque de Rendu")
    dossiers = [d for d in os.listdir() if os.path.isdir(d) and not d.startswith(".")]
    if dossiers:
        projet = st.selectbox("Sélectionner un projet", dossiers)
        fichiers = os.listdir(projet)
        for f in fichiers:
            if f.endswith(".mp4"):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"🎞️ {f}")
                with col_b:
                    with open(os.path.join(projet, f), "rb") as file:
                        st.download_button("Télécharger", file, file_name=f)
    else:
        st.write("Aucune production pour le moment.")
