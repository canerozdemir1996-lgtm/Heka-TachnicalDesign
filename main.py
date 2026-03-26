import os, io, vtracer
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from rembg import remove, new_session
from PIL import Image

app = FastAPI()

# RAM dostu model oturumu - Yeni versiyonlarda ismi budur uşağum!
# Eğer 'is-net-general-use' bulamazsa standart olana döner.
try:
    session = new_session("is-net-general-use")
except:
    session = new_session("u2net")

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

@app.get("/")
async def home():
    return {"mesaj": "Dernekpazarı Mermi Gibi Vektör Servisi Aktif! /docs adresine gel uşağum!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        # 1. Fotoğrafı oku
        content = await file.read()
        input_img = Image.open(io.BytesIO(content)).convert("RGBA")
        
        # 2. Arka planı temizle
        no_bg = remove(input_img, session=session)
        
        base_name = "sonuc"
        temp_png = f"{base_name}_temp.png"
        temp_svg = f"{base_name}.svg"
        temp_eps = f"{base_name}.eps"
        
        no_bg.save(temp_png)

        # 3. Vektörleştirme (SVG)
        # v_func kontrolü (Laz inadı ile garantili buluş)
        v_func = getattr(vtracer, 'convert_to_svg', getattr(vtracer, 'convert_image_to_svg', None))
        if v_func:
            v_func(temp_png, temp_svg, mode='spline', clustering_threshold=15)
        else:
            raise Exception("VTracer motoru çalüşmayi uşağum!")

        # 4. Inkscape ile EPS'ye paketle
        os.system(f"inkscape {temp_svg} --export-type=eps --export-filename={temp_eps}")

        if not os.path.exists(temp_eps):
            # EPS olmazsa bari SVG gönderelum, boş dönmeyelum
            if os.path.exists(temp_svg):
                return FileResponse(temp_svg, media_type='image/svg+xml', filename=f"{base_name}.svg")
            return JSONResponse(content={"hata": "Vektör oluşturulamadi uşağum!"}, status_code=500)

        # Temizlik görevini arkaya atalum
        background_tasks.add_task(cleanup, [temp_png, temp_svg, temp_eps])

        return FileResponse(
            path=temp_eps, 
            filename=f"{file.filename.split('.')[0]}_vektor.eps", 
            media_type='application/postscript'
        )

    except Exception as e:
        return JSONResponse(content={"hata": str(e)}, status_code=500)