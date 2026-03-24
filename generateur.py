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
    try:
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        
        # Par défaut, on place en haut (environ 15% de l'écran)
        default_top = int(canvas_h * 0.15)
        default_bottom = int(canvas_h * 0.75)
        
        if not ret: return default_top
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_y = (y + h/2) * (canvas_h / frame.shape[0])
            # Si le visage est en haut, on met le texte en bas, et inversement
            if face_y < canvas_h * 0.45: return default_bottom 
            else: return default_top 
    except: pass
    return int(canvas_h * 0.15) 

def create_unique_text_sticker(text, reel_size, base_y):
    canvas_w, canvas_h = reel_size
    img = Image.new('RGBA', reel_size, (0, 0, 0, 0))
    # Réduction de l'offset aléatoire pour OFM plus propre
    random_y_offset = random.randint(-20, 20)
    final_y = base_y + random_y_offset
    length = len(text)
    
    # --- CALCUL Master Force OFM ---
    # On cale la police sur la hauteur (1920px type), c'est plus stable
    # et on force une taille de base OFM MASSIVE
    
    # 📏 Calcul OFM Géant relatif à une hauteur type de 1920px vertical
    scale_factor = canvas_h / 1920.0
    # On assure une échelle minimale pour les basses résolutions
    base_ofm_scale = max(0.5, scale_factor)

    # 📏 LES NOUVELLES BASES Master Force OFM (Pour un Reels de 1920h)
    font_size = int(300 * base_ofm_scale) if length < 15 else (int(200 * base_ofm_scale) if length < 50 else int(150 * base_ofm_scale))
    font_size += random.randint(-5, 5)

    try: font = ImageFont.truetype("arial.ttf", font_size)
    except: font = ImageFont.load_default()

    with Pilmoji(img, source=AppleEmojiSource) as pilmoji:
        lines = []
        max_w = int(canvas_w * 0.9) # Plus de marge pour OFM
        words = text.split()
        line = ""
        for w in words:
            test = line + " " + w if line else w
            if pilmoji.getsize(test, font=font)[0] < max_w: line = test
            else: lines.append(line); line = w
        lines.append(line)
        
        # Stroke dynamique renforcé pour OFM ( visible sur blanc/noir )
        stroke_w = max(2, int(6 * base_ofm_scale))
        total_h = len(lines) * (font_size + 20)
        start_y = final_y - (total_h // 2)

        for l in lines:
            w_t = pilmoji.getsize(l, font=font)[0]
            pilmoji.text(((canvas_w - w_t) // 2, start_y), l, font=font, 
                         fill="white", stroke_width=stroke_w, stroke_fill="black")
            start_y += font_size + 20
            
    return np.array(img)

def lancer_production_serie(chemin_video, chemin_captions, dossier_sortie, n_to_make, modele_nom, stop_event=None):
    
    with open(chemin_captions, "r", encoding="utf-8") as f:
        all_captions = [c.strip() for c in f.read().split('\n\n') if c.strip()]
    
    if not all_captions:
        all_captions = ["Texte par défaut"]

    clip_base = VideoFileClip(chemin_video)
    
    # 📏 On calcule le placement selon la VRAIE hauteur de la vidéo
    base_y = get_base_y_placement(chemin_video, clip_base.h)
    
    reels_reussis = 0

    for i in range(n_to_make):
        
        # 🛑 VÉRIFICATION DU BOUTON STOP AVANT CHAQUE NOUVEAU REEL
        if stop_event and stop_event.is_set():
            print("Arrêt de la production demandé par l'utilisateur.")
            break

        txt = all_captions[i % len(all_captions)]
        
        # --- PACK ANTI-BAN CORRIGÉ ---
        zoom_factor = random.uniform(1.02, 1.04)
        
        # 1. Zoom proportionnel (ça ne déforme plus rien, Turn 10)
        video_reel = clip_base.resized(zoom_factor)
        
        active_effects = []
        if i % 2 == 0:
            active_effects.append(vfx.MirrorX())
            
        # Ajout furtif de la couleur (Variation très légère pour brouiller l'IA d'Insta, Turn 11)
        try:
            active_effects.append(vfx.Colorx(random.uniform(0.99, 1.01)))
        except:
            pass 

        if active_effects:
            video_reel = video_reel.with_effects(active_effects)
        
        # 2. Recadrage à la dimension exacte de la vidéo d'origine (Fini le zoom flou, Turn 10 !)
        video_reel = video_reel.cropped(
            x_center=video_reel.w/2, 
            y_center=video_reel.h/2, 
            width=clip_base.w, 
            height=clip_base.h
        )
        
        # 3. Coupe temporelle aléatoire
        cut_time = random.uniform(0.05, 0.25)
        video_reel = video_reel.subclipped(0, video_reel.duration - cut_time)

        # Rendu du texte avec la vraie dimension de la vidéo
        # C'est ici que le nouveau texte Master Force GÉANT est créé
        txt_img = create_unique_text_sticker(txt, (clip_base.w, clip_base.h), base_y)
        txt_clip = ImageClip(txt_img).with_duration(video_reel.duration)
        # On superpose le nouveau texte GÉANT par-dessus la vidéo source
        final = CompositeVideoClip([video_reel, txt_clip])
        
        output_name = f"{modele_nom}_Reel_{i+1}_variant.mp4"
        clean_params = ["-map_metadata", "-1", "-metadata", f"comment=Generation_ID_{random.randint(10000,99999)}"]
        
        final.write_videofile(os.path.join(dossier_sortie, output_name), 
                              codec="libx264", audio_codec="aac", fps=24, logger=None,
                              ffmpeg_params=clean_params)
        
        reels_reussis += 1
        
    clip_base.close()
