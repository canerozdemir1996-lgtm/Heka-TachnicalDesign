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
    return {"mesaj": "Vektör Motoru Rölantide, Bekliyi uşağum!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    temp_png = f"p_{job_id}.png"
    temp_svg = f"s_{job_id}.svg"
    
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert("RGBA")
        img.thumbnail((800, 800))
        img.save(temp_png)
        
        v_func = getattr(vtracer, 'convert_image_to_svg', getattr(vtracer, 'convert_to_svg', None))
        
        if v_func:
            v_func(temp_png, temp_svg, mode='spline', clustering_threshold=15)
        else:
            os.system(f"vtracer --input {temp_png} --output {temp_svg} --mode spline")

        if not os.path.exists(temp_svg):
            return JSONResponse(content={"hata": "Vektör çizilemedi uşağum!"}, status_code=500)

        background_tasks.add_task(cleanup, [temp_png, temp_svg])

        return FileResponse(
            path=temp_svg, 
            filename=f"{file.filename.split('.')[0]}_vektor.svg", 
            media_type='image/svg+xml'
        )

    except Exception as e:
        cleanup([temp_png, temp_svg])
        return JSONResponse(content={"hata": str(e)}, status_code=500)