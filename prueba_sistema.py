import os
import sqlite3
import psycopg2
import json
import socket
from datetime import datetime

# Función para cargar variables desde claves.env de forma segura
def cargar_claves(ruta=None):
    if ruta is None:
        # Busca el archivo claves.env en el mismo directorio donde está este script
        directorio_script = os.path.dirname(os.path.abspath(__file__))
        ruta = os.path.join(directorio_script, "claves.env")
        
    if os.path.exists(ruta):
        with open(ruta, "r") as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith("#"):
                    partes = linea.split("=", 1)
                    if len(partes) == 2:
                        os.environ[partes[0].strip()] = partes[1].strip()

cargar_claves()

# =========================================================================
# CONFIGURACIÓN DE CREDENCIALES (Cargadas de forma segura con respaldos por defecto)
# =========================================================================
DB_HOST = os.environ.get("DB_HOST", "aws-0-us-east-2.pooler.supabase.com")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "postgres.qatcfaqnqmofeovblkar")
DB_PASS = os.environ.get("DB_PASS", "auPyS15OfpBTHKKi")
DB_PORT = os.environ.get("DB_PORT", "6543")
DB_PROJECT_ID = os.environ.get("DB_PROJECT_ID", "qatcfaqnqmofeovblkar")

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

import urllib.request

def comprobar_internet():
    try:
        # Intenta abrir Google con un límite de tiempo de 3 segundos
        # Esto simula exactamente lo que hace tu navegador web
        urllib.request.urlopen('https://www.google.com', timeout=3)
        return True
    except Exception:
        return False

def obtener_conexion_nube():
    try:
        # Añadimos las opciones específicas que exige el Pooler de Supabase
        argumentos_conexion = {
            "host": DB_HOST,
            "database": DB_NAME,
            "user": DB_USER,
            "password": DB_PASS,
            "port": DB_PORT,
            "connect_timeout": 5,
        }
        if DB_PROJECT_ID:
            argumentos_conexion["options"] = f"-c project={DB_PROJECT_ID}"
        
        conexion = psycopg2.connect(**argumentos_conexion)
        return conexion
    except Exception as error_real:
        print(f"\n[ALERTA NUBE] Error de conexión: {error_real}")
        return None

# =========================================================================
# LÓGICA DE SINCRONIZACIÓN Y CONSULTA
# =========================================================================
def sincronizar_y_descargar():
    """Intenta subir facturas offline y descarga el stock fresco de la nube"""
    if not comprobar_internet():
        print("[ESTADO] Trabajando en MODO OFFLINE (Sin internet).")
        return False

    conn_nube = obtener_conexion_nube()
    if conn_nube is None:
        print("\n[AVISO] No se pudo establecer el puente con Supabase.")
        print(f"Revisa si tus credenciales en el archivo coinciden exactamente con tu panel.")
        print(f"Host configurado: {DB_HOST} | Puerto: {DB_PORT} | BD: {DB_NAME}\n")
        print("[ESTADO] Trabajando en MODO OFFLINE (No se pudo conectar a Supabase).")
        return False

    print("[ESTADO] Conectado a la NUBE. Sincronizando datos...")
    try:
        cursor_nube = conn_nube.cursor()
        conn_local = sqlite3.connect("local.db")
        cursor_local = conn_local.cursor()

        # 1. Subir facturas retenidas en local
        cursor_local.execute("SELECT id, cliente, rif_cedula, fecha, monto_total, detalles_json FROM facturas_pendientes")
        facturas_offline = cursor_local.fetchall()

        if facturas_offline:
            print(f"-> Subiendo {len(facturas_offline)} facturas pendientes a Supabase...")
            for fac in facturas_offline:
                id_local, cliente, rif, fecha, total, detalles_json = fac
                
                # Truncamos los valores para cumplir con los límites varchar(150) y varchar(50) de Supabase
                cliente_seguro = cliente[:150] if cliente else "Sin Nombre"
                rif_seguro = rif[:50] if rif else "N/A"
                
                # Insertar en Supabase
                cursor_nube.execute("""
                    INSERT INTO facturas (cliente, rif_cedula, fecha, monto_total, detalles_json)
                    VALUES (%s, %s, %s, %s, %s)
                """, (cliente_seguro, rif_seguro, fecha, total, detalles_json))
                
                # Eliminar de la cola local
                cursor_local.execute("DELETE FROM facturas_pendientes WHERE id = ?", (id_local,))
            
            conn_nube.commit()
            conn_local.commit()

        # 2. Descargar el inventario fresco de Supabase para actualizar la PC local
        cursor_nube.execute("SELECT id, nombre, cantidad, precio, to_char(fecha_modificacion, 'YYYY-MM-DD HH24:MI') FROM inventario")
        productos_nube_crudos = cursor_nube.fetchall()

        # Convertimos el precio (Decimal) a float para que sqlite3 pueda guardarlo correctamente
        productos_nube = [
            (p[0], p[1], p[2], float(p[3]) if p[3] is not None else 0.0, p[4])
            for p in productos_nube_crudos
        ]

        cursor_local.execute("DELETE FROM inventario")
        cursor_local.executemany("INSERT INTO inventario VALUES (?, ?, ?, ?, ?)", productos_nube)
        
        conn_local.commit()
        conn_local.close()
        conn_nube.close()
        print("[SISTEMA] Sincronización exitosa. Base de datos local actualizada.")
        return True
    except Exception as e:
        print(f"\n[ERROR CRÍTICO DE CONEXIÓN] El sistema operativo o la BD rechazó el intento.")
        print(f"Detalle técnico del error: {e}\n") # <- ESTA LÍNEA NOS DIRÁ LA VERDAD
        return False

