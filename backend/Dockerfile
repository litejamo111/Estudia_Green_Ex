# Contexto de build: raíz del repo (ver deploy/gcp/docker-compose.yml)
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY backend/requirements.txt backend/
RUN pip install -r backend/requirements.txt
COPY backend/ backend/
COPY data/ data/
COPY docs/documentacion/parametros_prueba.json docs/documentacion/parametros_prueba.json
EXPOSE 8000
CMD ["sh","-c","python backend/predicta.py ingesta && uvicorn api:app --app-dir backend --host 0.0.0.0 --port 8000"]
