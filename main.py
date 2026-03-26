import os, io, vtracer, cv2
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from rembg import remove
from PIL import Image

app = FastAPI()

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

@app.get("/")
async def home():
    return {"mesaj": "Dernekpazarı Vektör Servisi Aktif! /docs adresine git uşağum!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        # 1. Fotoğrafı oku ve arka planı uçur
        content = await file.read()
        input_img = Image.open(io.BytesIO(content)).convert("RGBA")
        no_bg = remove(input_img)
        
        base_name = "sonuc"
        temp_png = f"{base_name}_temp.png"
        temp_svg = f"{base_name}.svg"
        temp_eps = f"{base_name}.eps"
        
        no_bg.save(temp_png)

        # 2. Vektörleştirme (SVG)
        v_func = getattr(vtracer, 'convert_to_svg', getattr(vtracer, 'convert_image_to_svg', None))
        v_func(temp_png, temp_svg, mode='spline', clustering_threshold=15)

        # 3. Inkscape ile EPS'ye paketle
        os.system(f"inkscape {temp_svg} --export-type=eps --export-filename={temp_eps}")

        if not os.path.exists(temp_eps):
            return JSONResponse(content={"hata": "EPS dosyasi oluşturulamadi uşağum!"}, status_code=500)

        # İş bitince temizlik yapalum
        background_tasks.add_task(cleanup, [temp_png, temp_svg, temp_eps])

        return FileResponse(path=temp_eps, filename=f"{file.filename.split('.')[0]}.eps", media_type='application/postscript')

    except Exception as e:
        return JSONResponse(content={"hata": str(e)}, status_code=500)