def mostrar_inventario_local():
    conn = sqlite3.connect("local.db")
    cursor = conn.cursor()
    
    # --- CONSTRUCTOR AUTOMÁTICO (Por si no existían las tablas) ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        precio REAL NOT NULL,
        fecha_modificacion TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facturas_pendientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT NOT NULL,
        rif_cedula TEXT,
        fecha TEXT NOT NULL,
        monto_total REAL NOT NULL,
        detalles_json TEXT NOT NULL
    )
    """)
    
    # Si la tabla estaba vacía, le metemos datos de prueba locales
    cursor.execute("SELECT COUNT(*) FROM inventario")
    if cursor.fetchone()[0] == 0:
        productos_iniciales = [
            (1, "Escritorio Madera", 10, 120.0, "2026-06-17 10:00"),
            (2, "Silla Ergonómica", 15, 85.0, "2026-06-17 10:00")
        ]
        cursor.executemany("INSERT INTO inventario VALUES (?, ?, ?, ?, ?)", productos_iniciales)
        conn.commit()
    # ---------------------------------------------------------------

    # Ahora sí, leemos los datos de forma segura
    cursor.execute("SELECT id, nombre, cantidad, precio, fecha_modificacion FROM inventario")
    productos = cursor.fetchall()
    conn.close()

    print("\n--- STOCK DISPONIBLE (VISTA LOCAL) ---")
    for p in productos:
        print(f"ID: {p[0]} | {p[1]:<18} | Stock: {p[2]:<3} | Precio: ${p[3]} | Modif: {p[4]}")
    print("-" * 70) 

    print("\n--- STOCK DISPONIBLE (VISTA LOCAL) ---")
    for p in productos:
        print(f"ID: {p[0]} | {p[1]:<18} | Stock: {p[2]:<3} | Precio: ${p[3]} | Modif: {p[4]}")
    print("-" * 70)

# =========================================================================
# PROCESO DE VENTA (FACTURACIÓN)
# =========================================================================
def registrar_venta_offline(cliente, productos_carro, total_factura):
    """Guarda la factura localmente para subirla después y descuenta el stock local"""
    conn = sqlite3.connect("local.db")
    cursor = conn.cursor()
    fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    detalles_txt = json.dumps(productos_carro)

    # Guardar en cola de pendientes
    cursor.execute("""
        INSERT INTO facturas_pendientes (cliente, rif_cedula, fecha, monto_total, detalles_json)
        VALUES (?, ?, ?, ?, ?)
    """, (cliente, "N/A", fecha_str, total_factura, detalles_txt))

    # Descontar del stock de la PC local inmediatamente
    for p in productos_carro:
        cursor.execute("""
            UPDATE inventario 
            SET cantidad = cantidad - ?, fecha_modificacion = ? 
            WHERE id = ?
        """, (p['cantidad'], fecha_str, p['id']))

    conn.commit()
    conn.close()
    print("\n[✓] ¡Venta guardada localmente de forma segura!")

# =========================================================================
# FLUJO DE LA PRUEBA
# =========================================================================
def ejecutar_prueba():
    limpiar_pantalla()
    print("=== INICIANDO PRUEBA DE COLA OFFLINE CON SUPABASE ===")
    
    # Intentamos sincronizar al arrancar
    online = sincronizar_y_descargar()
    mostrar_inventario_local()

    # Simulamos una venta rápida de prueba
    print("\n--- SIMULANDO UNA VENTA ---")
    cliente = input("Nombre del cliente para la prueba: ") or "Cliente Prueba"
    
    # Simulación fija: Vendemos 2 unidades del producto ID 1 (Escritorio)
    id_vender = 1
    cant_vender = 2
    precio_item = 120.0
    total = cant_vender * precio_item

    carro = [{"id": id_vender, "nombre": "Escritorio Madera", "cantidad": cant_vender, "precio": precio_item}]

    print(f"Procesando venta: 2 Escritorios. Total a pagar: ${total * 1.16:.2f} (Con IVA)")
    
    # Registramos localmente pase lo que pase
    registrar_venta_offline(cliente, carro, total * 1.16)

    # Intentamos sincronizar inmediatamente después de la venta
    print("\n--- INTENTANDO ENVIAR LA VENTA A LA NUBE ---")
    sincronizar_y_descargar()
    
    print("\nPrueba finalizada.")

if __name__ == "__main__":
    ejecutar_prueba()