# config.py
import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@127.0.0.1:3306/islaencanto')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_unique_and_secret_key')  # Clave secreta para sesiones
    # Google OAuth2 credentials (set these env vars to enable Google login locally)
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    # development helper: when True and real Google creds are missing, /google-login will use a simulated login
    ENABLE_DEV_GOOGLE = os.environ.get('ENABLE_DEV_GOOGLE', '1') == '1'