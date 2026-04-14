import streamlit as st
import os
import time
import shutil
import generateur
import drive_manager
from utilisateurs import USERS

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="OR-DUSINE AI PRO", page_icon="💎", layout="wide")

# --- DESIGN LUXURY GOLD & DARK ---
st.markdown("""
<style>
.stApp { background-color: #0E1117; color: white; }
div.stButton > button:first-child {
    background: linear-gradient(45deg, #FFD700, #B8860B);
    color: black; border: none; font-weight: bold;
    border-radius: 8px; transition: 0.3s;
}
div.stButton > button:first-child:hover { transform: scale(1.02); color: white; }
.stProgress > div > div > div > div { background-color: #FFD700; }
[data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #FFD700; }
h1, h2, h3 { color: #FFD700 !important; font-family: 'Arial Rounded MT Bold', sans-serif; }
.drive-connected { background: #1a3a1a; border: 1px solid #00ff00; border-radius: 8px; padding: 10px; margin: 5px 0; }
.drive-disconnected { background: #3a1a1a; border: 1px solid #ff4444; border-radius: 8px; padding: 10px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 🏗️ ESPACES PRIVÉS
# ==========================================

def init_espace_prive(username):
    dossier_base = f"Espace_{username}"
    dossier_scripts = os.path.join(dossier_base, "Scripts")
    dossier_modeles = os.path.join(dossier_base, "Modeles")
    os.makedirs(dossier_scripts, exist_ok=True)
    os.makedirs(dossier_modeles, exist_ok=True)
    return dossier_base, dossier_scripts, dossier_modeles


# ==========================================
# 🔐 LOGIN
# ==========================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["current_user"] = ""

def verifier_identifiants(username, password):
    return username in USERS and USERS[username] == password

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
            st.error("❌ Identifiant ou mot de passe incorrect.")
    st.stop()

# --- INIT ESPACE ---
ws_base, ws_scripts, ws_modeles = init_espace_prive(st.session_state['current_user'])
username = st.session_state['current_user']

# ==========================================
# 🔗 GESTION OAUTH GOOGLE (dans l'URL)
# ==========================================

query_params = st.query_params
if "code" in query_params:
    code = query_params["code"]
    if drive_manager.save_token_from_code(username, code):
        st.success("✅ Google Drive connecté avec succès !")
        st.query_params.clear()
        time.sleep(1)
        st.rerun()
    else:
        st.error("❌ Erreur lors de la connexion Google Drive.")
        st.query_params.clear()

# ==========================================
# 🌍 SIDEBAR + NAVIGATION
# ==========================================

with st.sidebar:
    st.title("💎 OR-DUSINE PRO")
    st.markdown("---")
    menu = st.radio("MENU NAVIGATION", [
        "🚀 CENTRE DE PRODUCTION",
        "✍️ ÉDITEUR CAPTIONS",
        "📂 GESTION DES MODÈLES"
    ])
    st.markdown("---")

    # --- BLOC GOOGLE DRIVE ---
    st.subheader("☁️ Google Drive")
    drive_service = drive_manager.get_drive_service(username)

    if drive_service:
        st.markdown('<div class="drive-connected">✅ Drive connecté</div>', unsafe_allow_html=True)
        if st.button("🔌 Déconnecter Drive", use_container_width=True):
            drive_manager.disconnect_drive(username)
            st.rerun()
    else:
        st.markdown('<div class="drive-disconnected">❌ Drive non connecté</div>', unsafe_allow_html=True)
        if st.button("🔗 Connecter mon Google Drive", use_container_width=True):
            auth_url = drive_manager.get_auth_url(username)
            st.markdown(f"[👉 Clique ici pour autoriser Google Drive]({auth_url})")
            st.info("Après autorisation, tu seras redirigé automatiquement.")

    st.markdown("---")
    st.info("Statut Serveur : ✅ Opérationnel")
    st.success(f"Connecté : {username}")
    if st.button("🚪 Déconnexion"):
        st.session_state["logged_in"] = False
        st.rerun()


# ==========================================
# ONGLET 1 : CENTRE DE PRODUCTION
# ==========================================

if menu == "🚀 CENTRE DE PRODUCTION":
    st.header(f"🚀 Production Privée ({username})")

    col1, col2 = st.columns(2)
    with col1:
        video_files = st.file_uploader(
            "🎥 Glisse tes vidéos ici",
            type=["mp4", "mov"],
            accept_multiple_files=True
        )
    with col2:
        scripts = [f for f in os.listdir(ws_scripts) if f.endswith(".txt")]
        if scripts:
            script_choisi = st.selectbox("📄 Choisir un Script", scripts)
        else:
            st.warning("Aucun script. Va dans 'ÉDITEUR CAPTIONS' pour en créer un !")
            script_choisi = None

    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
        nb_reels = st.number_input("Quantité de variantes", min_value=1, max_value=50, value=5)
    with col4:
        nom_modele = st.text_input("Nom du Modèle", "Nouveau_Modele")

    # --- OPTIONS GOOGLE DRIVE ---
    drive_service = drive_manager.get_drive_service(username)
    upload_drive = False
    dossier_drive_choisi_id = None
    dossier_drive_choisi_nom = None

    if drive_service:
        st.markdown("---")
        st.subheader("☁️ Options Google Drive")
        upload_drive = st.toggle("📤 Envoyer automatiquement sur Google Drive après génération", value=True)

        if upload_drive:
            col_drive1, col_drive2 = st.columns(2)
            with col_drive1:
                dossiers = drive_manager.lister_dossiers_drive(drive_service)
                options_dossiers = {"📁 Racine de mon Drive": None}
                for d in dossiers:
                    options_dossiers[f"📂 {d['name']}"] = d['id']

                dossier_selectionne = st.selectbox(
                    "Choisir le dossier de destination :",
                    list(options_dossiers.keys())
                )
                dossier_drive_choisi_id = options_dossiers[dossier_selectionne]
                dossier_drive_choisi_nom = dossier_selectionne

            with col_drive2:
                st.write("")
                st.write("")
                nouveau_dossier_nom = st.text_input("Ou créer un nouveau dossier :", placeholder="Nom du nouveau dossier")
                if st.button("➕ Créer ce dossier", use_container_width=True):
                    if nouveau_dossier_nom:
                        new_id = drive_manager.creer_dossier_drive(drive_service, nouveau_dossier_nom, dossier_drive_choisi_id)
                        if new_id:
                            st.success(f"✅ Dossier '{nouveau_dossier_nom}' créé !")
                            dossier_drive_choisi_id = new_id
                            time.sleep(1)
                            st.rerun()
    else:
        st.info("💡 Connecte ton Google Drive dans la sidebar pour activer l'upload automatique !")

    st.markdown("---")

    if st.button("⚡ LANCER LA MACHINE", use_container_width=True):
        if video_files and script_choisi:
            progress_bar = st.progress(0)
            status = st.empty()
            st.info(f"🚀 Production lancée pour {len(video_files)} vidéos...")

            dossier_sortie_modele = os.path.join(ws_modeles, nom_modele)
            os.makedirs(dossier_sortie_modele, exist_ok=True)
            chemin_script_complet = os.path.join(ws_scripts, script_choisi)

            for i, video_file in enumerate(video_files):
                status.text(f"⚙️ Traitement vidéo {i+1}/{len(video_files)}...")
                temp_video_path = f"temp_video_{i}.mp4"
                with open(temp_video_path, "wb") as f:
                    f.write(video_file.read())

                generateur.lancer_production_serie(
                    chemin_video=temp_video_path,
                    chemin_captions=chemin_script_complet,
                    dossier_sortie=dossier_sortie_modele,
                    n_to_make=nb_reels,
                    modele_nom=f"{nom_modele}_{i+1}",
                    status_text=status
                )

                if os.path.exists(temp_video_path):
                    os.remove(temp_video_path)

                progress_bar.progress((i + 1) / len(video_files))

            st.success("✅ Toutes les vidéos ont été générées !")

            # --- UPLOAD GOOGLE DRIVE ---
            if upload_drive and drive_service:
                st.info("☁️ Upload vers Google Drive en cours...")
                status_drive = st.empty()

                # Crée un sous-dossier au nom du modèle sur Drive
                dossier_modele_drive_id = drive_manager.creer_dossier_drive(
                    drive_service,
                    nom_modele,
                    dossier_drive_choisi_id
                )

                nb_uploaded = drive_manager.uploader_videos_vers_drive(
                    service=drive_service,
                    dossier_local=dossier_sortie_modele,
                    dossier_drive_id=dossier_modele_drive_id,
                    status_text=status_drive
                )

                status_drive.empty()
                st.success(f"✅ {nb_uploaded} vidéos uploadées sur Google Drive dans '{dossier_drive_choisi_nom}/{nom_modele}' !")

            st.balloons()
        else:
            st.error("⚠️ Ajoute au moins une vidéo et sélectionne un script !")


# ==========================================
# ONGLET 2 : ÉDITEUR DE CAPTIONS
# ==========================================

elif menu == "✍️ ÉDITEUR CAPTIONS":
    st.header(f"✍️ Gestion de tes Scripts ({username})")
    st.write("Règle : 1 Entrée = Ligne | 2 Entrées = Espace | 3 Entrées = Nouvelle Vidéo")
    st.markdown("---")

    choix_action = st.radio("Que souhaites-tu faire ?", [
        "📝 Créer un nouveau script",
        "✏️ Modifier / Supprimer un script existant"
    ])
    scripts_existants = [f for f in os.listdir(ws_scripts) if f.endswith(".txt")]

    if choix_action == "📝 Créer un nouveau script":
        nom_script = st.text_input("Nom du script (sans .txt)", "nouveau_script")
        contenu_script = st.text_area("Colle ou tape ton texte ici...", height=300)
        if st.button("💾 SAUVEGARDER", use_container_width=True):
            if nom_script and contenu_script:
                chemin_sauvegarde = os.path.join(ws_scripts, f"{nom_script}.txt")
                with open(chemin_sauvegarde, "w", encoding="utf-8") as f:
                    f.write(contenu_script)
                st.success("Script sauvegardé !")
                time.sleep(1)
                st.rerun()
            else:
                st.warning("Il faut un nom et du texte !")
    else:
        if scripts_existants:
            script_a_modifier = st.selectbox("Sélectionne le script :", scripts_existants)
            chemin_script_actuel = os.path.join(ws_scripts, script_a_modifier)
            with open(chemin_script_actuel, "r", encoding="utf-8") as f:
                contenu_actuel = f.read()

            nom_actuel = script_a_modifier.replace(".txt", "")
            nouveau_nom = st.text_input("Nom du script", nom_actuel)
            nouveau_contenu = st.text_area("Modifie ton texte...", value=contenu_actuel, height=300)

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
                if st.button("🗑️ SUPPRIMER", use_container_width=True):
                    os.remove(chemin_script_actuel)
                    st.error("Script supprimé !")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("Aucun script. Crées-en un nouveau !")


# ==========================================
# ONGLET 3 : GESTION DES MODÈLES
# ==========================================

elif menu == "📂 GESTION DES MODÈLES":
    st.header(f"📂 Ton Drive Privé ({username})")

    modeles = [d for d in os.listdir(ws_modeles) if os.path.isdir(os.path.join(ws_modeles, d))]

    if modeles:
        modele_choisi = st.selectbox("Sélectionner un Modèle :", modeles)
        chemin_modele = os.path.join(ws_modeles, modele_choisi)
        chemin_zip = os.path.join(ws_modeles, f"{modele_choisi}.zip")

        with st.expander("⚙️ Options (ZIP / Renommer / Supprimer / Upload Drive)", expanded=False):
            col_zip, col_edit1, col_edit2, col_drive = st.columns(4)

            with col_zip:
                st.write("📦 Exporter en ZIP :")
                if st.button("1. Préparer ZIP", use_container_width=True):
                    with st.spinner("Compression..."):
                        shutil.make_archive(chemin_modele, 'zip', chemin_modele)
                    st.success("✅ ZIP prêt !")
                if os.path.exists(chemin_zip):
                    with open(chemin_zip, "rb") as f:
                        st.download_button("2. 📥 Télécharger", f, file_name=f"{modele_choisi}.zip",
                                           mime="application/zip", use_container_width=True)

            with col_edit1:
                st.write("✏️ Renommer :")
                nouveau_nom_modele = st.text_input("", value=modele_choisi, label_visibility="collapsed")
                if st.button("Renommer", use_container_width=True):
                    if nouveau_nom_modele != modele_choisi:
                        nouveau_chemin = os.path.join(ws_modeles, nouveau_nom_modele)
                        os.rename(chemin_modele, nouveau_chemin)
                        if os.path.exists(chemin_zip): os.remove(chemin_zip)
                        st.success("Renommé !")
                        time.sleep(1)
                        st.rerun()

            with col_edit2:
                st.write("🗑️ Supprimer :")
                st.write("")
                if st.button("Supprimer TOUT", use_container_width=True):
                    shutil.rmtree(chemin_modele)
                    if os.path.exists(chemin_zip): os.remove(chemin_zip)
                    st.error(f"{modele_choisi} supprimé !")
                    time.sleep(1)
                    st.rerun()

            with col_drive:
                st.write("☁️ Upload Drive :")
                drive_service = drive_manager.get_drive_service(username)
                if drive_service:
                    dossiers = drive_manager.lister_dossiers_drive(drive_service)
                    options = {"📁 Racine": None}
                    for d in dossiers:
                        options[f"📂 {d['name']}"] = d['id']
                    dest = st.selectbox("Destination :", list(options.keys()), key="dest_modele")
                    dest_id = options[dest]

                    if st.button("📤 Envoyer sur Drive", use_container_width=True):
                        with st.spinner("Upload en cours..."):
                            status_up = st.empty()
                            folder_id = drive_manager.creer_dossier_drive(drive_service, modele_choisi, dest_id)
                            nb = drive_manager.uploader_videos_vers_drive(drive_service, chemin_modele, folder_id, status_up)
                            status_up.empty()
                        st.success(f"✅ {nb} vidéos envoyées sur Drive !")
                else:
                    st.warning("Connecte ton Drive dans la sidebar !")

        st.markdown("---")
        st.subheader(f"🎞️ Vidéos de {modele_choisi}")
        videos = [f for f in os.listdir(chemin_modele) if f.endswith(".mp4")]

        if videos:
            for f in videos:
                chemin_video_seule = os.path.join(chemin_modele, f)
                col_vid, col_down, col_del = st.columns([6, 2, 2])
                with col_vid:
                    st.write(f"▶️ {f}")
                with col_down:
                    with open(chemin_video_seule, "rb") as file:
                        st.download_button("📥 Télécharger", file, file_name=f,
                                           key=f"dl_{f}", use_container_width=True)
                with col_del:
                    if st.button("🗑️ Effacer", key=f"del_{f}", use_container_width=True):
                        os.remove(chemin_video_seule)
                        st.rerun()
        else:
            st.info("Aucune vidéo générée pour ce modèle.")
    else:
        st.write("Aucun modèle dans ton Drive privé.")
