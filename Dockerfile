FROM python:3.13-alpine

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para algunos paquetes de Python
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    linux-headers \
    libffi-dev

# Copiar archivos de requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación (todo el repo)
COPY . .

# Asegurar que las plantillas y estáticos se copien explícitamente (por seguridad frente a .dockerignore)
COPY templates/ /app/templates/
COPY Static/ /app/Static/
RUN echo "Contenido de /app/templates durante build:" && ls -la /app/templates || true && \
    echo "Contenido de /app/templates/home durante build:" && ls -la /app/templates/home || true

# Copiar script de entrada y darle permisos
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Crear el directorio instance si no existe (para la base de datos)
RUN mkdir -p instance && chmod 777 instance

# Exponer el puerto 5000
EXPOSE 5000

# Variables de entorno
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Configurar punto de entrada
ENTRYPOINT ["docker-entrypoint.sh"]

# Comando para ejecutar la aplicación con Gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]