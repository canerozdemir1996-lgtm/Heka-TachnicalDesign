import os, io, vtracer
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from rembg import remove, new_session
from PIL import Image

app = FastAPI()

# İşte Karadeniz zekası! Sadece 4 MB'lık hamsi model. 
# Sunucunun RAM'ini gram yormaz, 503 hatası falan verdirmez!
session = new_session("u2netp")

def cleanup(files: list):
    for f in files:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

@app.get("/")
async def home():
    return {"mesaj": "Dernekpazarı Mermi Gibi Vektör Servisi Aktif! Hadi /docs adresine gel uşağum!"}

@app.post("/vektorlestir")
async def vektorlestir(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        # 1. Fotoğrafı oku
        content = await file.read()
        input_img = Image.open(io.BytesIO(content)).convert("RGBA")
        
        # 2. Arka planı en hafif modelle temizle (Sunucu bayılmasun diye)
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
            raise Exception("VTracer motoru darmadağın oldi, çalüşmayi uşağum!")

        # 4. Inkscape ile EPS'ye paketle
        os.system(f"inkscape {temp_svg} --export-type=eps --export-filename={temp_eps}")

        if not os.path.exists(temp_eps):
            # EPS olmazsa bari SVG gönderelum, yari yolda kalmayalum
            if os.path.exists(temp_svg):
                background_tasks.add_task(cleanup, [temp_png, temp_svg])
                return FileResponse(temp_svg, media_type='image/svg+xml', filename=f"{base_name}.svg")
            return JSONResponse(content={"hata": "Vektör oluşturulamadi uşağum, matbaa yandi!"}, status_code=500)

        # Temizlik görevini arkaya atalum (Çöpleri dereye dökiyi)
        background_tasks.add_task(cleanup, [temp_png, temp_svg, temp_eps])

        return FileResponse(
            path=temp_eps, 
            filename=f"{file.filename.split('.')[0]}_vektor.eps", 
            media_type='application/postscript'
        )

    except Exception as e:
        return JSONResponse(content={"hata": str(e)}, status_code=500)