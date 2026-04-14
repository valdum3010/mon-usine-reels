import os
import random
import uuid
import numpy as np
import warnings
import cv2
import re
import textwrap
from datetime import datetime, timedelta
from PIL import Image, ImageFont, ImageFilter, ImageEnhance
from pilmoji import Pilmoji
from pilmoji.source import AppleEmojiSource

warnings.filterwarnings("ignore")

from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, vfx

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


# ============================================================
# 🎯 DÉTECTION DE VISAGE (inchangé, déjà bien)
# ============================================================

def get_base_y_placement(video_path, canvas_h):
    safe_top = int(canvas_h * 0.22)
    safe_bottom = int(canvas_h * 0.68)
    fallback_y = safe_bottom
    try:
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return fallback_y
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 3)
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_y = (y + h / 2) * (canvas_h / frame.shape[0])
            if face_y < canvas_h * 0.5:
                return safe_bottom
            else:
                return safe_top
        return fallback_y
    except:
        pass
    return fallback_y


# ============================================================
# 🎨 VARIATION 1 : Style du texte (couleur + contour + position)
# ============================================================

def varier_style_texte():
    """Retourne une couleur de texte, épaisseur de contour et décalage Y aléatoires."""
    couleurs = [
        (255, 255, 255),   # Blanc pur
        (255, 252, 245),   # Blanc chaud
        (240, 240, 255),   # Blanc froid
        (255, 255, 230),   # Blanc jaunâtre
        (250, 248, 255),   # Blanc légèrement lavande
    ]
    couleur = random.choice(couleurs)
    stroke = random.randint(3, 6)
    y_offset = random.randint(-25, 25)
    return couleur, stroke, y_offset


# ============================================================
# 🖼️ CRÉATION DU STICKER TEXTE (amélioré)
# ============================================================

