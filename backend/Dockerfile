# Utilisation de l'image Python officielle
FROM python:3.10

# On va copier TOUT le repo dans /app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On copie tout le dossier backend (et db, etc.)
COPY . .

# On indique à Python que /app est un package root
ENV PYTHONPATH=/app

EXPOSE 8000

# Lance la FastAPI : module backend.main, attribut app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]