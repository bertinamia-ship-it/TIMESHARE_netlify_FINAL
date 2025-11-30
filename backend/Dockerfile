FROM python:3.11-slim

# Evitar prompts y asegurar entorno consistente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
