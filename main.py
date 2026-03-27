import os, io, asyncio, uuid
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
import cv2
import numpy as np
import vtracer
from rembg import remove, new_session

app = FastAPI()

# Yapay zeka modelini rölantide tutayruk (Hamsi model)
session = new_session("u2netp")

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

@app.get("/")
async def home():
    return {"mesaj": "Dernekpazarı Dekupeli Çizim Motoru Aktif!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    temp_edge_png = f"e_{job_id}.png"
    temp_svg = f"s_{job_id}.svg"
    
    try:
        # 1. DOSYAYI OKU VE UFALT (Render RAM'i için 800px hayati önemdedur!)
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert("RGBA")
        img.thumbnail((800, 800))
        
        # 2. YAPAY ZEKA İLE DEKUPE ET (Arka plani sil)
        no_bg_img = remove(img, session=session)
        
        # 3. OPENCV İÇİN HAZIRLA
        # Arka plani şeffaf değil, tam BEYAZ yapayruk ki çizgiler net çiksun
        white_bg = Image.new("RGBA", no_bg_img.size, "WHITE")
        white_bg.paste(no_bg_img, (0, 0), no_bg_img)
        rgb_img = white_bg.convert("RGB")
        
        # Pillow'dan OpenCV formatina (Numpy) geçiş
        img_cv2 = np.array(rgb_img)
        img_cv2 = img_cv2[:, :, ::-1].copy() # RGB'den BGR'ye
        
        # 4. TEKNİK ÇİZGİLERİ (İSKELETİ) ÇIKART
        gray = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        # Çizgileri biraz kalınlaştur (Silik çikmasun)
        kernel = np.ones((2,2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Siyah arka planı beyaz, beyaz çizgileri siyah yap
        edges_inv = cv2.bitwise_not(edges)
        cv2.imwrite(temp_edge_png, edges_inv)
        
        # 5. VTRACER İLE VEKTÖR YAP (Siyah/Beyaz Modunda)
        try:
            vtracer.convert_image_to_svg_py(temp_edge_png, temp_svg, colormode="bw", mode="spline")
        except AttributeError:
            try:
                vtracer.convert_image_to_svg(temp_edge_png, temp_svg, colormode="bw", mode="spline")
            except Exception:
                pass
                
        # Laz inadı: Kütüphane patlarsa komut satırından zorla
        if not os.path.exists(temp_svg):
            os.system(f"vtracer --input {temp_edge_png} --output {temp_svg} --colormode bw --mode spline")

        if not os.path.exists(temp_svg):
            return JSONResponse(content={"hata": "Motor kilitlendi, SVG basulamadi uşağum!"}, status_code=500)

        background_tasks.add_task(cleanup, [temp_edge_png, temp_svg])

        return FileResponse(
            path=temp_svg, 
            filename=f"dekupe_cizim_{job_id}.svg", 
            media_type='image/svg+xml'
        )

    except Exception as e:
        cleanup([temp_edge_png, temp_svg])
        return JSONResponse(content={"hata": f"Mutfak yandi uşağum: {str(e)}"}, status_code=500)