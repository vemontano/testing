import sqlite3

def inicializar_bd():
    conexion = sqlite3.connect("sistema.db")
    cursor = conexion.cursor()
    
    # Creamos la tabla de inventario si no existe
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        precio REAL NOT NULL,
        fecha_modificacion TEXT NOT NULL
    )
    """)
    
    # Insertamos datos de prueba si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM inventario")
    if cursor.fetchone()[0] == 0:
        productos = [
            (1, "Escritorio Madera", 10, 120.0, "2026-06-17 10:00"),
            (2, "Silla Ergonómica", 15, 85.0, "2026-06-17 10:00")
        ]
        cursor.executemany("INSERT INTO inventario VALUES (?, ?, ?, ?, ?)", productos)
        conexion.commit()
        print("Base de datos 'sistema.db' creada con éxito.")
        
    conexion.close()

if __name__ == "__main__":
    inicializar_bd()