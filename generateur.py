import os
import gc
import random
import uuid
import numpy as np
import warnings
import cv2
import re
import textwrap
from datetime import datetime, timedelta
from PIL import Image, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import AppleEmojiSource

warnings.filterwarnings("ignore")

from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, vfx

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


# ============================================================
# 🎯 DÉTECTION DE VISAGE
# ============================================================

def get_base_y_placement(video_path, canvas_h):
    safe_top = int(canvas_h * 0.22)
    safe_bottom = int(canvas_h * 0.68)
    fallback_y = safe_bottom
    try:
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        if not ret: return fallback_y
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 3)
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_y = (y + h/2) * (canvas_h / frame.shape[0])
            if face_y < canvas_h * 0.5: return safe_bottom
            else: return safe_top
        return fallback_y
    except: pass
    return fallback_y


# ============================================================
# 🎨 VARIATION STYLE TEXTE
# ============================================================

def varier_style_texte():
    couleurs = [
        (255, 255, 255),
        (255, 252, 245),
        (240, 240, 255),
        (255, 255, 230),
        (250, 248, 255),
    ]
    couleur = random.choice(couleurs)
    stroke = random.randint(3, 6)
    y_offset = random.randint(-25, 25)
    return couleur, stroke, y_offset


# ============================================================
# 🖼️ CRÉATION DU STICKER TEXTE
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
                pilmoji.text((x, start_y), l, font=font,
                    fill=couleur, stroke_width=stroke_w, stroke_fill="black")
            start_y += font_size + espacement

    return np.array(img)


# ============================================================
# 🧹 MÉTADONNÉES FALSIFIÉES
# ============================================================

def get_clean_ffmpeg_params():
    fake_date = datetime.now() - timedelta(
        days=random.randint(0, 30),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    fake_date_str = fake_date.strftime("%Y-%m-%dT%H:%M:%S")
    unique_id = uuid.uuid4().hex[:12]
    return [
        "-map_metadata", "-1",
        "-metadata", f"comment=EditID_{unique_id}",
        "-metadata", f"creation_time={fake_date_str}",
        "-preset", "ultrafast",
        "-tune", "fastdecode",
    ]


# ============================================================
# 🏭 MOTEUR PRINCIPAL
# ============================================================

def lancer_production_serie(chemin_video, chemin_captions, dossier_sortie,
                             n_to_make, modele_nom,
                             progress_bar=None, status_text=None, stop_event=None):

    with open(chemin_captions, "r", encoding="utf-8") as f:
        contenu = f.read()

    all_captions = [c.strip() for c in re.split(r'\n(?:[ \t]*\n){2,}', contenu) if c.strip()]
    if not all_captions:
        all_captions = ["Texte par défaut"]

    # Pré-chargement UNE SEULE FOIS
    clip_base = VideoFileClip(chemin_video)
    base_y = get_base_y_placement(chemin_video, clip_base.h)

    reels_reussis = 0

    for i in range(n_to_make):
        if stop_event and stop_event.is_set():
            break

        txt = all_captions[i % len(all_captions)]

        if status_text:
            status_text.text(f"⚡ [{i+1}/{n_to_make}] Production : {txt[:20]}...")

        video_reel = None
        txt_clip = None
        final = None

        try:
            # 1. Zoom léger
            zoom_factor = random.uniform(1.02, 1.04)
            video_reel = clip_base.resized(zoom_factor)

            # 2. Crop centré (sans décalage pour éviter les bords noirs)
            video_reel = video_reel.cropped(
                x_center=video_reel.w / 2,
                y_center=video_reel.h / 2,
                width=clip_base.w,
                height=clip_base.h
            )

            # 3. Miroir 1 sur 2 (rapide, pas de bords noirs)
            if i % 2 == 0:
                video_reel = video_reel.with_effects([vfx.MirrorX()])

            # 4. Coupure fin uniquement
            cut_time = random.uniform(0.05, 0.15)
            if video_reel.duration > cut_time + 0.5:
                video_reel = video_reel.subclipped(0, video_reel.duration - cut_time)

            # 5. Texte varié
            couleur, stroke, y_offset = varier_style_texte()
            txt_img = create_unique_text_sticker(
                txt, (clip_base.w, clip_base.h),
                base_y + y_offset, couleur=couleur, stroke_w=stroke
            )
            txt_clip = ImageClip(txt_img).with_duration(video_reel.duration)

            # 6. Composition finale
            final = CompositeVideoClip([video_reel, txt_clip])
            output_name = f"{modele_nom}_Reel_{i+1}_v{uuid.uuid4().hex[:6]}.mp4"

            # 7. Encodage ultra rapide
            final.write_videofile(
                os.path.join(dossier_sortie, output_name),
                codec="libx264",
                audio_codec="aac",
                fps=24,
                logger=None,
                ffmpeg_params=get_clean_ffmpeg_params()
            )

            reels_reussis += 1

        except Exception as e:
            print(f"Erreur variante {i+1} : {e}")

        finally:
            # Nettoyage mémoire forcé après chaque vidéo
            if final:
                try: final.close()
                except: pass
            if video_reel:
                try: video_reel.close()
                except: pass
            if txt_clip:
                try: txt_clip.close()
                except: pass
            try: del final, video_reel, txt_clip
            except: pass
            gc.collect()

        if progress_bar:
            progress_bar.progress(reels_reussis / n_to_make)

    clip_base.close()
    del clip_base
    gc.collect()
