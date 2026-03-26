import os, io, vtracer, asyncio
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from rembg import remove, new_session
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

# Hamsi model
session = new_session("u2netp")
executor = ThreadPoolExecutor(max_workers=2)

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

def process_image(img_bytes):
    # 1. Fotoğrafı RAM'e al
    input_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    
    # LAZ İNADI BURADA DEVREYE GİRİYOR!
    # O devasa "DSC" fotoğrafını sunucu bayılmasın diye makul bir boyuta çekiyoruz!
    input_img.thumbnail((1024, 1024)) 
    
    # 2. Arka planı sil (Şimdi fisek gibi işleyecek)
    return remove(input_img, session=session)

def vectorize_image(temp_png, temp_svg):
    vtracer.convert_image_to_svg(temp_png, temp_svg, mode='spline', clustering_threshold=15)

@app.get("/")
async def home():
    return {"mesaj": "Dernekpazarı Anti-OOM Vektör Servisi Aktif! /docs adresine gel!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        content = await file.read()
        loop = asyncio.get_event_loop()
        
        # Bütün ağır işlemi (küçültme + arka plan silme) ayrı bir odaya yolladık
        no_bg = await loop.run_in_executor(executor, process_image, content)
        
        base_name = "sonuc"
        temp_png = f"{base_name}_temp.png"
        temp_svg = f"{base_name}.svg"
        temp_eps = f"{base_name}.eps"
        
        no_bg.save(temp_png)

        # Vektörleştirme
        await loop.run_in_executor(executor, vectorize_image, temp_png, temp_svg)

        # Inkscape ile EPS'ye çevirme
        process = await asyncio.create_subprocess_shell(
            f"inkscape {temp_svg} --export-type=eps --export-filename={temp_eps}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        if not os.path.exists(temp_eps):
            if os.path.exists(temp_svg):
                background_tasks.add_task(cleanup, [temp_png, temp_svg])
                return FileResponse(temp_svg, media_type='image/svg+xml', filename=f"{base_name}.svg")
            return JSONResponse(content={"hata": "Vektör oluşturulamadı uşağum!"}, status_code=500)

        # Temizlik
        background_tasks.add_task(cleanup, [temp_png, temp_svg, temp_eps])

        return FileResponse(
            path=temp_eps, 
            filename=f"{file.filename.split('.')[0]}_vektor.eps", 
            media_type='application/postscript'
        )

    except Exception as e:
        return JSONResponse(content={"hata": str(e)}, status_code=500)