# config.py
import os


class Config:
    # Preferencia: usar MySQL con estos valores por defecto (se pueden sobreescribir con variables de entorno)
    # mysql+pymysql://adriana:adrianac@isladigital.xyz:3311/f58_adriana
    DB_USER = os.environ.get('DB_USER', 'adriana')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'adrianac')
    DB_HOST = os.environ.get('DB_HOST', 'isladigital.xyz')
    DB_PORT = os.environ.get('DB_PORT', '3311')
    DB_NAME = os.environ.get('DB_NAME', 'f58_adriana')
    
    # Estrategia dual:
    # - Si existe DATABASE_URL -> usarla (MySQL en producción)
    # - Si no existe -> usar SQLite local en 'instance/tu_base_de_datos.db' con ruta ABSOLUTA (evita errores en Windows)
    _base_dir = os.path.dirname(os.path.abspath(__file__))
    _sqlite_path = os.path.join(_base_dir, 'instance', 'tu_base_de_datos.db')
    # Orden de selección de la URI:
    # 1) DATABASE_URL (si está definida)
    # 2) MySQL construido desde variables/valores por defecto
    # 3) SQLite local como fallback
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    elif all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
        SQLALCHEMY_DATABASE_URI = (
            f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
            f'?connect_timeout=10&read_timeout=10&write_timeout=10'
        )
    else:
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{_sqlite_path}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Esquema preferido para generar URLs externas (útil para OAuth tras proxy)
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'http')
    
    # Configuración adaptable según el tipo de base de datos
    if 'sqlite' in SQLALCHEMY_DATABASE_URI:
        # Configuración optimizada para SQLite
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }
    else:
        # Configuración para MySQL
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_timeout': 10,
            'pool_recycle': 300,
            'pool_pre_ping': True
        }