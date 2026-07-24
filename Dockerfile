FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para cachear
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Puerto que Railway asigna
EXPOSE $PORT

# Comando de inicio
CMD gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --log-level debug --error-logfile - --access-logfile - --capture-output main:app
