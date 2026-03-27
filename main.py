import os, subprocess, asyncio, uuid
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

@app.get("/")
async def home():
    return {"mesaj": "Render RAM Dostu Yayla Aktif!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Dosya adını benzersiz yapalım
    job_id = str(uuid.uuid4())
    in_file = f"in_{job_id}.jpg"
    out_svg = f"out_{job_id}.svg"
    out_eps = f"out_{job_id}.eps"
    
    try:
        # 1. Fotoğrafı RAM'e yüklemeden doğrudan diske yaz!
        # En güvenli yol budur, RAM şişmez.
        with open(in_file, "wb") as f:
            f.write(await file.read())

        # 2. VTracer'ı binary olarak çalıştır (RAM harcamaz)
        # Not: requirements.txt içinde vtracer-cli yüklü olmalı
        subprocess.run([
            "vtracer", 
            "--input", in_file, 
            "--output", out_svg, 
            "--mode", "spline",
            "--clustering_threshold", "15"
        ], check=True)

        # 3. Inkscape ile EPS yap
        subprocess.run([
            "inkscape", out_svg, 
            "--export-type=eps", 
            "--export-filename=out_eps"
        ])

        background_tasks.add_task(cleanup, [in_file, out_svg, out_eps])

        if os.path.exists(out_eps):
            return FileResponse(out_eps, filename="vektor.eps")
        return FileResponse(out_svg, filename="vektor.svg")

    except Exception as e:
        cleanup([in_file, out_svg, out_eps])
        return JSONResponse(content={"hata": str(e)}, status_code=500)