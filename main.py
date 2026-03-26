import os, io, vtracer, asyncio, subprocess
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from rembg import remove, new_session
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

# En hafif model
session = new_session("u2netp")
# Havuz kapasitesini artırdık
executor = ThreadPoolExecutor(max_workers=4)

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

def remove_background(input_img):
    # Bu ağır iş arka planda çalışacak
    return remove(input_img, session=session)

def vectorize_image(temp_png, temp_svg):
    # VTracer'ı ayrı çalıştırıyoruz
    vtracer.convert_image_to_svg(temp_png, temp_svg, mode='spline', clustering_threshold=15)

@app.get("/")
async def home():
    return {"mesaj": "Dernekpazarı Turbo Vektör Servisi Aktif! /docs adresine gel!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        # 1. Dosyayı oku
        content = await file.read()
        input_img = Image.open(io.BytesIO(content)).convert("RGBA")
        
        loop = asyncio.get_event_loop()
        
        # 2. Arka plan temizleme (Ayrı kanalda)
        no_bg = await loop.run_in_executor(executor, remove_background, input_img)
        
        base_name = "sonuc"
        temp_png = f"{base_name}_temp.png"
        temp_svg = f"{base_name}.svg"
        temp_eps = f"{base_name}.eps"
        
        # PNG olarak kaydet
        no_bg.save(temp_png)

        # 3. Vektörleştirme (Ayrı kanalda)
        await loop.run_in_executor(executor, vectorize_image, temp_png, temp_svg)

        # 4. Inkscape ile EPS çevirisi (Bunu da subprocess ile çalıştırıp bekletmeyelim)
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
            return JSONResponse(content={"hata": "Vektör oluşturulamadı!"}, status_code=500)

        # Temizlik
        background_tasks.add_task(cleanup, [temp_png, temp_svg, temp_eps])

        return FileResponse(
            path=temp_eps, 
            filename=f"{file.filename.split('.')[0]}_vektor.eps", 
            media_type='application/postscript'
        )

    except Exception as e:
        return JSONResponse(content={"hata": str(e)}, status_code=500)