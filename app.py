import streamlit as st
import os
import time
import shutil 
import generateur 
from utilisateurs import USERS # 🚨 LA MAGIE EST ICI : On importe ta liste !

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="OR-DUSINE AI PRO", page_icon="💎", layout="wide")

# --- DESIGN LUXURY GOLD & DARK (CSS CUSTOM) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
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

# ==========================================
# 🔐 SYSTÈME DE LOGIN MULTI-UTILISATEURS
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["current_user"] = ""

def verifier_identifiants(username, password):
    # 🚨 Le serveur vérifie directement dans ton dictionnaire USERS
    if username in USERS and USERS[username] == password:
        return True
    return False

if not st.session_state["logged_in"]:
    st.title("🔐 Accès Restreint : OR-DUSINE PRO")
    st.markdown("---")
    
    col_id, col_pwd = st.columns(2)
    with col_id:
        user_input = st.text_input("👤 Identifiant")
    with col_pwd:
        pwd_input = st.text_input("🔑 Mot de passe", type="password")
    
    if st.button("DÉVERROUILLER L'USINE", use_container_width=True):
        if verifier_identifiants(user_input, pwd_input):
            st.session_state["logged_in"] = True
            st.session_state["current_user"] = user_input
            st.rerun()
        else:
            st.error("❌ Identifiant ou mot de passe incorrect. Accès refusé.")
    st.stop() 

# ==========================================
# 🌍 NAVIGATION (Seulement si connecté)
# ==========================================
with st.sidebar:
    st.title("💎 OR-DUSINE PRO")
    st.markdown("---")
    menu = st.radio("MENU NAVIGATION", ["🚀 CENTRE DE PRODUCTION", "✍️ ÉDITEUR CAPTIONS", "📂 GESTION DES MODÈLES"])
    st.markdown("---")
    st.info("Statut Serveur : ✅ Opérationnel")
    st.success(f"Connecté : {st.session_state['current_user']}")
    
    if st.button("🚪 Déconnexion"):
        st.session_state["logged_in"] = False
        st.rerun()

# ==========================================
# ONGLET 1 : CENTRE DE PRODUCTION
# ==========================================
if menu == "🚀 CENTRE DE PRODUCTION":
    st.header("🚀 Production par Modèle")
    
    col1, col2 = st.columns(2)
    with col1:
        video_file = st.file_uploader("🎥 Vidéo de fond (MP4)", type=["mp4", "mov"])
    with col2:
        scripts = [f for f in os.listdir() if f.endswith(".txt") and f != "requirements.txt"]
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
                os.makedirs(nom_modele, exist_ok=True)
                
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
            st.success(f"Bravo ! Les vidéos pour {nom_modele} sont prêtes. Va dans 'GESTION DES MODÈLES' pour télécharger le ZIP !")
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
    scripts_existants = [f for f in os.listdir() if f.endswith(".txt") and f != "requirements.txt"]

    if choix_action == "📝 Créer un nouveau script":
        nom_script = st.text_input("Nom du script (sans le .txt)", "nouveau_script")
        contenu_script = st.text_area("Colle ou tape ton texte ici...", height=300)
        
        if st.button("💾 SAUVEGARDER LE NOUVEAU SCRIPT", use_container_width=True):
            if nom_script and contenu_script:
                with open(f"{nom_script}.txt", "w", encoding="utf-8") as f:
                    f.write(contenu_script)
                st.success(f"Script '{nom_script}.txt' sauvegardé !")
                time.sleep(1)
                st.rerun()
            else:
                st.warning("Il faut un nom et du texte pour sauvegarder !")

    else:
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
    
    dossiers_interdits = ["__pycache__", "CAPTIONS_STORAGE", "Output_Reels", "inputs", ".git"]
    modeles = [d for d in os.listdir() if os.path.isdir(d) and not d.startswith(".") and d not in dossiers_interdits]
    
    if modeles:
        modele_choisi = st.selectbox("Sélectionner un Modèle :", modeles)
        
        with st.expander("⚙️ Options du Modèle (Exporter en ZIP / Renommer / Supprimer)", expanded=False):
            col_zip, col_edit1, col_edit2 = st.columns(3)
            
            with col_zip:
                st.write("📦 Exporter toutes les vidéos :")
                if st.button("1. Préparer le fichier .ZIP", use_container_width=True):
                    with st.spinner("Compression en cours..."):
                        shutil.make_archive(modele_choisi, 'zip', modele_choisi)
                    st.success("✅ ZIP prêt !")
                
                if os.path.exists(f"{modele_choisi}.zip"):
                    with open(f"{modele_choisi}.zip", "rb") as f:
                        st.download_button(
                            label="2. 📥 TÉLÉCHARGER LE ZIP", 
                            data=f, 
                            file_name=f"{modele_choisi}.zip", 
                            mime="application/zip", 
                            use_container_width=True
                        )
            
            with col_edit1:
                st.write("✏️ Changer le nom :")
                nouveau_nom_modele = st.text_input("", value=modele_choisi, label_visibility="collapsed")
                if st.button("Renommer le Modèle", use_container_width=True):
                    if nouveau_nom_modele != modele_choisi:
                        os.rename(modele_choisi, nouveau_nom_modele)
                        if os.path.exists(f"{modele_choisi}.zip"): os.remove(f"{modele_choisi}.zip")
                        st.success("Nom mis à jour !")
                        time.sleep(1)
                        st.rerun()
            
            with col_edit2:
                st.write("🗑️ Nettoyage complet :")
                st.write("") 
                if st.button("Supprimer TOUT le Modèle", use_container_width=True):
                    shutil.rmtree(modele_choisi)
                    if os.path.exists(f"{modele_choisi}.zip"):
                        os.remove(f"{modele_choisi}.zip")
                    st.error(f"Le modèle {modele_choisi} a été supprimé !")
                    time.sleep(1)
                    st.rerun()
        
        st.markdown("---")
        st.subheader(f"🎞️ Vidéos individuelles de {modele_choisi}")
        
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
                    if st.button("🗑️ Effacer", key=f"del_{f}", use_container_width=True):
                        os.remove(os.path.join(modele_choisi, f))
                        st.rerun()
        else:
            st.info("Ce modèle n'a aucune vidéo générée pour le moment.")
    else:
        st.write("Aucun modèle enregistré dans l'usine.")
