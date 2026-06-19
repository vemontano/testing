import os
import sqlite3
import psycopg2
import urllib.request
import json
from datetime import datetime

# =========================================================================
# CARGAR VARIABLES DESDE CLAVES.ENV
# =========================================================================
def cargar_claves(ruta=None):
    if ruta is None:
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

# Credenciales de base de datos cargadas de forma segura con respaldos
DB_HOST = os.environ.get("DB_HOST", "aws-1-us-east-2.pooler.supabase.com")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "postgres.qatcfaqnqmofeovblkar")
DB_PASS = os.environ.get("DB_PASS", "Prueba123.$")
DB_PORT = os.environ.get("DB_PORT", "6543")
DB_PROJECT_ID = os.environ.get("DB_PROJECT_ID", "qatcfaqnqmofeovblkar")

# =========================================================================
# ABSTRACCIÓN DE CONEXIONES Y DIAGNÓSTICOS
# =========================================================================
def comprobar_internet():
    try:
        urllib.request.urlopen('https://www.google.com', timeout=3)
        return True
    except Exception:
        return False

def obtener_conexion_nube():
    try:
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
        print(f"\n[ALERTA NUBE] Error de conexión a Supabase: {error_real}")
        return None

def inicializar_bd_local():
    """Crea la base de datos local local.db y sus tablas si no existen"""
    conn = sqlite3.connect("local.db")
    cursor = conn.cursor()
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
    
    # Si la tabla local de inventario está vacía, cargamos valores mínimos por defecto
    cursor.execute("SELECT COUNT(*) FROM inventario")
    if cursor.fetchone()[0] == 0:
        productos_iniciales = [
            (1, "Escritorio Madera", 10, 120.0, "2026-06-17 10:00"),
            (2, "Silla Ergonómica", 15, 85.0, "2026-06-17 10:00")
        ]
        cursor.executemany("INSERT INTO inventario VALUES (?, ?, ?, ?, ?)", productos_iniciales)
        conn.commit()
    conn.close()

# =========================================================================
# LÓGICA CENTRAL DE SINCRONIZACIÓN
# =========================================================================
def sincronizar_y_descargar(silencioso=False):
    """
    1. Sube facturas en espera local a Supabase.
    2. Descarga el inventario fresco de Supabase a la base de datos SQLite local.
    """
    # Nos aseguramos de tener la estructura de la base de datos creada localmente
    inicializar_bd_local()

    if not comprobar_internet():
        if not silencioso:
            print("[ESTADO] Trabajando en MODO OFFLINE (Sin conexión a internet).")
        return False

    conn_nube = obtener_conexion_nube()
    if conn_nube is None:
        if not silencioso:
            print("[ESTADO] Trabajando en MODO OFFLINE (No se pudo establecer conexión a Supabase).")
        return False

    if not silencioso:
        print("[ESTADO] Conectado a la NUBE. Sincronizando datos...")
        
    try:
        cursor_nube = conn_nube.cursor()
        conn_local = sqlite3.connect("local.db")
        cursor_local = conn_local.cursor()

        # 1. Subir facturas retenidas en local
        cursor_local.execute("SELECT id, cliente, rif_cedula, fecha, monto_total, detalles_json FROM facturas_pendientes")
        facturas_offline = cursor_local.fetchall()

        if facturas_offline:
            if not silencioso:
                print(f"-> Subiendo {len(facturas_offline)} facturas pendientes a Supabase...")
            for fac in facturas_offline:
                id_local, cliente, rif, fecha, total, detalles_json = fac
                
                # Truncamos los valores para cumplir con los límites de la base de datos remota
                cliente_seguro = cliente[:150] if cliente else "Sin Nombre"
                rif_seguro = rif[:50] if rif else "N/A"
                
                # Insertar en la nube
                cursor_nube.execute("""
                    INSERT INTO facturas (cliente, rif_cedula, fecha, monto_total, detalles_json)
                    VALUES (%s, %s, %s, %s, %s)
                """, (cliente_seguro, rif_seguro, fecha, total, detalles_json))
                
                # Eliminar de la cola local una vez subida con éxito
                cursor_local.execute("DELETE FROM facturas_pendientes WHERE id = ?", (id_local,))
            
            conn_nube.commit()
            conn_local.commit()

        # 2. Descargar el inventario fresco de Supabase para actualizar la PC local
        cursor_nube.execute("SELECT id, nombre, cantidad, precio, to_char(fecha_modificacion, 'YYYY-MM-DD HH24:MI') FROM inventario")
        productos_nube_crudos = cursor_nube.fetchall()

        # Convertimos Decimal (de Postgres numeric) a float para SQLite local
        productos_nube = [
            (p[0], p[1], p[2], float(p[3]) if p[3] is not None else 0.0, p[4])
            for p in productos_nube_crudos
        ]

        cursor_local.execute("DELETE FROM inventario")
        cursor_local.executemany("INSERT INTO inventario VALUES (?, ?, ?, ?, ?)", productos_nube)
        
        conn_local.commit()
        conn_local.close()
        conn_nube.close()
        if not silencioso:
            print("[SISTEMA] Sincronización exitosa. Base de datos local actualizada con Supabase.")
        return True
    except Exception as e:
        if not silencioso:
            print(f"\n[ERROR CRÍTICO EN SINCRONIZACIÓN] {e}\n")
        return False
