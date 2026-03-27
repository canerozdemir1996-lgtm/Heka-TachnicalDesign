import os, io, uuid, vtracer
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image

app = FastAPI()

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

@app.get("/")
async def home():
    return {"mesaj": "Dernekpazarı Terminatör Sürümü Aktif! /docs adresine gel!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    temp_png = f"p_{job_id}.png"
    temp_svg = f"s_{job_id}.svg"
    
    try:
        # Fotoğrafı al ve ufalat (Render RAM'i patlamasun)
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert("RGBA")
        img.thumbnail((800, 800))
        img.save(temp_png)
        
        # İŞTE ZURNANIN ZIRT DEDİĞİ YER!
        # Yeni nesil vtracer fonksiyonu budur: convert_image_to_svg_py
        try:
            vtracer.convert_image_to_svg_py(temp_png, temp_svg, colormode="color", mode="spline")
        except AttributeError:
            # Ula belki eski sürüm kurulmuştur diye Laz sağlama alması
            vtracer.convert_image_to_svg(temp_png, temp_svg, colormode="color", mode="spline")

        # Dosya çıkmış mı diye bakayruk
        if not os.path.exists(temp_svg):
            return JSONResponse(content={"hata": "VTracer motoru tekledi, SVG basamadi!"}, status_code=500)

        # Temizlik
        background_tasks.add_task(cleanup, [temp_png, temp_svg])

        # Saf, temiz SVG dosyasını yolla gitsin!
        return FileResponse(
            path=temp_svg, 
            filename=f"vektor_{job_id}.svg", 
            media_type='image/svg+xml'
        )

    except Exception as e:
        cleanup([temp_png, temp_svg])
        return JSONResponse(content={"hata": f"Mutfak yandi uşağum: {str(e)}"}, status_code=500)