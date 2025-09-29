# config.py
import os


class Config:
    # Construir URI de base de datos desde variables de entorno
    DB_USER = os.environ.get('DB_USER', 'user')  # ← Usando 'user' por defecto
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')  # ← Usando 'password' por defecto
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME')
    
    # URI de base de datos - priorizar DATABASE_URL completa, luego construir desde componentes
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    elif all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?connect_timeout=10&read_timeout=10&write_timeout=10'
    else:
        # Fallback para desarrollo local con SQLite si no hay configuración MySQL
        SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/tu_base_de_datos.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_timeout': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_unique_and_secret_key_change_in_production')  # Clave secreta para sesiones
    # Google OAuth2 credentials (set these env vars to enable Google login locally)
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    # development helper: when True and real Google creds are missing, /google-login will use a simulated login
    ENABLE_DEV_GOOGLE = os.environ.get('ENABLE_DEV_GOOGLE', '1') == '1'