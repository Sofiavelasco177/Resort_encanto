import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def check_mysql_schema():
    """Verificar esquema de la base de datos MySQL"""
    
    # Configuración de base de datos
    DATABASE_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://adriana:adrianac@isladigital.xyz:3311/f58_adriana')
    
    try:
        print("🔄 Conectando a la base de datos MySQL...")
        # Conectar a la base de datos
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Obtener información de la tabla usuario
            result = conn.execute(text("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    COLUMN_KEY,
                    EXTRA
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'f58_adriana' 
                AND TABLE_NAME = 'usuario'
                ORDER BY ORDINAL_POSITION
            """))
            
            columns = result.fetchall()
            
            print("\n=== ESQUEMA ACTUAL DE LA TABLA 'usuario' (MySQL) ===")
            print("Columna | Tipo | Nullable | Default | Key | Extra")
            print("-" * 70)
            
            if columns:
                for col in columns:
                    print(f"{col[0]} | {col[1]} | {col[2]} | {col[3]} | {col[4]} | {col[5]}")
                
                # Verificar si existen datos
                result = conn.execute(text("SELECT COUNT(*) FROM usuario"))
                count = result.fetchone()[0]
                
                print(f"\n=== DATOS EN LA TABLA 'usuario' ===")
                print(f"Total de registros: {count}")
                
                if count > 0:
                    result = conn.execute(text("SELECT idUsuario, usuario, correo, rol FROM usuario LIMIT 3"))
                    rows = result.fetchall()
                    print("\nPrimeros 3 registros:")
                    for row in rows:
                        print(f"ID: {row[0]}, Usuario: {row[1]}, Correo: {row[2]}, Rol: {row[3]}")
            else:
                print("⚠️ La tabla 'usuario' no existe o no se encontraron columnas")
        
        print("\n✅ Verificación completada exitosamente")
        
    except SQLAlchemyError as e:
        print(f"❌ Error de base de datos: {str(e)}")
    except Exception as e:
        print(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    check_mysql_schema()