def create_unique_text_sticker(text, reel_size, base_y, couleur=(255, 255, 255), stroke_w=5):
    canvas_w, canvas_h = reel_size
    img = Image.new('RGBA', reel_size, (0, 0, 0, 0))

    final_y = int(canvas_h * 0.68) + random.randint(-15, 15)

    length = len(text.replace('\n', ' '))
    base_font_scale = canvas_w / 1080.0

    font_size = (
        int(80 * base_font_scale) if length < 15
        else int(60 * base_font_scale) if length < 50
        else int(45 * base_font_scale)
    )
    font_size += random.randint(-3, 3)

    try:
        font = ImageFont.truetype("arialrounded.ttf", font_size)
    except Exception as e:
        print(f"Erreur police : {e}")
        font = ImageFont.load_default()

    with Pilmoji(img, source=AppleEmojiSource) as pilmoji:
        lines = []
        paragraphes = text.split('\n')
        for para in paragraphes:
            if not para.strip():
                lines.append("")
                continue
            lignes_coupees = textwrap.wrap(para, width=22)
            lines.extend(lignes_coupees)

        espacement = int(10 * base_font_scale)
        total_h = len(lines) * (font_size + espacement)
        start_y = final_y - (total_h // 2)

        for l in lines:
            if l != "":
                w_t = pilmoji.getsize(l, font=font)[0]
                x = (canvas_w - w_t) // 2
                pilmoji.text(
                    (x, start_y), l,
                    font=font,
                    fill=couleur,
                    stroke_width=stroke_w,
                    stroke_fill="black"
                )
            start_y += font_size + espacement

    return np.array(img)


# ============================================================
# 🔄 VARIATION 2 : Effets visuels sur la vidéo
# ============================================================

def appliquer_variations_visuelles(clip, index):
    """Applique un ensemble d'effets visuels aléatoires pour différencier chaque variante."""
    effets = []

    # Miroir horizontal (une variante sur deux)
    if index % 2 == 0:
        effets.append(vfx.MirrorX())

    # Variation de luminosité/saturation
    try:
        effets.append(vfx.Colorx(random.uniform(0.97, 1.03)))
    except:
        pass

    # Rotation très légère (change le hash sans être visible)
    try:
        angle = random.uniform(-0.6, 0.6)
        effets.append(vfx.Rotate(angle))
    except:
        pass

    if effets:
        clip = clip.with_effects(effets)

    # Variation de vitesse légère (±2%)
    speed_factor = random.uniform(0.98, 1.02)
    try:
        clip = clip.with_speed_scaled(speed_factor)
    except:
        pass

    return clip


# ============================================================
# ✂️ VARIATION 3 : Recadrage aléatoire (crop unique à chaque variante)
# ============================================================

def recadrage_aleatoire(clip):
    """Décale légèrement le cadrage pour créer une empreinte vidéo unique."""
    w, h = clip.w, clip.h
    offset_x = random.randint(-int(w * 0.02), int(w * 0.02))
    offset_y = random.randint(-int(h * 0.02), int(h * 0.02))

    zoom = random.uniform(1.02, 1.05)
    clip = clip.resized(zoom)

    clip = clip.cropped(
        x_center=(clip.w / 2) + offset_x,
        y_center=(clip.h / 2) + offset_y,
        width=w,
        height=h
    )
    return clip


# ============================================================
# 🎞️ VARIATION 4 : Paramètres d'encodage variables
# ============================================================

def get_encoding_params():
    """Varie le bitrate et les FPS pour que chaque fichier ait une signature différente."""
    bitrate = random.choice(["3800k", "4000k", "4200k", "4500k", "4700k"])
    fps = random.choice([23.976, 24, 25, 29.97])
    return bitrate, fps


# ============================================================
# 🧹 VARIATION 5 : Métadonnées nettoyées et falsifiées
# ============================================================

def get_clean_ffmpeg_params():
    """Supprime les vraies métadonnées et injecte de fausses données aléatoires."""
    fake_date = datetime.now() - timedelta(days=random.randint(0, 30),
                                            hours=random.randint(0, 23),
                                            minutes=random.randint(0, 59))
    fake_date_str = fake_date.strftime("%Y-%m-%dT%H:%M:%S")
    unique_id = uuid.uuid4().hex[:12]
    encoder_version = f"{random.randint(1,9)}.{random.randint(0,9)}.{random.randint(0,99)}"

    return [
        "-map_metadata", "-1",
        "-metadata", f"comment=EditID_{unique_id}",
        "-metadata", f"creation_time={fake_date_str}",
        "-metadata", f"encoder=MediaEncoder_{encoder_version}",
        "-metadata", f"handler_name=VideoHandler_{random.randint(100,999)}",
    ]


# ============================================================
# 🏭 MOTEUR PRINCIPAL DE PRODUCTION
# ============================================================

def lancer_production_serie(chemin_video, chemin_captions, dossier_sortie,
                             n_to_make, modele_nom,
                             progress_bar=None, status_text=None, stop_event=None):

    with open(chemin_captions, "r", encoding="utf-8") as f:
        contenu = f.read()

    all_captions = [c.strip() for c in re.split(r'\n(?:[ \t]*\n){2,}', contenu) if c.strip()]
    if not all_captions:
        all_captions = ["Texte par défaut"]

    clip_base = VideoFileClip(chemin_video)
    base_y = get_base_y_placement(chemin_video, clip_base.h)

    reels_reussis = 0

    for i in range(n_to_make):

        if stop_event and stop_event.is_set():
            print("Arrêt de la production demandé.")
            break

        txt = all_captions[i % len(all_captions)]

        if status_text:
            status_text.text(f"⚡ [{i+1}/{n_to_make}] Production : {txt[:20]}...")

        # --- ÉTAPE 1 : Effets visuels ---
        video_reel = appliquer_variations_visuelles(clip_base, i)

        # --- ÉTAPE 2 : Recadrage unique ---
        video_reel = recadrage_aleatoire(video_reel)

        # --- ÉTAPE 3 : Coupure début ET fin aléatoire ---
        cut_start = random.uniform(0.0, 0.15)
        cut_end = random.uniform(0.05, 0.25)
        if video_reel.duration > (cut_start + cut_end + 0.5):
            video_reel = video_reel.subclipped(cut_start, video_reel.duration - cut_end)

        # --- ÉTAPE 4 : Texte avec style varié ---
        couleur, stroke, y_offset = varier_style_texte()
        txt_img = create_unique_text_sticker(
            txt,
            (clip_base.w, clip_base.h),
            base_y + y_offset,
            couleur=couleur,
            stroke_w=stroke
        )
        txt_clip = ImageClip(txt_img).with_duration(video_reel.duration)

        # --- ÉTAPE 5 : Encodage avec paramètres variables ---
        bitrate, fps = get_encoding_params()
        final = CompositeVideoClip([video_reel, txt_clip])

        output_name = f"{modele_nom}_Reel_{i+1}_v{uuid.uuid4().hex[:6]}.mp4"

        final.write_videofile(
            os.path.join(dossier_sortie, output_name),
            codec="libx264",
            audio_codec="aac",
            fps=fps,
            bitrate=bitrate,
            logger=None,
            ffmpeg_params=get_clean_ffmpeg_params()
        )

        # --- NETTOYAGE MÉMOIRE ---
        final.close()
        video_reel.close()
        txt_clip.close()
        del final, video_reel, txt_clip

        reels_reussis += 1

        if progress_bar:
            progress_bar.progress(reels_reussis / n_to_make)

    clip_base.close()
    del clip_base
