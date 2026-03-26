FROM python:3.11-slim-bookworm

# Sistem araçlarını ve Inkscape'i (EPS için şart) kuruyoruz
RUN apt-get update && apt-get install -y \
    inkscape \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Önce malzemeler, sonra inşaat
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway'in nazlı portuna uyum sağlayalım
ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]