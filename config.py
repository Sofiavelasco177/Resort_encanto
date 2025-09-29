# config.py
import os


class Config:
    # Construir URI de base de datos desde variables de entorno
    DB_USER = os.environ.get('DB_USER', 'user')  # ← Usando 'user' por defecto
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')  # ← Usando 'password' por defecto
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'f58_adriana')
    
    # URI de base de datos - Usar SQLite como principal temporalmente
    # Priorizar SQLite para evitar problemas de conexión
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///instance/tu_base_de_datos.db')
    
    # Si necesitas MySQL, descomenta estas líneas y comenta la de arriba:
    # if os.environ.get('DATABASE_URL'):
    #     SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # elif all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    #     SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?connect_timeout=10&read_timeout=10&write_timeout=10'
    # else:
    #     SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/tu_base_de_datos.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
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