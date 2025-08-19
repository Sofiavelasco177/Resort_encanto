from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuario'
    idUsuario = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)  # Mejor como String
    correo = db.Column(db.String(255), nullable=True, unique=True)
    contraseña = db.Column(db.String(255), nullable=False)  
    direccion = db.Column(db.String(255), nullable=True)
    fechaNacimiento = db.Column(db.Date, nullable=True)
    rol = db.Column(db.String(20), nullable=True, default='usuario')


