# Python 3.11 tabanlı sağlam bir temel seçtik
FROM python:3.11-slim

# Sistem araçlarını ve Inkscape'i kuruyoruz (EPS için şart!)
RUN apt-get update && apt-get install -y \
    inkscape \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Çalışma klasörümüzü ayarlayalım
WORKDIR /app

# Önce malzemeleri yükleyelim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kodları içeri alalım
COPY . .

# Uygulamayı 8080 portundan ayağa kaldıralım
CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "8080"]