# config.py

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@127.0.0.1:3306/islaencanto'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_unique_and_secret_key'  # Clave secreta para sesiones