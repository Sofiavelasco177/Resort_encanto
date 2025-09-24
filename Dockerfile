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

# Copiar el código de la aplicación
COPY . .

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

# Detener el contenedor en ejecución
RUN docker stop resort-encanto