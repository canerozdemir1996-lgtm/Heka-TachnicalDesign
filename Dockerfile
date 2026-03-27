FROM python:3.11-slim-bookworm

# Inkscape ve sistem kütüphaneleri (Zorunlu malzemeler)
RUN apt-get update && apt-get install -y \
    inkscape \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Malzemeleri kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kodlari kopyala
COPY . .

# Render'da 10000 nolu kapıdan misafir alacağız
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]