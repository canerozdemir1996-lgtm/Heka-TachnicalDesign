import os, io, asyncio, uuid
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
import cv2
import numpy as np
import vtracer

app = FastAPI()

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

@app.get("/")
async def home():
    return {"mesaj": "Erhan'un Hafifletilmiş Blueprint Motoru Aktif!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    temp_edge_png = f"e_{job_id}.png"
    temp_svg = f"s_{job_id}.svg"
    
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert("RGBA")
        
        # Artık yapay zeka yok, boyutu 1200px yapabiliruk!
        img.thumbnail((1200, 1200)) 
        
        # Şeffaf resim gelirse, arkasını bembeyaz kağıt yap
        white_bg = Image.new("RGBA", img.size, "WHITE")
        white_bg.paste(img, (0, 0), img)
        rgb_img = white_bg.convert("RGB")

        # OpenCV'ye geçiş
        img_cv2 = np.array(rgb_img)
        img_cv2 = img_cv2[:, :, ::-1].copy() 
        
        # Teknik Çizgi (Blueprint) İskeletini Bul
        gray = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        kernel = np.ones((2,2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Siyah üstüne beyaz çizgiyi, beyaz üstüne siyah yap
        edges_inv = cv2.bitwise_not(edges)
        cv2.imwrite(temp_edge_png, edges_inv)
        
        # VTracer ile Vektör
        try:
            vtracer.convert_image_to_svg_py(temp_edge_png, temp_svg, colormode="bw", mode="spline")
        except AttributeError:
            try:
                vtracer.convert_image_to_svg(temp_edge_png, temp_svg, colormode="bw", mode="spline")
            except Exception:
                pass
                
        if not os.path.exists(temp_svg):
            os.system(f"vtracer --input {temp_edge_png} --output {temp_svg} --colormode bw --mode spline")

        if not os.path.exists(temp_svg):
            return JSONResponse(content={"hata": "Vektör motoru patladi!"}, status_code=500)

        background_tasks.add_task(cleanup, [temp_edge_png, temp_svg])

        return FileResponse(
            path=temp_svg, 
            filename=f"erhan_blueprint_{job_id}.svg", 
            media_type='image/svg+xml'
        )

    except Exception as e:
        cleanup([temp_edge_png, temp_svg])
        return JSONResponse(content={"hata": f"Mutfak yandi: {str(e)}"}, status_code=500)