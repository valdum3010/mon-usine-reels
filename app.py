import streamlit as st
import os
import time
import shutil 
import generateur 
from utilisateurs import USERS 

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
# 🏗️ CRÉATEUR D'ESPACES PRIVÉS (NOUVEAU)
# ==========================================
def init_espace_prive(username):
    # Crée un dossier principal au nom de l'utilisateur (ex: "Espace_admin")
    dossier_base = f"Espace_{username}"
    dossier_scripts = os.path.join(dossier_base, "Scripts")
    dossier_modeles = os.path.join(dossier_base, "Modeles")
    
    # Si les dossiers n'existent pas encore, l'usine les construit
    os.makedirs(dossier_scripts, exist_ok=True)
    os.makedirs(dossier_modeles, exist_ok=True)
    
    return dossier_base, dossier_scripts, dossier_modeles

# ==========================================
# 🔐 SYSTÈME DE LOGIN MULTI-UTILISATEURS
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["current_user"] = ""

def verifier_identifiants(username, password):
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

# --- INITIALISATION DES VARIABLES DE L'ESPACE PRIVÉ ---
ws_base, ws_scripts, ws_modeles = init_espace_prive(st.session_state['current_user'])

# ==========================================
# 🌍 NAVIGATION
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
    st.header(f"🚀 Production Privée ({st.session_state['current_user']})")
    
    col1, col2 = st.columns(2)
    with col1:
        video_files = st.file_uploader("🎥 Glisse tes vidéos ici (Tu peux en mettre plusieurs !)", type=["mp4", "mov"], accept_multiple_files=True)
    with col2:
        # 🚨 L'usine ne cherche les scripts QUE dans le dossier secret de l'utilisateur !
        scripts = [f for f in os.listdir(ws_scripts) if f.endswith(".txt")]
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
        if video_files: # Si tu as mis au moins une vidéo
            progress_bar = st.progress(0)
            st.info(f"🚀 Production lancée pour {len(video_files)} vidéos...")
            
            for i, video_file in enumerate(video_files):
                st.write(f"⚙️ Traitement de la vidéo {i+1}...")
                
                # On lance ta machine pour CHAQUE vidéo
                generateur.lancer_production_serie(
                    chemin_video=video_file,
                    # ⚠️ ATTENTION : L'erreur de tout à l'heure vient d'ici 👇
                    script_nom=script_choisi, 
                    nb_variantes=nb_reels,
                    nom_modele=f"{nom_modele}_{i+1}",
                    status_text=st.empty()
                )
                progress_bar.progress((i + 1) / len(video_files))
                
            st.success("✅ Toutes les vidéos ont été générées !")
            st.balloons()
        else:
            st.error("⚠️ N'oublie pas de glisser au moins une vidéo !")

            # 2. CAS D'UN SEUL FICHIER (NORMAL)
            else:
                generateur.lancer_production_serie(
                    chemin_video=video_file,
                    script_nom=script_choisi,
                    nb_variantes=nb_reels,
                    nom_modele=nom_modele,
                    status_text=st.empty()
                )
        else:
            st.error("⚠️ Oublie pas de mettre une vidéo ou un ZIP !")

# ==========================================
# ONGLET 2 : ÉDITEUR DE CAPTIONS
# ==========================================
elif menu == "✍️ ÉDITEUR CAPTIONS":
    st.header(f"✍️ Gestion de tes Scripts ({st.session_state['current_user']})")
    st.write("Règle : 1 Entrée = Ligne suivante | 2 Entrées = Espace | 3 Entrées = Nouvelle Vidéo")
    st.markdown("---")
    
    choix_action = st.radio("Que souhaites-tu faire ?", ["📝 Créer un nouveau script", "✏️ Modifier / Supprimer un script existant"])
    scripts_existants = [f for f in os.listdir(ws_scripts) if f.endswith(".txt")]

    if choix_action == "📝 Créer un nouveau script":
        nom_script = st.text_input("Nom du script (sans le .txt)", "nouveau_script")
        contenu_script = st.text_area("Colle ou tape ton texte ici...", height=300)
        
        if st.button("💾 SAUVEGARDER LE NOUVEAU SCRIPT", use_container_width=True):
            if nom_script and contenu_script:
                chemin_sauvegarde = os.path.join(ws_scripts, f"{nom_script}.txt")
                with open(chemin_sauvegarde, "w", encoding="utf-8") as f:
                    f.write(contenu_script)
                st.success(f"Script sauvegardé dans ton espace privé !")
                time.sleep(1)
                st.rerun()
            else:
                st.warning("Il faut un nom et du texte pour sauvegarder !")

    else:
        if scripts_existants:
            script_a_modifier = st.selectbox("Sélectionne le script :", scripts_existants)
            chemin_script_actuel = os.path.join(ws_scripts, script_a_modifier)
            
            with open(chemin_script_actuel, "r", encoding="utf-8") as f:
                contenu_actuel = f.read()
            nom_actuel = script_a_modifier.replace(".txt", "")
            
            nouveau_nom = st.text_input("Nom du script", nom_actuel)
            nouveau_contenu = st.text_area("Modifie ton texte ici...", value=contenu_actuel, height=300)
            
            colA, colB = st.columns(2)
            with colA:
                if st.button("💾 METTRE À JOUR", use_container_width=True):
                    chemin_nouveau = os.path.join(ws_scripts, f"{nouveau_nom}.txt")
                    with open(chemin_nouveau, "w", encoding="utf-8") as f:
                        f.write(nouveau_contenu)
                    
                    if nouveau_nom != nom_actuel:
                        os.remove(chemin_script_actuel)
                    st.success("Script mis à jour !")
                    time.sleep(1)
                    st.rerun()
            with colB:
                if st.button("🗑️ SUPPRIMER CE SCRIPT", use_container_width=True):
                    os.remove(chemin_script_actuel)
                    st.error("Script supprimé définitivement !")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("Aucun script enregistré. Crées-en un nouveau !")

