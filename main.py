from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from rembg import remove
from PIL import Image
import vtracer
import io
import os

app = FastAPI()

@app.post("/vektorlestir")
async def vektorlestir(file: UploadFile = File(...)):
    # 1. Fotoğrafı oku
    request_object_content = await file.read()
    input_image = Image.open(io.BytesIO(request_object_content)).convert("RGBA")

    # 2. Dekupe (Arka Planı At)
    # Vercel'de şişmesin diye en hafif modeli kullanıyoruz
    output_image = remove(input_image)
    
    # Geçici dosyalar için RAM kullanıyoruz (Vercel disk sevmez)
    img_byte_arr = io.BytesIO()
    output_image.save(img_byte_arr, format='PNG')
    
    # 3. Vektörleştirme (SVG)
    # VTracer burada devreye girer
    temp_input = "temp_input.png"
    temp_output = "temp_output.svg"
    
    with open(temp_input, "wb") as f:
        f.write(img_byte_arr.getvalue())

    # Karadeniz usulü pürüzsüz çizgiler (Spline Mode)
    # Fonksiyon adını dinamik kontrol ediyoruz (vtracer versiyon fix)
    v_func = getattr(vtracer, 'convert_to_svg', getattr(vtracer, 'convert_image_to_svg', None))
    v_func(temp_input, temp_output, mode='spline', clustering_threshold=15)

    # 4. Çıktıyı hazırlayıp gönder
    with open(temp_output, "rb") as f:
        svg_content = f.read()

    # Temizlik (İş bitti mi iz bırakmayalum)
    os.remove(temp_input)
    os.remove(temp_output)

    return StreamingResponse(io.BytesIO(svg_content), media_type="image/svg+xml")

@app.get("/")
def home():
    return {"mesaj": "Dernekpazarı Vektör Servisi Aktif, Uşağum!"}