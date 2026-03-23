import streamlit as st
import os, shutil, time, threading
from datetime import datetime
from utilisateurs import USERS 
from generateur import lancer_production_serie

# --- CONFIGURATION & LOOK ---
st.set_page_config(page_title="OR D'USINE | AI Studio", page_icon="💎", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0e1117 0%, #1a1c24 100%); }
    .stButton>button {
        border-radius: 12px;
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
        color: white; border: none; padding: 10px 24px; font-weight: bold; transition: all 0.3s ease;
    }
    [data-testid="stExpander"] { background-color: #1e222d !important; border: 1px solid #30363d !important; border-radius: 15px !important; }
    [data-testid="stSidebar"] { background-color: #0e1117 !important; border-right: 1px solid #30363d; }
    h1 { background: -webkit-linear-gradient(#fff, #99aab5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

# --- FONCTION DE MIGRATION AUTOMATIQUE ---
def migrer_anciens_fichiers(user_name):
    """Déplace les fichiers orphelins vers le dossier de l'utilisateur admin par défaut"""
    base_reels = "Output_Reels"
    base_caps = "CAPTIONS_STORAGE"
    
    target_reels = os.path.join(base_reels, user_name)
    target_caps = os.path.join(base_caps, user_name)
    
    os.makedirs(target_reels, exist_ok=True)
    os.makedirs(target_caps, exist_ok=True)

    # Si c'est l'admin, on récupère tout ce qui traîne à la racine
    if user_name == "admin":
        # Migration des Captions (.txt à la racine de CAPTIONS_STORAGE)
        for f in os.listdir(base_caps):
            full_path = os.path.join(base_caps, f)
            if os.path.isfile(full_path) and f.endswith(".txt"):
                shutil.move(full_path, os.path.join(target_caps, f))
        
        # Migration des Reels (Dossiers à la racine de Output_Reels)
        for d in os.listdir(base_reels):
            full_path = os.path.join(base_reels, d)
            # On déplace si c'est un dossier et que ce n'est pas un dossier utilisateur existant
            if os.path.isdir(full_path) and d not in USERS and d != user_name:
                try:
                    shutil.move(full_path, os.path.join(target_reels, d))
                except: pass

# --- SYSTÈME DE LOGIN ---
def login():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        col_l, col_c, col_r = st.columns([1,2,1])
        with col_c:
            st.markdown("<h1 style='text-align: center;'>💎 OR D'USINE</h1>", unsafe_allow_html=True)
            user = st.text_input("Identifiant")
            pw = st.text_input("Mot de passe", type="password")
            if st.button("DÉVERROUILLER", use_container_width=True):
                if user in USERS and USERS[user] == pw:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user
                    # LANCER LA MIGRATION ICI
                    migrer_anciens_fichiers(user)
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
        st.stop()

login()
user_actif = st.session_state["username"]

# --- SETUP DOSSIERS UTILISATEUR ---
user_reels_path = os.path.join("Output_Reels", user_actif)
user_captions_path = os.path.join("CAPTIONS_STORAGE", user_actif)
os.makedirs(user_reels_path, exist_ok=True)
os.makedirs(user_captions_path, exist_ok=True)

# --- SIDEBAR ---
st.sidebar.markdown(f"<h2 style='color: #a855f7;'>👤 {user_actif.upper()}</h2>", unsafe_allow_html=True)
page = st.sidebar.radio("MENU", ["🚀 PRODUCTION", "✍️ CAPTIONS", "📁 MON DRIVE"])
if st.sidebar.button("Déconnexion"):
    st.session_state["authenticated"] = False
    st.rerun()

# ==========================================
# PAGE 1 : PRODUCTION
# ==========================================
if page == "🚀 PRODUCTION":
    st.title("🚀 Nouvelle Campagne")
    col1, col2 = st.columns(2)
    with col1:
        archive_nom = st.text_input("Nom de la session", placeholder="Ex: Projet_X")
        nb_reels = st.number_input("Nombre de vidéos", min_value=1, value=10)
    with col2:
        fichiers_txt = [f for f in os.listdir(user_captions_path) if f.endswith('.txt')]
        cap_select = st.selectbox("📂 Fichier texte", ["Aucun"] + fichiers_txt)
        vid_file = st.file_uploader("🎬 Vidéo source", type=["mp4"])

    if st.button("LANCER LA FABRICATION", type="primary", use_container_width=True):
        if not vid_file or cap_select == "Aucun":
            st.error("⚠️ Manque vidéo ou texte !")
        else:
            path_in = os.path.join("inputs", f"{user_actif}_{vid_file.name}")
            with open(path_in, "wb") as f: f.write(vid_file.getbuffer())
            
            sess_nom = archive_nom if archive_nom else f"Sess_{int(time.time())}"
            path_out = os.path.join(user_reels_path, sess_nom)
            os.makedirs(path_out, exist_ok=True)
            
            stop_ev = threading.Event()
            st.session_state['stop_ev'] = stop_ev
            
            def travail_bg():
                try:
                    lancer_production_serie(path_in, os.path.join(user_captions_path, cap_select), path_out, nb_reels, user_actif, stop_event=stop_ev)
                finally:
                    if os.path.exists(path_in): os.remove(path_in)

            threading.Thread(target=travail_bg).start()
            st.success("C'est en cuisine ! Suis l'avancée ci-dessous.")
            st.session_state['en_cours'] = path_out
            st.session_state['total'] = nb_reels

    if 'en_cours' in st.session_state:
        d, t = st.session_state['en_cours'], st.session_state['total']
        if os.path.exists(d):
            finis = len([f for f in os.listdir(d) if f.endswith('.mp4')])
            st.progress(finis/t)
            st.write(f"Vidéos prêtes : {finis}/{t}")
            if st.button("🛑 ARRÊTER"): 
                st.session_state['stop_ev'].set()
                del st.session_state['en_cours']; st.rerun()

# ==========================================
# PAGE 2 : CAPTIONS
# ==========================================
elif page == "✍️ CAPTIONS":
    st.title("✍️ Gestion des Captions")
    fichiers = [f for f in os.listdir(user_captions_path) if f.endswith('.txt')]
    choix = st.selectbox("📂 Charger un fichier :", ["➕ Nouveau..."] + fichiers)
    
    n_init = choix if choix != "➕ Nouveau..." else ""
    cont_init = ""
    if choix != "➕ Nouveau...":
        with open(os.path.join(user_captions_path, choix), "r", encoding="utf-8") as f:
            cont_init = f.read()

    nom_f = st.text_input("Nom du fichier (.txt)", value=n_init)
    txt_f = st.text_area("Texte", value=cont_init, height=300)
    
    b1, b2 = st.columns([4,1])
    with b1:
        if st.button("💾 Sauvegarder", use_container_width=True, type="primary"):
            full_n = nom_f if nom_f.endswith(".txt") else nom_f + ".txt"
            with open(os.path.join(user_captions_path, full_n), "w", encoding="utf-8") as f:
                f.write(txt_f)
            st.success("Enregistré !")
            time.sleep(1); st.rerun()
    with b2:
        if choix != "➕ Nouveau..." and st.button("🗑️", use_container_width=True):
            os.remove(os.path.join(user_captions_path, choix)); st.rerun()

# ==========================================
# PAGE 3 : MON DRIVE
# ==========================================
elif page == "📁 MON DRIVE":
    st.title("📁 Ton Drive Personnel")
    sessions = [s for s in os.listdir(user_reels_path) if os.path.isdir(os.path.join(user_reels_path, s))]
    
    if not sessions:
        st.info("Aucune session trouvée.")
        
    for s in sessions:
        path_s = os.path.join(user_reels_path, s)
        reels = [f for f in os.listdir(path_s) if f.endswith('.mp4')]
        with st.expander(f"📦 {s} ({len(reels)} vidéos)"):
            c1, c2 = st.columns(2)
            with c1:
                path_z = path_s + ".zip"
                if st.button("🗜️ Créer ZIP", key=f"z_{s}"):
                    shutil.make_archive(path_s, 'zip', path_s); st.rerun()
                if os.path.exists(path_z):
                    with open(path_z, "rb") as fz:
                        st.download_button("📥 Télécharger ZIP", fz, file_name=f"{s}.zip", key=f"dl_z_{s}")
            with c2:
                if st.button("🗑️ Supprimer", key=f"del_s_{s}"):
                    shutil.rmtree(path_s)
                    if os.path.exists(path_z): os.remove(path_z)
                    st.rerun()
            st.markdown("---")
            for r in reels:
                path_r = os.path.join(path_s, r)
                cr1, cr2 = st.columns([4, 1])
                with cr1: st.write(f"🎬 `{r}`")
                with cr2:
                    with open(path_r, "rb") as fr:
                        st.download_button("⬇️", fr, file_name=r, key=f"dl_r_{s}_{r}")