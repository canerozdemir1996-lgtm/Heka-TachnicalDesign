FROM python:3.11-slim-bookworm

# Sistem araçları ve meşhur Inkscape'imiz
RUN apt-get update && apt-get install -y \
    inkscape \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Malzemeleri hızlıca kur
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Laz inadını bıraktuk! Railway hangi PORT'u verirse uşak oraya geçecek.
# Eğer kimse port vermezse (senin bilgisayarda falan) yine 8080'de durur.
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"