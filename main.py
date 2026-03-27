import os, io, vtracer, asyncio
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
    try:
        # 1. Dosyayı en az RAM harcayacak şekilde oku
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # 2. Daha fotoğrafı açmadan önce boyutunu iyice ufalat (Sunucu bayılmasın!)
        # Bu işlem RAM'i korur uşağum!
        img.thumbnail((800, 800))
        
        temp_png = "s.png"
        temp_svg = "s.svg"
        temp_eps = "s.eps"
        
        # PNG olarak kaydet (Arka plan silmeyi şimdilik geçtik, test ediyoruz!)
        img.save(temp_png)

        # 3. Vektörleştirme (VTracer fisek gibidir, yormaz)
        vtracer.convert_image_to_svg(temp_png, temp_svg, mode='spline')

        # 4. Inkscape ile EPS çevirisi
        process = await asyncio.create_subprocess_shell(
            f"inkscape {temp_svg} --export-type=eps --export-filename={temp_eps}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        background_tasks.add_task(cleanup, [temp_png, temp_svg, temp_eps])
        
        if os.path.exists(temp_eps):
            return FileResponse(temp_eps, filename="vektor.eps")
        else:
            return FileResponse(temp_svg, filename="vektor.svg")

    except Exception as e:
        return JSONResponse(content={"hata": str(e)}, status_code=500)