import os
import json
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_FILE = "credentials.json"


# ============================================================
# 🔐 AUTHENTIFICATION GOOGLE DRIVE PAR UTILISATEUR
# ============================================================

def get_token_path(username):
    """Chaque utilisateur a son propre token stocké séparément."""
    token_dir = f"Espace_{username}"
    os.makedirs(token_dir, exist_ok=True)
    return os.path.join(token_dir, "token_drive.json")


def get_drive_service(username):
    """Retourne le service Google Drive si l'utilisateur est connecté, sinon None."""
    token_path = get_token_path(username)
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # Refresh automatique si le token est expiré
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        except:
            creds = None

    if creds and creds.valid:
        return build("drive", "v3", credentials=creds)

    return None


def get_auth_url(username):
    """Génère l'URL d'authentification Google OAuth2."""
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri="http://localhost:8501"
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    st.session_state[f"oauth_state_{username}"] = state
    st.session_state[f"oauth_flow_{username}"] = flow
    return auth_url


def save_token_from_code(username, code):
    """Échange le code OAuth contre un token et le sauvegarde."""
    try:
        flow = st.session_state.get(f"oauth_flow_{username}")
        if not flow:
            flow = Flow.from_client_secrets_file(
                CREDENTIALS_FILE,
                scopes=SCOPES,
                redirect_uri="http://localhost:8501"
            )
        flow.fetch_token(code=code)
        creds = flow.credentials
        token_path = get_token_path(username)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
        return True
    except Exception as e:
        print(f"Erreur token : {e}")
        return False


def disconnect_drive(username):
    """Déconnecte l'utilisateur de Google Drive."""
    token_path = get_token_path(username)
    if os.path.exists(token_path):
        os.remove(token_path)


# ============================================================
# 📂 GESTION DES DOSSIERS DRIVE
# ============================================================

def lister_dossiers_drive(service):
    """Liste tous les dossiers disponibles sur le Drive de l'utilisateur."""
    try:
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)",
            pageSize=50
        ).execute()
        dossiers = results.get("files", [])
        return dossiers  # [{"id": "...", "name": "..."}, ...]
    except Exception as e:
        print(f"Erreur listing dossiers : {e}")
        return []


def creer_dossier_drive(service, nom_dossier, parent_id=None):
    """Crée un dossier sur Google Drive et retourne son ID."""
    try:
        metadata = {
            "name": nom_dossier,
            "mimeType": "application/vnd.google-apps.folder"
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        dossier = service.files().create(
            body=metadata,
            fields="id"
        ).execute()
        return dossier.get("id")
    except Exception as e:
        print(f"Erreur création dossier : {e}")
        return None


# ============================================================
# 📤 UPLOAD DES VIDÉOS
# ============================================================

def uploader_videos_vers_drive(service, dossier_local, dossier_drive_id, status_text=None):
    """Upload toutes les vidéos MP4 d'un dossier local vers Google Drive."""
    videos = [f for f in os.listdir(dossier_local) if f.endswith(".mp4")]

    if not videos:
        return 0

    reussis = 0
    for i, video in enumerate(videos):
        chemin_local = os.path.join(dossier_local, video)

        if status_text:
            status_text.text(f"☁️ Upload {i+1}/{len(videos)} : {video}...")

        try:
            file_metadata = {
                "name": video,
                "parents": [dossier_drive_id]
            }
            media = MediaFileUpload(
                chemin_local,
                mimetype="video/mp4",
                resumable=True  # Upload résumable pour les gros fichiers
            )
            service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()
            reussis += 1
        except Exception as e:
            print(f"Erreur upload {video} : {e}")

    return reussis
