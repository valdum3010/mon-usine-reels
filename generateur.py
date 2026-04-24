import os
import random
import numpy as np
import warnings
import cv2
import re
import textwrap
from datetime import datetime
from PIL import Image, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import AppleEmojiSource

warnings.filterwarnings("ignore")

from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, vfx

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

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

def create_unique_text_sticker(text, reel_size, base_y):
    canvas_w, canvas_h = reel_size
    img = Image.new('RGBA', reel_size, (0, 0, 0, 0))

    final_y = int(canvas_h * 0.68) + random.randint(-15, 15)
    length = len(text.replace('\n', ' '))
    base_font_scale = canvas_w / 1080.0

    font_size = int(80 * base_font_scale) if length < 15 else (int(60 * base_font_scale) if length < 50 else int(45 * base_font_scale))
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

        stroke_w = max(3, int(5 * base_font_scale))
        espacement = int(10 * base_font_scale)
        total_h = len(lines) * (font_size + espacement)
        start_y = final_y - (total_h // 2)

        for l in lines:
            if l != "":
                w_t = pilmoji.getsize(l, font=font)[0]
                x = (canvas_w - w_t) // 2
                pilmoji.text((x, start_y), l, font=font,
                             fill="white", stroke_width=stroke_w, stroke_fill="black")
            start_y += font_size + espacement

    return np.array(img)

def lancer_production_serie(chemin_video, chemin_captions, dossier_sortie, n_to_make, modele_nom, progress_bar=None, status_text=None, stop_event=None):

    # =============================================
    # DURÉE CIBLE : entre 6.0 et 8.0 secondes
    DUREE_MIN = 6.0
    DUREE_MAX = 8.0
    # =============================================

    with open(chemin_captions, "r", encoding="utf-8") as f:
        contenu = f.read()

    all_captions = [c.strip() for c in re.split(r'\n(?:[ \t]*\n){2,}', contenu) if c.strip()]
    if not all_captions:
        all_captions = ["Texte par défaut"]

    # On lit juste la durée et les dimensions de la vidéo source
    clip_info = VideoFileClip(chemin_video)
    duree_source = clip_info.duration
    canvas_w = clip_info.w
    canvas_h = clip_info.h
    clip_info.close()
    del clip_info

    base_y = get_base_y_placement(chemin_video, canvas_h)

    reels_reussis = 0

    for i in range(n_to_make):
        if stop_event and stop_event.is_set():
            print("Arrêt de la production demandé.")
            break

        txt = all_captions[i % len(all_captions)]

        if status_text:
            status_text.text(f"⚡ [{i+1}/{n_to_make}] Production de la variante : {txt[:20]}...")

        # --- DURÉE ALÉATOIRE ENTRE 6 ET 8 SECONDES ---
        duree_cible = round(random.uniform(DUREE_MIN, DUREE_MAX), 2)

        if duree_source <= DUREE_MIN:
            start_time = 0
            end_time = duree_source - 0.05
        else:
            max_start = duree_source - duree_cible
            if max_start > 0:
                start_time = round(random.uniform(0, max_start), 2)
            else:
                start_time = 0
                duree_cible = duree_source - 0.05
            end_time = start_time + duree_cible

        # --- ON RECHARGE LA VIDÉO PROPREMENT À CHAQUE VARIANTE ---
        # Couper D'ABORD pour éviter la désynchronisation audio
        clip_base = VideoFileClip(chemin_video)
        video_reel = clip_base.subclipped(start_time, end_time)

        # Ensuite on applique les effets visuels
        zoom_factor = random.uniform(1.02, 1.04)
        video_reel = video_reel.resized(zoom_factor)

        active_effects = []
        if i % 2 == 0:
            active_effects.append(vfx.MirrorX())
        try:
            active_effects.append(vfx.Colorx(random.uniform(0.99, 1.01)))
        except:
            pass

        if active_effects:
            video_reel = video_reel.with_effects(active_effects)

        video_reel = video_reel.cropped(
            x_center=video_reel.w / 2,
            y_center=video_reel.h / 2,
            width=canvas_w,
            height=canvas_h
        )

        txt_img = create_unique_text_sticker(txt, (canvas_w, canvas_h), base_y)
        txt_clip = ImageClip(txt_img).with_duration(video_reel.duration)

        final = CompositeVideoClip([video_reel, txt_clip])

        output_name = f"{modele_nom}_Reel_{i+1}_variant.mp4"

        # Métadonnées 100% uniques par variante
        gen_id = random.randint(100000, 999999)
        timestamp_unique = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        clean_params = [
            "-map_metadata", "-1",
            "-metadata", f"comment=Gen_{gen_id}_{timestamp_unique}",
            "-metadata", f"title=Reel_{i+1}_{random.randint(1000,9999)}",
            "-metadata", f"creation_time={datetime.utcnow().isoformat()}",
        ]

        final.write_videofile(
            os.path.join(dossier_sortie, output_name),
            codec="libx264",
            audio_codec="aac",
            fps=24,
            logger=None,
            ffmpeg_params=clean_params
        )

        # Nettoyage mémoire complet à chaque variante
        final.close()
        video_reel.close()
        txt_clip.close()
        clip_base.close()
        del final, video_reel, txt_clip, clip_base

        reels_reussis += 1

        if progress_bar:
            progress_bar.progress(reels_reussis / n_to_make)
