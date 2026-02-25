FROM python:3.8-slim

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia il codice
COPY app/ ./app/

# Crea directory necessarie
RUN mkdir -p uploads outputs logs

# Porta
EXPOSE 8000

# Avvio
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT