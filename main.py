import os, io, vtracer, asyncio
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from rembg import remove, new_session
from PIL import Image

app = FastAPI()

# 4 MB'lık hamsi model. Render için EN GARANTİSİ budur!
session = new_session("u2netp")

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

@app.get("/")
async def home():
    return {"mesaj": "Render Yaylası Aktif! /docs adresine gel uşağum!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        content = await file.read()
        input_img = Image.open(io.BytesIO(content)).convert("RGBA")
        
        # Render'ın 512MB RAM'i için fotoğrafı 800px'e çekiyoruz. 
        # Vektör olacağı için kaliteden korkma uşağum!
        input_img.thumbnail((800, 800)) 
        
        # Arka planı temizle
        no_bg = remove(input_img, session=session)
        
        temp_png, temp_svg, temp_eps = "s.png", "s.svg", "s.eps"
        no_bg.save(temp_png)

        # Vektörleştirme
        vtracer.convert_image_to_svg(temp_png, temp_svg, mode='spline')

        # Inkscape ile EPS çevirisi
        process = await asyncio.create_subprocess_shell(
            f"inkscape {temp_svg} --export-type=eps --export-filename={temp_eps}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        background_tasks.add_task(cleanup, [temp_png, temp_svg, temp_eps])
        
        return FileResponse(temp_eps, filename="vektor.eps")

    except Exception as e:
        return JSONResponse(content={"hata": str(e)}, status_code=500)