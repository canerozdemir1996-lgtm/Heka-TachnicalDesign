import os, io, vtracer, asyncio
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from rembg import remove, new_session
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

# En hafif modelimiz duruyor
session = new_session("u2netp")

# Sunucu boğulmasın diye işlemi bu havuzda (ayrı bir odada) yapacağız
executor = ThreadPoolExecutor(max_workers=2)

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

# Ağır işlemi (rembg) ayrı bir fonksiyona aldık ki sunucunun ana damarı tıkanmasın
def process_image(input_img):
    return remove(input_img, session=session)

@app.get("/")
async def home():
    return {"mesaj": "Dernekpazarı Asenkron Vektör Servisi Aktif! /docs adresine gel!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        content = await file.read()
        input_img = Image.open(io.BytesIO(content)).convert("RGBA")
        
        # DİKKAT: İşlemi "ThreadPoolExecutor" ile arka planda çalıştırıyoruz.
        # Bu sayede Uvicorn sunucusu "Ben kitlendim, 503 veriyorum" demeyecek!
        loop = asyncio.get_event_loop()
        no_bg = await loop.run_in_executor(executor, process_image, input_img)
        
        base_name = "sonuc"
        temp_png = f"{base_name}_temp.png"
        temp_svg = f"{base_name}.svg"
        temp_eps = f"{base_name}.eps"
        
        no_bg.save(temp_png)

        v_func = getattr(vtracer, 'convert_to_svg', getattr(vtracer, 'convert_image_to_svg', None))
        if v_func:
            # vtracer çok hızlıdır, onu asenkrone atmaya gerek yok
            v_func(temp_png, temp_svg, mode='spline', clustering_threshold=15)
        else:
            raise Exception("VTracer motoru çalüşmayi!")

        os.system(f"inkscape {temp_svg} --export-type=eps --export-filename={temp_eps}")

        if not os.path.exists(temp_eps):
            if os.path.exists(temp_svg):
                background_tasks.add_task(cleanup, [temp_png, temp_svg])
                return FileResponse(temp_svg, media_type='image/svg+xml', filename=f"{base_name}.svg")
            return JSONResponse(content={"hata": "Vektör oluşturulamadi!"}, status_code=500)

        background_tasks.add_task(cleanup, [temp_png, temp_svg, temp_eps])

        return FileResponse(
            path=temp_eps, 
            filename=f"{file.filename.split('.')[0]}_vektor.eps", 
            media_type='application/postscript'
        )

    except Exception as e:
        return JSONResponse(content={"hata": str(e)}, status_code=500)