# ==========================================
# ONGLET 3 : GESTION DES MODÈLES (LE "DRIVE" PRIVÉ)
# ==========================================
elif menu == "📂 GESTION DES MODÈLES":
    st.header(f"📂 Ton Drive Privé ({st.session_state['current_user']})")
    
    # On ne regarde plus les dossiers à la racine, mais SEULEMENT dans le dossier "Modeles" du client
    modeles = [d for d in os.listdir(ws_modeles) if os.path.isdir(os.path.join(ws_modeles, d))]
    
    if modeles:
        modele_choisi = st.selectbox("Sélectionner un Modèle :", modeles)
        chemin_modele = os.path.join(ws_modeles, modele_choisi)
        chemin_zip = os.path.join(ws_modeles, f"{modele_choisi}.zip")
        
        with st.expander("⚙️ Options du Modèle (Exporter en ZIP / Renommer / Supprimer)", expanded=False):
            col_zip, col_edit1, col_edit2 = st.columns(3)
            
            with col_zip:
                st.write("📦 Exporter toutes les vidéos :")
                if st.button("1. Préparer le fichier .ZIP", use_container_width=True):
                    with st.spinner("Compression en cours..."):
                        # Compresse uniquement le dossier privé du modèle
                        shutil.make_archive(chemin_modele, 'zip', chemin_modele)
                    st.success("✅ ZIP prêt !")
                
                if os.path.exists(chemin_zip):
                    with open(chemin_zip, "rb") as f:
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
                        nouveau_chemin = os.path.join(ws_modeles, nouveau_nom_modele)
                        os.rename(chemin_modele, nouveau_chemin)
                        if os.path.exists(chemin_zip): os.remove(chemin_zip)
                        st.success("Nom mis à jour !")
                        time.sleep(1)
                        st.rerun()
            
            with col_edit2:
                st.write("🗑️ Nettoyage complet :")
                st.write("") 
                if st.button("Supprimer TOUT le Modèle", use_container_width=True):
                    shutil.rmtree(chemin_modele)
                    if os.path.exists(chemin_zip): os.remove(chemin_zip)
                    st.error(f"Le modèle {modele_choisi} a été supprimé !")
                    time.sleep(1)
                    st.rerun()
        
        st.markdown("---")
        st.subheader(f"🎞️ Vidéos individuelles de {modele_choisi}")
        
        fichiers = os.listdir(chemin_modele)
        videos = [f for f in fichiers if f.endswith(".mp4")]
        
        if videos:
            for f in videos:
                chemin_video_seule = os.path.join(chemin_modele, f)
                col_vid, col_down, col_del = st.columns([6, 2, 2])
                with col_vid:
                    st.write(f"▶️ {f}")
                with col_down:
                    with open(chemin_video_seule, "rb") as file:
                        st.download_button("📥 Télécharger", file, file_name=f, key=f"dl_{f}", use_container_width=True)
                with col_del:
                    if st.button("🗑️ Effacer", key=f"del_{f}", use_container_width=True):
                        os.remove(chemin_video_seule)
                        st.rerun()
        else:
            st.info("Ce modèle n'a aucune vidéo générée pour le moment.")
    else:
        st.write("Aucun modèle enregistré dans ton Drive privé.")
