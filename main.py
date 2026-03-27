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
    return {"mesaj": "Dernekpazarı Vektör Motoru (Final Sürüm) Rölantide, Bekliyi uşağum!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    temp_png = f"p_{job_id}.png"
    temp_edge_png = f"e_{job_id}.png"
    temp_svg = f"s_{job_id}.svg"
    
    try:
        # 1. Dosyayı oku ve Render RAM'i patlamasun diye hemen küçült (thumbnail)
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert("RGBA")
        
        # 1200px sınırı hem kalite hem RAM dostudur uşağum!DSC dosyaları için bu hayati!
        img.thumbnail((1200, 1200))
        img.save(temp_png)
        
        # 2. LAZ İNADI BURADA DEVREYE GİRİYOR: TEKNIK ÇIZGI ISKELETINI BULALUM!
        # OpenCV (cv2) uşağını mutfağa soktuk.
        
        # Fotoğrafı tekrar OpenCV formatında okuyalim (Pillow'dan cv2'ye geçiş)
        img_cv2 = cv2.imread(temp_png, cv2.IMREAD_GRAYSCALE)
        
        # Canny Kenar Bulma (Edge Detection) ile sadece iskeleti çikartiyoruz.
        # Bu değerler (100, 200) çoğu fotoğraf için mermi gibidür.
        edges = cv2.Canny(img_cv2, 100, 200)
        
        # Siyah arka plan üzerine beyaz çizgiler çıktı, bunu tersine çevirelim:
        # Beyaz arka plan üzerine siyah çizgiler yapalım ki VTracer sevsun!
        edges_inv = cv2.bitwise_not(edges)
        
        # İskelet halini diske yazalim
        cv2.imwrite(temp_edge_png, edges_inv)
        
        # 3. VEKTÖRLEŞTİRME (VTracer'ı iskelet üzerinde çalıştur)
        # Kütüphanenin en son nesil fonksiyonu: convert_image_to_svg_py
        try:
            # colormode="color" dedik ama iskelet olduğu için zaten siyah-beyaz çizgi basacak. mode="spline" pürüzsüz çizgiler yapur.
            vtracer.convert_image_to_svg_py(temp_edge_png, temp_svg, colormode="color", mode="spline", clustering_threshold=15)
        except AttributeError:
            # Belki eski sürüm kurulmuştur diye Laz sağlama alması
            vtracer.convert_image_to_svg(temp_edge_png, temp_svg, colormode="color", mode="spline")

        # Dosya çıkmış mı diye bakayruk
        if not os.path.exists(temp_svg):
            return JSONResponse(content={"hata": "VTracer motoru tekledi, SVG basamadi uşağum!"}, status_code=500)

        # Temizlik
        # p_{job_id}.png ve e_{job_id}.png dosyalarını arkada silsun
        background_tasks.add_task(cleanup, [temp_png, temp_edge_png, temp_svg])

        # Saf, temiz teknik çizim iskeletini (SVG) fırlat gitsin!
        return FileResponse(
            path=temp_svg, 
            filename=f"{file.filename.split('.')[0]}_technical_blueprint.svg", 
            media_type='image/svg+xml'
        )

    except Exception as e:
        cleanup([temp_png, temp_edge_png, temp_svg])
        return JSONResponse(content={"hata": f"Mutfak yandi uşağum: {str(e)}"}, status_code=500)