import os, io, asyncio, uuid
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
import vtracer

app = FastAPI()

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

@app.get("/")
async def home():
    return {"mesaj": "Render Yaylası Mermi Gibi Aktif! /docs adresine gel!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    temp_png = f"p_{job_id}.png"
    temp_svg = f"s_{job_id}.svg"
    temp_eps = f"e_{job_id}.eps"
    
    try:
        # 1. Dosyayı oku ve RAM dostu olması için hemen ufalt
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert("RGBA")
        
        # 800px sınırı Render için hayati önem taşır uşağum!
        img.thumbnail((800, 800))
        img.save(temp_png)
        
        # 2. VTracer kontrolü - Kütüphane hangi ismi kullanırsa kullansın bulacağuz!
        v_func = getattr(vtracer, 'convert_image_to_svg', 
                 getattr(vtracer, 'convert_to_svg', None))
        
        if v_func:
            # VTracer'ı çalıştur
            v_func(temp_png, temp_svg, mode='spline', clustering_threshold=15)
        else:
            # Eğer kütüphane patlarsa komut satırından deneyeceğuz (Laz inadı!)
            os.system(f"vtracer --input {temp_png} --output {temp_svg} --mode spline")

        # 3. Inkscape ile EPS'ye çevir
        # Render'ı kitlememek için subprocess kullanıyoruz
        process = await asyncio.create_subprocess_shell(
            f"inkscape {temp_svg} --export-type=eps --export-filename={temp_eps}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        background_tasks.add_task(cleanup, [temp_png, temp_svg, temp_eps])

        if os.path.exists(temp_eps):
            return FileResponse(temp_eps, filename=f"{file.filename.split('.')[0]}_vektor.eps", media_type='application/postscript')
        elif os.path.exists(temp_svg):
            return FileResponse(temp_svg, filename=f"{file.filename.split('.')[0]}_vektor.svg", media_type='image/svg+xml')
        
        return JSONResponse(content={"hata": "Dosya oluşturulamadı uşağum!"}, status_code=500)

    except Exception as e:
        cleanup([temp_png, temp_svg, temp_eps])
        return JSONResponse(content={"hata": str(e)}, status_code=500)