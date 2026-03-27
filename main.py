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
    return {"mesaj": "Dernekpazari Jilet EPS Motoru Aktif!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    temp_edge_png = f"e_{job_id}.png"
    temp_svg = f"s_{job_id}.svg"
    temp_eps = f"eps_{job_id}.eps"  # EPS Uşaği Buraya Gelecek
    
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert("RGBA")
        
        # Yapay zeka yok, boyutu rahatça 1200px yapabiluruk
        img.thumbnail((1200, 1200)) 
        
        # Arka plani şeffafsa bembeyaz kağida koy
        white_bg = Image.new("RGBA", img.size, "WHITE")
        white_bg.paste(img, (0, 0), img)
        rgb_img = white_bg.convert("RGB")

        # OpenCV mutfaği
        img_cv2 = np.array(rgb_img)
        img_cv2 = img_cv2[:, :, ::-1].copy() 
        
        # Jilet gibi iskelet (Line Art)
        gray = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        # Çizgiler kalınlaşsun (silik çikmasun)
        kernel = np.ones((2,2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Vtracer islesun diye siyah üstüne beyaz değil, beyaz üstüne siyah çizgi yap
        edges_inv = cv2.bitwise_not(edges)
        cv2.imwrite(temp_edge_png, edges_inv)
        
        # 1. Aşama: VTracer ile SVG bas
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
            return JSONResponse(content={"hata": "Motor SVG basamadi uşağum!"}, status_code=500)

        # 2. Aşama: LAZ İNADI (SVG'yi EPS yapayruk)
        os.system(f"inkscape {temp_svg} --export-filename={temp_eps}")
        
        if not os.path.exists(temp_eps):
            return JSONResponse(content={"hata": "Inkscape tekledi, EPS basulamadi!"}, status_code=500)

        # Temizlik
        background_tasks.add_task(cleanup, [temp_edge_png, temp_svg, temp_eps])

        # Direk EPS dosyasini firlat gitsun!
        return FileResponse(
            path=temp_eps, 
            filename=f"teknik_cizim_{job_id}.eps", 
            media_type='application/postscript'
        )

    except Exception as e:
        cleanup([temp_edge_png, temp_svg, temp_eps])
        return JSONResponse(content={"hata": f"Mutfak yandi abi: {str(e)}"}, status_code=500)