import os, random, numpy as np, warnings, cv2
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
        if not ret: return 300
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_y = (y + h/2) * (canvas_h / frame.shape[0])
            if face_y < canvas_h * 0.45: return 1450 
            else: return 300 
    except: pass
    return 300 

def create_unique_text_sticker(text, reel_size, base_y):
    canvas_w, canvas_h = reel_size
    img = Image.new('RGBA', reel_size, (0, 0, 0, 0))
    random_y_offset = random.randint(-40, 40)
    final_y = base_y + random_y_offset
    length = len(text)
    font_size = 140 if length < 15 else (95 if length < 50 else 70)
    font_size += random.randint(-3, 3)

    try: font = ImageFont.truetype("arial.ttf", font_size)
    except: font = ImageFont.load_default()

    with Pilmoji(img, source=AppleEmojiSource) as pilmoji:
        lines = []
        max_w = int(canvas_w * 0.8)
        words = text.split()
        line = ""
        for w in words:
            test = line + " " + w if line else w
            if pilmoji.getsize(test, font=font)[0] < max_w: line = test
            else: lines.append(line); line = w
        lines.append(line)
        
        total_h = len(lines) * (font_size + 20)
        start_y = final_y - (total_h // 2)

        for l in lines:
            w_t = pilmoji.getsize(l, font=font)[0]
            pilmoji.text(((canvas_w - w_t) // 2, start_y), l, font=font, 
                         fill="white", stroke_width=5, stroke_fill="black")
            start_y += font_size + 20
    return np.array(img)

# NOUVEAU PARAMÈTRE : stop_event
def lancer_production_serie(chemin_video, chemin_captions, dossier_sortie, n_to_make, modele_nom, progress_bar=None, status_text=None, stop_event=None):
    
    with open(chemin_captions, "r", encoding="utf-8") as f:
        all_captions = [c.strip() for c in f.read().split('\n\n') if c.strip()]
    
    if not all_captions:
        all_captions = ["Texte par défaut"]

    base_y = get_base_y_placement(chemin_video, 1920)
    clip_base = VideoFileClip(chemin_video)
    
    reels_reussis = 0

    for i in range(n_to_make):
        
        # 🛑 VÉRIFICATION DU BOUTON STOP AVANT CHAQUE NOUVEAU REEL
        if stop_event and stop_event.is_set():
            print("Arrêt de la production demandé par l'utilisateur.")
            break

        txt = all_captions[i % len(all_captions)]
        
        if status_text:
            status_text.text(f"⚡ [{i+1}/{n_to_make}] Production de la variante : {txt[:20]}...")

        # Pack Anti-Ban
        zoom_factor = random.uniform(1.01, 1.04)
        new_height = int(1920 * zoom_factor)
        video_reel = clip_base.resized(height=new_height)
        
        active_effects = []
        if i % 2 == 0:
            active_effects.append(vfx.MirrorX())
            
        if active_effects:
            video_reel = video_reel.with_effects(active_effects)
        
        video_reel = video_reel.cropped(x_center=video_reel.w/2, y_center=video_reel.h/2, width=1080, height=1920)
        cut_time = random.uniform(0.05, 0.25)
        video_reel = video_reel.subclipped(0, video_reel.duration - cut_time)

        # Rendu
        txt_img = create_unique_text_sticker(txt, (1080, 1920), base_y)
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
    return reels_reussis