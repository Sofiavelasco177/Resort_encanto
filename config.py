# config.py
import os


class Config:
    # Construir URI de base de datos desde variables de entorno
    DB_USER = os.environ.get('DB_USER', 'user')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'database')
    
    # URI de base de datos construida de forma segura
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?connect_timeout=10&read_timeout=10&write_timeout=10'
    )
    
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