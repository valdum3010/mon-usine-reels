import os
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_FILE = "credentials.json"

# URI spéciale pour le mode copier-coller (pas de redirection)
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


# ============================================================
# 🔐 AUTHENTIFICATION GOOGLE DRIVE PAR UTILISATEUR
# ============================================================

def get_token_path(username):
    token_dir = f"Espace_{username}"
    os.makedirs(token_dir, exist_ok=True)
    return os.path.join(token_dir, "token_drive.json")


def get_drive_service(username):
    token_path = get_token_path(username)
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

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


def get_auth_url():
    """Génère l'URL d'autorisation Google en mode copier-coller."""
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )
    return auth_url


def save_token_from_code(username, code):
    """Échange le code copié-collé contre un token et le sauvegarde."""
    try:
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(code=code.strip())
        creds = flow.credentials
        token_path = get_token_path(username)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
        return True
    except Exception as e:
        print(f"Erreur token : {e}")
        return False


def disconnect_drive(username):
    token_path = get_token_path(username)
    if os.path.exists(token_path):
        os.remove(token_path)


# ============================================================
# 📂 GESTION DES DOSSIERS DRIVE
# ============================================================

def lister_dossiers_drive(service):
    try:
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)",
            pageSize=50
        ).execute()
        return results.get("files", [])
    except Exception as e:
        print(f"Erreur listing dossiers : {e}")
        return []


def creer_dossier_drive(service, nom_dossier, parent_id=None):
    try:
        metadata = {
            "name": nom_dossier,
            "mimeType": "application/vnd.google-apps.folder"
        }
        if parent_id:
            metadata["parents"] = [parent_id]
        dossier = service.files().create(body=metadata, fields="id").execute()
        return dossier.get("id")
    except Exception as e:
        print(f"Erreur création dossier : {e}")
        return None


# ============================================================
# 📤 UPLOAD DES VIDÉOS
# ============================================================

def uploader_videos_vers_drive(service, dossier_local, dossier_drive_id, status_text=None):
    videos = [f for f in os.listdir(dossier_local) if f.endswith(".mp4")]
    if not videos:
        return 0

    reussis = 0
    for i, video in enumerate(videos):
        chemin_local = os.path.join(dossier_local, video)
        if status_text:
            status_text.text(f"☁️ Upload {i+1}/{len(videos)} : {video}...")
        try:
            file_metadata = {"name": video, "parents": [dossier_drive_id]}
            media = MediaFileUpload(chemin_local, mimetype="video/mp4", resumable=True)
            service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()
            reussis += 1
        except Exception as e:
            print(f"Erreur upload {video} : {e}")

    return reussis
