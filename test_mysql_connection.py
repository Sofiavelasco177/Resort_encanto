#!/usr/bin/env python3
"""
Script para probar la conexión a la base de datos MySQL
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def test_mysql_connection():
    """Prueba la conexión a MySQL"""
    
    # URL de conexión
    database_url = "mysql+pymysql://adriana:adrianac@isladigital.xyz:3311/f58_adriana"
    
    try:
        print("🔄 Probando conexión a MySQL...")
        print(f"📍 Host: isladigital.xyz:3311")
        print(f"👤 Usuario: adriana")
        print(f"🗄️ Base de datos: f58_adriana")
        print("-" * 50)
        
        # Crear engine
        engine = create_engine(database_url, echo=False)
        
        # Probar conexión
        with engine.connect() as connection:
            # Verificar la conexión
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            
            if test_value == 1:
                print("✅ ¡Conexión exitosa a MySQL!")
            
            # Obtener información de la base de datos
            print("\n📊 Información de la base de datos:")
            
            # Versión de MySQL
            result = connection.execute(text("SELECT VERSION() as version"))
            version = result.fetchone()[0]
            print(f"🐬 Versión MySQL: {version}")
            
            # Nombre de la base de datos actual
            result = connection.execute(text("SELECT DATABASE() as db_name"))
            db_name = result.fetchone()[0]
            print(f"🗄️ Base de datos actual: {db_name}")
            
            # Listar tablas existentes
            result = connection.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            
            print(f"\n📋 Tablas encontradas ({len(tables)}):")
            if tables:
                for table in tables:
                    table_name = table[0]
                    print(f"  📄 {table_name}")
                    
                    # Contar registros en cada tabla
                    try:
                        count_result = connection.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
                        count = count_result.fetchone()[0]
                        print(f"     └─ Registros: {count}")
                    except Exception as e:
                        print(f"     └─ Error contando: {str(e)}")
            else:
                print("  ⚠️ No se encontraron tablas")
            
            print("\n🎉 ¡Conexión MySQL configurada correctamente!")
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ Error de SQLAlchemy: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_mysql_connection()
    sys.exit(0 if success else 1)