import os
import random
import numpy as np
import warnings
import cv2
from datetime import datetime
from PIL import Image, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import AppleEmojiSource 

warnings.filterwarnings("ignore")
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, vfx

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def get_base_y_placement(video_path, canvas_h):
    # --- VRAIES MARGES DE SÉCURITÉ TIKTOK/REELS ---
    safe_top = int(canvas_h * 0.22)    # 22% du haut (Juste sous les menus)
    safe_bottom = int(canvas_h * 0.60) # 60% du haut (Juste au-dessus de la description)
    
    # Par défaut, on force dans la zone safe du BAS (car la tête est presque toujours en haut)
    fallback_y = safe_bottom 

    try:
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        
        if not ret: return fallback_y
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Scanner de visage
        faces = face_cascade.detectMultiScale(gray, 1.1, 3)
        
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_y = (y + h/2) * (canvas_h / frame.shape[0])
            
            # Si le visage est dans la moitié haute, le texte va dans la zone safe du BAS
            if face_y < canvas_h * 0.5: 
                return safe_bottom 
            else: 
                return safe_top 
                
        # Si le scanner rate (visage tourné, etc.), on applique le fallback en bas
        return fallback_y
        
    except: pass
    return fallback_y

def create_unique_text_sticker(text, reel_size, base_y):
    canvas_w, canvas_h = reel_size
    img = Image.new('RGBA', reel_size, (0, 0, 0, 0))
    random_y_offset = random.randint(-15, 15)
    final_y = base_y + random_y_offset
    length = len(text)
    
    # On se base sur la largeur pour que le texte s'adapte parfaitement
    base_font_scale = canvas_w / 1080.0

    # --- NOUVELLES TAILLES (Propres, lisibles, pas abusées) ---
    font_size = int(110 * base_font_scale) if length < 15 else (int(80 * base_font_scale) if length < 50 else int(60 * base_font_scale))
    font_size += random.randint(-3, 3)

    # 🚨 Pense bien à uploader IMPACT.TTF sur ton GitHub et à changer le nom ici si tu veux enlever l'italique !
    try: 
        font = ImageFont.truetype("ARIALNBI.TTF", font_size)
    except Exception as e: 
        print(f"Erreur police : {e}")
        font = ImageFont.load_default()

    with Pilmoji(img, source=AppleEmojiSource) as pilmoji:
        lines = []
        # Marge de sécurité latérale (max 85% de l'écran en largeur)
        max_w = int(canvas_w * 0.85)
        words = text.split()
        line = ""
        for w in words:
            test = line + " " + w if line else w
            if pilmoji.getsize(test, font=font)[0] < max_w: line = test
            else: lines.append(line); line = w
        lines.append(line)
        
        # Contour noir proportionnel (plus fin pour un rendu plus propre)
        stroke_w = max(2, int(4 * base_font_scale))
        
        # Espacement entre les lignes
        espacement = int(15 * base_font_scale)
        total_h = len(lines) * (font_size + espacement)
        start_y = final_y - (total_h // 2)

        for l in lines:
            w_t = pilmoji.getsize(l, font=font)[0]
            # Dessin du texte au centre
            pilmoji.text(((canvas_w - w_t) // 2, start_y), l, font=font, 
                         fill="white", stroke_width=stroke_w, stroke_fill="black")
            start_y += font_size + espacement
            
    return np.array(img)

def lancer_production_serie(chemin_video, chemin_captions, dossier_sortie, n_to_make, modele_nom, progress_bar=None, status_text=None, stop_event=None):
    
    with open(chemin_captions, "r", encoding="utf-8") as f:
        all_captions = [c.strip() for c in f.read().split('\n\n') if c.strip()]
    
    if not all_captions:
        all_captions = ["Texte par défaut"]

    clip_base = VideoFileClip(chemin_video)
    
    # 📏 Calcul du placement initial (esquive visage et zones safe)
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

        # Rendu du texte avec esquive de visage et marges de sécurité
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
