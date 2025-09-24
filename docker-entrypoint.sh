#!/bin/sh

# Script de inicialización para Docker

# Crear directorio instance si no existe
mkdir -p /app/instance

# Asegurar permisos correctos
chmod 777 /app/instance

# Crear archivo de base de datos vacío si no existe
touch /app/instance/tu_base_de_datos.db
chmod 666 /app/instance/tu_base_de_datos.db

# Ejecutar la aplicación
exec "$@"