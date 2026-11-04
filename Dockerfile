# Imagen de la aplicación: Dash + FastAPI + servicio de predicción en un único servicio.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# XGBoost necesita la biblioteca de OpenMP, que la imagen slim no trae.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src ./src

# Usuario sin privilegios.
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/modelos /app/data /app/reportes \
    && chown -R app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "alerta_temprana.app:app", "--host", "0.0.0.0", "--port", "8000"]
