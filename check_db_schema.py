import sqlite3
import os

# Conectar a la base de datos
db_path = 'instance/tu_base_de_datos.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener el esquema de la tabla usuario
    cursor.execute("PRAGMA table_info(usuario)")
    columns = cursor.fetchall()
    
    print("=== ESQUEMA ACTUAL DE LA TABLA 'usuario' ===")
    print("ID | Nombre | Tipo | NotNull | Default | PrimaryKey")
    print("-" * 60)
    for col in columns:
        print(f"{col[0]} | {col[1]} | {col[2]} | {col[3]} | {col[4]} | {col[5]}")
    
    # Verificar si existen datos
    cursor.execute("SELECT COUNT(*) FROM usuario")
    count = cursor.fetchone()[0]
    print(f"\nCantidad de registros en la tabla: {count}")
    
    if count > 0:
        # Mostrar algunos registros (sin mostrar contraseñas)
        cursor.execute("SELECT idUsuario, usuario, correo, rol FROM usuario LIMIT 3")
        rows = cursor.fetchall()
        print("\n=== PRIMEROS 3 REGISTROS ===")
        for row in rows:
            print(f"ID: {row[0]}, Usuario: {row[1]}, Correo: {row[2]}, Rol: {row[3]}")
    
    conn.close()
else:
    print(f"La base de datos {db_path} no existe")