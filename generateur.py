import os
import random
import numpy as np
import warnings
import cv2
import re  # <-- L'outil de lecture intelligent
from datetime import datetime
from PIL import Image, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import AppleEmojiSource 

warnings.filterwarnings("ignore")
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, vfx

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def get_base_y_placement(video_path, canvas_h):
    safe_top = int(canvas_h * 0.22)
    safe_bottom = int(canvas_h * 0.60)
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
    random_y_offset = random.randint(-15, 15)
    final_y = base_y + random_y_offset
    
    length = len(text.replace('\n', ' '))
    base_font_scale = canvas_w / 1080.0

    font_size = int(110 * base_font_scale) if length < 15 else (int(80 * base_font_scale) if length < 50 else int(60 * base_font_scale))
    font_size += random.randint(-3, 3)

    try: 
        font = ImageFont.truetype("arialrounded.ttf", font_size)
    except Exception as e: 
        print(f"Erreur police : {e}")
        font = ImageFont.load_default()

    with Pilmoji(img, source=AppleEmojiSource) as pilmoji:
        lines = []
        max_w = int(canvas_w * 0.85)
        
        # 🚨 LECTURE DES SAUTS DE LIGNE SIMPLES ET DOUBLES 🚨
        paragraphes = text.split('\n')
        
        for para in paragraphes:
            if not para.strip():
                lines.append("") # Maintient la ligne vide visuelle
                continue
                
            words = para.split()
            line = ""
            for w in words:
                test = line + " " + w if line else w
                if pilmoji.getsize(test, font=font)[0] < max_w: 
                    line = test
                else: 
                    lines.append(line)
                    line = w
            if line:
                lines.append(line)
        
        stroke_w = max(2, int(4 * base_font_scale))
        espacement = int(15 * base_font_scale)
        total_h = len(lines) * (font_size + espacement)
        start_y = final_y - (total_h // 2)

        for l in lines:
            if l != "": 
                w_t = pilmoji.getsize(l, font=font)[0]
                pilmoji.text(((canvas_w - w_t) // 2, start_y), l, font=font, 
                             fill="white", stroke_width=stroke_w, stroke_fill="black")
            start_y += font_size + espacement
            
    return np.array(img)

def lancer_production_serie(chemin_video, chemin_captions, dossier_sortie, n_to_make, modele_nom, progress_bar=None, status_text=None, stop_event=None):
    
    with open(chemin_captions, "r", encoding="utf-8") as f:
        contenu = f.read()
        # 🚨 LA MAGIE EST ICI : On coupe uniquement s'il y a 3 "Entrées" (2 lignes vides) 🚨
        all_captions = [c.strip() for c in re.split(r'\n(?:[ \t]*\n){2,}', contenu) if c.strip()]
    
    if not all_captions:
        all_captions = ["Texte par défaut"]

    clip_base = VideoFileClip(chemin_video)
    base_y = get_base_y_placement(chemin_video, clip_base.h)
    
    reels_reussis = 0

    for i in range(n_to_make):
        
        if stop_event and stop_event.is_set():
            print("Arrêt de la production demandé par l'utilisateur.")
            break

        txt = all_captions[i % len(all_captions)]
        
        if status_text:
            status_text.text(f"⚡ [{i+1}/{n_to_make}] Production de la variante : {txt[:20]}...")

        # --- PACK ANTI-BAN ---
        zoom_factor = random.uniform(1.02, 1.04)
        video_reel = clip_base.resized(zoom_factor)
        
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
            x_center=video_reel.w/2, 
            y_center=video_reel.h/2, 
            width=clip_base.w, 
            height=clip_base.h
        )
        
        cut_time = random.uniform(0.05, 0.25)
        video_reel = video_reel.subclipped(0, video_reel.duration - cut_time)

        txt_img = create_unique_text_sticker(txt, (clip_base.w, clip_base.h), base_y)
        txt_clip = ImageClip(txt_img).with_duration(video_reel.duration)
        final = CompositeVideoClip([video_reel, txt_clip])
        
        output_name = f"{modele_nom}_Reel_{i+1}_variant.mp4"
        clean_params = ["-map_metadata", "-1", "-metadata", f"comment=Generation_ID_{random.randint(10000,99999)}"]
        
        final.write_videofile(os.path.join(dossier_sortie, output_name), 
                              codec="libx264", audio_codec="aac", fps=24, logger=None,
                              ffmpeg_params=clean_params)
        
        reels_reussis += 1
        
        if progress_bar:
            progress_bar.progress(reels_reussis / n_to_make)

    clip_base.close()
