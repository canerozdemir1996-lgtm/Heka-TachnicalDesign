import os, io, asyncio, uuid, vtracer
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
    return {"mesaj": "Render Yaylası Aktif! /docs adresine gel!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    temp_png = f"p_{job_id}.png"
    temp_svg = f"s_{job_id}.svg"
    temp_eps = f"e_{job_id}.eps"
    
    try:
        # 1. Dosyayı oku ve hemen küçült (RAM'i korumak için)
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert("RGBA")
        
        # 800px sınırı Render için hayat kurtarır
        img.thumbnail((800, 800))
        img.save(temp_png)
        
        # 2. Vektörleştirme (Kütüphane üzerinden direkt)
        vtracer.convert_image_to_svg(temp_png, temp_svg, mode='spline', clustering_threshold=15)

        # 3. Inkscape ile EPS'ye çevir
        process = await asyncio.create_subprocess_shell(
            f"inkscape {temp_svg} --export-type=eps --export-filename={temp_eps}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        background_tasks.add_task(cleanup, [temp_png, temp_svg, temp_eps])

        if os.path.exists(temp_eps):
            return FileResponse(temp_eps, filename="vektor.eps")
        elif os.path.exists(temp_svg):
            return FileResponse(temp_svg, filename="vektor.svg")
        
        return JSONResponse(content={"hata": "Dosya oluşturulamadı uşağum!"}, status_code=500)

    except Exception as e:
        cleanup([temp_png, temp_svg, temp_eps])
        return JSONResponse(content={"hata": str(e)}, status_code=500)