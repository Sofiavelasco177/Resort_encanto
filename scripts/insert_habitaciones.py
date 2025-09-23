import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.baseDatos import db, nuevaHabitacion
from run import app

habitaciones_fijas = [
    {
        "nombre": "Habitación Básica",
        "descripcion": "Vista al jardín, cama queen size, baño privado, Wi-Fi gratuito, minibar básico.",
        "precio": 180000,
        "cupo_personas": 2,
        "estado": "Disponible",
        "imagen": "img/habitacion(1).jpg"
    },
    {
        "nombre": "Habitación Estándar",
        "descripcion": "Vista parcial al mar, cama king size, baño con ducha y bañera, Wi-Fi de alta velocidad, minibar surtido.",
        "precio": 250000,
        "cupo_personas": 2,
        "estado": "Mantenimiento",
        "imagen": "img/habitacion(2).jpg"
    },
    {
        "nombre": "Habitación Premium",
        "descripcion": "Vista al mar, cama king size premium, baño de mármol con jacuzzi, Wi-Fi VIP ultra rápido, minibar premium.",
        "precio": 320000,
        "cupo_personas": 2,
        "estado": "Ocupada",
        "imagen": "img/habitacion(3).jpg"
    },
    {
        "nombre": "Suite Familiar",
        "descripcion": "Espaciosa suite para familias, con dos ambientes, sala privada, y vistas al jardín. Capacidad para 4 personas.",
        "precio": 400000,
        "cupo_personas": 4,
        "estado": "Disponible",
        "imagen": "img/habitacion(7).jpg"
    },
    {
        "nombre": "Suite Deluxe",
        "descripcion": "Lujo y confort en una suite con vistas parciales al mar, cama king size, y baño en mármol con amenities premium.",
        "precio": 350000,
        "cupo_personas": 2,
        "estado": "Mantenimiento",
        "imagen": "img/habitacion(5).jpg"
    },
    {
        "nombre": "Villa Privada",
        "descripcion": "Villa independiente con piscina privada, jardín y servicio personalizado. Ideal para grupos o celebraciones.",
        "precio": 600000,
        "cupo_personas": 6,
        "estado": "Ocupada",
        "imagen": "img/habitacion(6).jpg"
    }
]

with app.app_context():
    for h in habitaciones_fijas:
        if not nuevaHabitacion.query.filter_by(nombre=h["nombre"]).first():
            nueva = nuevaHabitacion(
                nombre=h["nombre"],
                descripcion=h["descripcion"],
                precio=h["precio"],
                cupo_personas=h["cupo_personas"],
                estado=h["estado"],
                imagen=h["imagen"]
            )
            db.session.add(nueva)
    db.session.commit()
    print("Habitaciones fijas registradas en la base de datos.")
