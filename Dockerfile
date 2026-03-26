# Python 3.11'in daha geniş bir sürümünü kullanalum ki bağımlılık derdi olmasun
FROM python:3.11-slim-bookworm

# 1. Aşama: Sistem güncelleme ve Inkscape kurulumu (Hata payını sıfırladık)
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    inkscape \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    build-essential \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 2. Aşama: Çalışma klasörü
WORKDIR /app

# 3. Aşama: Bağımlılıklar (Önce bunları halledelim ki hızlansun)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Aşama: Kodları içeri alalum
COPY . .

# 5. Aşama: Railway için port ayarı (8080 standarttur)
EXPOSE 8080

# Çalıştıralum gitsin!
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]