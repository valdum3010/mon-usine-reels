import streamlit as st
import os
import time
import shutil # 🚨 Nouvel outil pour supprimer des dossiers entiers (Les modèles)
import generateur 

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="OR-DUSINE AI PRO", page_icon="💎", layout="wide")

# --- DESIGN LUXURY GOLD & DARK (CSS CUSTOM) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    
    /* Bouton principal de production */
    div.stButton > button:first-child {
        background: linear-gradient(45deg, #FFD700, #B8860B);
        color: black;
        border: none;
        font-weight: bold;
        border-radius: 8px;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        transform: scale(1.02);
        color: white;
    }

    .stProgress > div > div > div > div { background-color: #FFD700; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #FFD700; }
    h1, h2, h3 { color: #FFD700 !important; font-family: 'Arial Rounded MT Bold', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
with st.sidebar:
    st.title("💎 OR-DUSINE PRO")
    st.markdown("---")
    menu = st.radio("MENU NAVIGATION", ["🚀 CENTRE DE PRODUCTION", "✍️ ÉDITEUR CAPTIONS", "📂 GESTION DES MODÈLES"])
    st.markdown("---")
    st.info("Statut Serveur : ✅ Opérationnel")

# ==========================================
# ONGLET 1 : CENTRE DE PRODUCTION
# ==========================================
if menu == "🚀 CENTRE DE PRODUCTION":
    st.header("🚀 Production par Modèle")
    
    col1, col2 = st.columns(2)
    with col1:
        video_file = st.file_uploader("🎥 Vidéo de fond (MP4)", type=["mp4", "mov"])
    with col2:
        scripts = [f for f in os.listdir() if f.endswith(".txt")]
        if scripts:
            script_choisi = st.selectbox("📄 Choisir un Script", scripts)
        else:
            st.warning("Aucun script trouvé. Va dans l'onglet 'ÉDITEUR CAPTIONS' pour en créer un !")
            script_choisi = None
    
    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
        nb_reels = st.number_input("Quantité de variantes à générer", min_value=1, max_value=50, value=5)
    with col4:
        # 🚨 MODIF : On parle de "Modèle" et non plus de "Projet"
        nom_modele = st.text_input("Nom du Modèle (ex: Chloe_OF, Emma_Tiktok...)", "Nouveau_Modele")

    if st.button("⚡ LANCER LA MACHINE", use_container_width=True):
        if video_file and script_choisi and nom_modele:
            with open("temp_video.mp4", "wb") as f:
                f.write(video_file.read())
            
            st.markdown("---")
            status_placeholder = st.empty()
            progress_placeholder = st.empty()
            
            with st.status("🏗️ Analyse et rendu en cours...", expanded=True) as status:
                bar = progress_placeholder.progress(0)
                os.makedirs(nom_modele, exist_ok=True) # Crée le dossier au nom du modèle
                
                generateur.lancer_production_serie(
                    chemin_video="temp_video.mp4",
                    chemin_captions=script_choisi,
                    dossier_sortie=nom_modele,
                    n_to_make=nb_reels,
                    modele_nom=nom_modele,
                    progress_bar=bar,
                    status_text=status_placeholder
                )
                status.update(label="✅ PRODUCTION TERMINÉE !", state="complete", expanded=False)
            
            st.balloons()
            st.success(f"Bravo ! Les vidéos pour {nom_modele} sont prêtes dans l'onglet 'GESTION DES MODÈLES'.")
        else:
            st.error("N'oublie pas d'ajouter une vidéo, un script et un nom de modèle !")

# ==========================================
# ONGLET 2 : ÉDITEUR DE CAPTIONS
# ==========================================
elif menu == "✍️ ÉDITEUR CAPTIONS":
    st.header("✍️ Gestion des Scripts")
    st.write("Règle : 1 Entrée = Ligne suivante | 2 Entrées = Espace | 3 Entrées = Nouvelle Vidéo")
    st.markdown("---")
    
    choix_action = st.radio("Que souhaites-tu faire ?", ["📝 Créer un nouveau script", "✏️ Modifier / Supprimer un script existant"])
    scripts_existants = [f for f in os.listdir() if f.endswith(".txt")]

    if choix_action == "📝 Créer un nouveau script":
        nom_script = st.text_input("Nom du script (sans le .txt)", "nouveau_script")
        contenu_script = st.text_area("Colle ou tape ton texte ici...", height=300)
        
        if st.button("💾 SAUVEGARDER LE NOUVEAU SCRIPT", use_container_width=True):
            if nom_script and contenu_script:
                with open(f"{nom_script}.txt", "w", encoding="utf-8") as f:
                    f.write(contenu_script)
                st.success(f"Script '{nom_script}.txt' sauvegardé !")
                time.sleep(1)
                st.rerun() # Rafraîchit la page
            else:
                st.warning("Il faut un nom et du texte pour sauvegarder !")

    else: # Mode Modification / Suppression
        if scripts_existants:
            script_a_modifier = st.selectbox("Sélectionne le script :", scripts_existants)
            
            with open(script_a_modifier, "r", encoding="utf-8") as f:
                contenu_actuel = f.read()
            nom_actuel = script_a_modifier.replace(".txt", "")
            
            nouveau_nom = st.text_input("Nom du script", nom_actuel)
            nouveau_contenu = st.text_area("Modifie ton texte ici...", value=contenu_actuel, height=300)
            
            colA, colB = st.columns(2)
            with colA:
                if st.button("💾 METTRE À JOUR", use_container_width=True):
                    with open(f"{nouveau_nom}.txt", "w", encoding="utf-8") as f:
                        f.write(nouveau_contenu)
                    if nouveau_nom != nom_actuel:
                        os.remove(script_a_modifier)
                    st.success("Script mis à jour !")
                    time.sleep(1)
                    st.rerun()
            with colB:
                # 🚨 LA NOUVEAUTÉ : SUPPRIMER LE SCRIPT
                if st.button("🗑️ SUPPRIMER CE SCRIPT", use_container_width=True):
                    os.remove(script_a_modifier)
                    st.error("Script supprimé définitivement !")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("Aucun script enregistré. Crées-en un nouveau !")

# ==========================================
# ONGLET 3 : GESTION DES MODÈLES (LE "DRIVE")
# ==========================================
elif menu == "📂 GESTION DES MODÈLES":
    st.header("📂 Le Drive des Modèles")
    
    # Sécurité anti-dossiers techniques
    dossiers_interdits = ["__pycache__", "CAPTIONS_STORAGE", "Output_Reels", "inputs", ".git"]
    modeles = [d for d in os.listdir() if os.path.isdir(d) and not d.startswith(".") and d not in dossiers_interdits]
    
    if modeles:
        modele_choisi = st.selectbox("Sélectionner un Modèle :", modeles)
        
        # --- PANNEAU DE CONTRÔLE DU MODÈLE (Edit / Sup) ---
        with st.expander("⚙️ Options du Modèle (Renommer / Supprimer)", expanded=False):
            col_edit1, col_edit2 = st.columns(2)
            with col_edit1:
                nouveau_nom_modele = st.text_input("Nouveau nom :", value=modele_choisi)
                if st.button("✏️ Renommer le Modèle", use_container_width=True):
                    if nouveau_nom_modele != modele_choisi:
                        os.rename(modele_choisi, nouveau_nom_modele)
                        st.success("Nom mis à jour !")
                        time.sleep(1)
                        st.rerun()
            with col_edit2:
                st.write("") # Petit espace pour aligner
                st.write("")
                if st.button("🗑️ Supprimer TOUT le Modèle", use_container_width=True):
                    shutil.rmtree(modele_choisi) # Détruit le dossier et son contenu
                    st.error(f"Le modèle {modele_choisi} a été supprimé !")
                    time.sleep(1)
                    st.rerun()
        
        st.markdown("---")
        st.subheader(f"🎞️ Vidéos de {modele_choisi}")
        
        fichiers = os.listdir(modele_choisi)
        videos = [f for f in fichiers if f.endswith(".mp4")]
        
        if videos:
            for f in videos:
                col_vid, col_down, col_del = st.columns([6, 2, 2])
                with col_vid:
                    st.write(f"▶️ {f}")
                with col_down:
                    with open(os.path.join(modele_choisi, f), "rb") as file:
                        st.download_button("📥 Télécharger", file, file_name=f, key=f"dl_{f}", use_container_width=True)
                with col_del:
                    # Permet de supprimer UNE seule vidéo ratée
                    if st.button("🗑️ Effacer", key=f"del_{f}", use_container_width=True):
                        os.remove(os.path.join(modele_choisi, f))
                        st.rerun()
        else:
            st.info("Ce modèle n'a aucune vidéo générée pour le moment.")
    else:
        st.write("Aucun modèle enregistré dans l'usine.")
