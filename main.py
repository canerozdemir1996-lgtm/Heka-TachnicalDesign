import os, io, asyncio
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from rembg import remove, new_session
from PIL import Image
import vtracer

app = FastAPI()

# 1. MODELİ BURADA (GLOBAL) BİR KERE YÜKLÜYORUZ
# Uygulama açılırken bir kere yorulur, sonra mermi gibi olur!
try:
    session = new_session("u2netp")
except Exception as e:
    print(f"Model yüklenemedi: {e}")
    session = None

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

@app.get("/")
async def home():
    return {"mesaj": "Hugging Face Yaylası Aktif! /docs adresine gel uşağum!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if session is None:
        return JSONResponse(content={"hata": "Model hazır değil uşağum!"}, status_code=500)
    
    try:
        # 2. FOTOĞRAFI OKU VE SIKIŞTIR
        content = await file.read()
        input_img = Image.open(io.BytesIO(content)).convert("RGBA")
        
        # Sunucu bayılmasın diye 1200px sınırı koyduk
        input_img.thumbnail((1200, 1200))
        
        # 3. ARKA PLANI SİL (Global session ile şimşek gibi!)
        no_bg = remove(input_img, session=session)
        
        temp_png = "s.png"
        temp_svg = "s.svg"
        temp_eps = "s.eps"
        
        no_bg.save(temp_png)

        # 4. VEKTÖRLEŞTİRME (VTracer)
        vtracer.convert_image_to_svg(temp_png, temp_svg, mode='spline', clustering_threshold=15)

        # 5. INKSCAPE İLE EPS'YE ÇEVİR
        # Subprocess kullanarak sistemi kitlemiyoruz
        process = await asyncio.create_subprocess_shell(
            f"inkscape {temp_svg} --export-type=eps --export-filename={temp_eps}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        if not os.path.exists(temp_eps):
            # EPS olmazsa bari SVG gönderelim, dükkanı boş kapatmayalım
            if os.path.exists(temp_svg):
                background_tasks.add_task(cleanup, [temp_png, temp_svg])
                return FileResponse(temp_svg, media_type='image/svg+xml', filename="sonuc.svg")
            return JSONResponse(content={"hata": "Vektör duman oldi!"}, status_code=500)

        # 6. TEMİZLİK (Dereye çöp atmayalum)
        background_tasks.add_task(cleanup, [temp_png, temp_svg, temp_eps])

        return FileResponse(
            path=temp_eps, 
            filename=f"{file.filename.split('.')[0]}_vektor.eps", 
            media_type='application/postscript'
        )

    except Exception as e:
        return JSONResponse(content={"hata": str(e)}, status_code=500)