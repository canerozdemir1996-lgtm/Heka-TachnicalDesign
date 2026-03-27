import os, io, asyncio, uuid
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
import cv2
import numpy as np
import vtracer

app = FastAPI()

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

@app.get("/")
async def home():
    return {"mesaj": "Dernekpazarı Teknik Çizim Motoru Aktif!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    temp_png = f"p_{job_id}.png"
    temp_edge_png = f"e_{job_id}.png"
    temp_svg = f"s_{job_id}.svg"
    
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert("RGBA")
        img.thumbnail((1200, 1200))
        img.save(temp_png)
        
        # --- OPENCV İLE TEKNİK İSKELET ÇIKARMA ---
        img_cv2 = cv2.imread(temp_png, cv2.IMREAD_GRAYSCALE)
        
        # Fotoğraftaki kumlanmaları (gürültüyü) sil ki çizim pürüzsüz olsun
        blurred = cv2.GaussianBlur(img_cv2, (5, 5), 0)
        
        # Kenarları bul (Edge Detection)
        edges = cv2.Canny(blurred, 50, 150)
        
        # Çizgileri azıcık kalınlaştıralım ki vektör motoru tam yakalasın (soluk çıkmasın)
        kernel = np.ones((2,2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Siyah arka planı beyaz, beyaz çizgileri siyah yap (Tam blueprint tarzı)
        edges_inv = cv2.bitwise_not(edges)
        cv2.imwrite(temp_edge_png, edges_inv)
        
        # --- VTRACER İLE SİYAH/BEYAZ SVG YAPMA ---
        # Hata veren 'clustering_threshold' silindi! 
        # colormode="bw" (black/white) yapıldı ki tam teknik çizim olsun.
        try:
            vtracer.convert_image_to_svg_py(temp_edge_png, temp_svg, colormode="bw", mode="spline")
        except AttributeError:
            try:
                vtracer.convert_image_to_svg(temp_edge_png, temp_svg, colormode="bw", mode="spline")
            except Exception:
                pass
                
        # Eğer kütüphane yine naz yaparsa, en garantili yol komut satırı:
        if not os.path.exists(temp_svg):
            os.system(f"vtracer --input {temp_edge_png} --output {temp_svg} --colormode bw --mode spline")

        if not os.path.exists(temp_svg):
            return JSONResponse(content={"hata": "Motor kilitlendi, SVG basulamadi!"}, status_code=500)

        background_tasks.add_task(cleanup, [temp_png, temp_edge_png, temp_svg])

        return FileResponse(
            path=temp_svg, 
            filename=f"teknik_cizim_{job_id}.svg", 
            media_type='image/svg+xml'
        )

    except Exception as e:
        cleanup([temp_png, temp_edge_png, temp_svg])
        return JSONResponse(content={"hata": f"Mutfak yandi uşağum: {str(e)}"}, status_code=500)