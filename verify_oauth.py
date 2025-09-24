#!/usr/bin/env python3
"""
Script para verificar la configuración de Google OAuth
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

client_id = os.getenv('GOOGLE_CLIENT_ID')
client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

print("=== Verificación de Google OAuth ===")
print(f"GOOGLE_CLIENT_ID: {client_id[:20] + '...' if client_id else 'NO CONFIGURADO'}")
print(f"GOOGLE_CLIENT_SECRET: {'**configurado**' if client_secret else 'NO CONFIGURADO'}")
print()

print("URLs de redirección que debes configurar en Google Cloud Console:")
print("- http://127.0.0.1:5000/google_authorize")
print("- http://localhost:5000/google_authorize")
print()

print("Para acceder al login con Google:")
print("- http://127.0.0.1:5000/google-login")
print("- http://localhost:5000/google-login")
print()

print("URL de la aplicación:")
print("- http://127.0.0.1:5000")

if client_id and client_secret:
    print("\n✅ Las credenciales de Google OAuth están configuradas")
else:
    print("\n❌ Las credenciales de Google OAuth NO están configuradas")