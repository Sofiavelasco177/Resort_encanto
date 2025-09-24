#!/usr/bin/env python3
"""
Script para inicializar las tablas en la base de datos MySQL
"""
import os
import sys
from flask import Flask
from utils.extensions import db
from models.baseDatos import Usuario, nuevaHabitacion, habitacionHuesped, Huesped, PerfilAdmin
from config import Config

def create_app():
    """Crear aplicación Flask para inicializar DB"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar extensiones
    db.init_app(app)
    
    return app

def init_mysql_database():
    """Inicializar base de datos MySQL con las tablas"""
    
    print("🚀 Inicializando base de datos MySQL...")
    print(f"📍 Host: isladigital.xyz:3311")
    print(f"🗄️ Base de datos: f58_adriana")
    print("-" * 50)
    
    try:
        app = create_app()
        
        with app.app_context():
            # Crear todas las tablas
            print("📋 Creando tablas...")
            db.create_all()
            
            # Verificar tablas creadas
            from sqlalchemy import text
            result = db.session.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            
            print(f"\n✅ Tablas creadas exitosamente ({len(tables)}):")
            for table in tables:
                table_name = table[0]
                print(f"  📄 {table_name}")
                
                # Verificar estructura de cada tabla
                result = db.session.execute(text(f"DESCRIBE `{table_name}`"))
                columns = result.fetchall()
                print(f"     └─ Columnas: {len(columns)}")
                for col in columns:
                    print(f"        • {col[0]} ({col[1]})")
            
            # Crear usuario administrador por defecto si no existe
            admin_user = Usuario.query.filter_by(usuario='admin').first()
            if not admin_user:
                print("\n👤 Creando usuario administrador por defecto...")
                from flask_bcrypt import Bcrypt
                bcrypt = Bcrypt(app)
                
                admin_user = Usuario(
                    usuario='admin',
                    correo='admin@resortencanto.com',
                    contrasena=bcrypt.generate_password_hash('admin123').decode('utf-8'),
                    rol='admin'
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Usuario administrador creado:")
                print("   📧 Email: admin@resortencanto.com")
                print("   🔑 Password: admin123")
                print("   👑 Rol: admin")
            else:
                print("\n👤 Usuario administrador ya existe")
            
            # Crear algunas habitaciones de ejemplo
            if nuevaHabitacion.query.count() == 0:
                print("\n🏨 Creando habitaciones de ejemplo...")
                
                habitaciones_ejemplo = [
                    {
                        'nombre': 'Habitación Deluxe Vista al Mar',
                        'descripcion': 'Habitación elegante con vista panorámica al océano, cama king size y balcón privado.',
                        'precio': 250.00,
                        'cupo_personas': 2,
                        'estado': 'Disponible',
                        'imagen': 'habitacion(1).jpg'
                    },
                    {
                        'nombre': 'Suite Familiar',
                        'descripcion': 'Amplia suite con dos habitaciones, sala de estar y cocina equipada.',
                        'precio': 400.00,
                        'cupo_personas': 4,
                        'estado': 'Disponible',
                        'imagen': 'habitacion(2).jpg'
                    },
                    {
                        'nombre': 'Habitación Estándar',
                        'descripcion': 'Habitación cómoda con todas las comodidades básicas y vista al jardín.',
                        'precio': 150.00,
                        'cupo_personas': 2,
                        'estado': 'Disponible',
                        'imagen': 'habitacion(3).jpg'
                    }
                ]
                
                for hab_data in habitaciones_ejemplo:
                    habitacion = nuevaHabitacion(**hab_data)
                    db.session.add(habitacion)
                
                db.session.commit()
                print(f"✅ {len(habitaciones_ejemplo)} habitaciones de ejemplo creadas")
            else:
                print(f"\n🏨 Ya existen {nuevaHabitacion.query.count()} habitaciones en la base de datos")
            
            print("\n🎉 ¡Base de datos MySQL inicializada correctamente!")
            print("🔗 Conexión establecida con éxito")
            print("📊 Tablas y datos iniciales configurados")
            
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = init_mysql_database()
    sys.exit(0 if success else 1)