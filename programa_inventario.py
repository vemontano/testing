import os
import sqlite3
from datetime import datetime

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def obtener_fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

import sync_db

def mostrar_inventario():
    limpiar_pantalla()
    print("--- MÓDULO DE INVENTARIO INDEPENDIENTE ---")
    
    # Intentar sincronizar con Supabase para mostrar el stock actualizado
    sync_db.sincronizar_y_descargar(silencioso=True)
    
    conexion = sqlite3.connect("local.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, cantidad, precio, fecha_modificacion FROM inventario")
    productos = cursor.fetchall()
    conexion.close()
    
    if not productos:
        print("El inventario está vacío.")
    else:
        print(f"{'ID':<5} | {'Producto':<18} | {'Stock':<6} | {'Precio':<8} | {'Última Modif.':<16}")
        print("-" * 65)
        for prod in productos:
            print(f"{prod[0]:<5} | {prod[1]:<18} | {prod[2]:<6} | ${prod[3]:<7.2f} | {prod[4]:<16}")
    
    print("")
    input("Presione Enter para actualizar / volver...")

def agregar_producto():
    limpiar_pantalla()
    print("--- REGISTRAR NUEVO PRODUCTO ---")
    try:
        idx = int(input("Ingrese ID único: "))
        nombre = input("Nombre: ")
        cantidad = int(input("Cantidad: "))
        precio = float(input("Precio: "))
        
        conexion = sqlite3.connect("local.db")
        cursor = conexion.cursor()
        
        cursor.execute("INSERT INTO inventario VALUES (?, ?, ?, ?, ?)", 
                       (idx, nombre, cantidad, precio, "Sin modificaciones"))
        conexion.commit()
        conexion.close()
        print("\n¡Producto agregado a la Base de Datos!")
    except sqlite3.IntegrityError:
        print("\nError: El ID ya existe.")
    except ValueError:
        print("\nError: Datos inválidos.")
    input("\nPresione Enter para continuar...")

if __name__ == "__main__":
    # Asegurar la creación de tablas locales en local.db
    sync_db.inicializar_bd_local()
    
    while True:
        limpiar_pantalla()
        print("=== CONTROL DE INVENTARIO ===")
        print("1. Ver Stock Actual")
        print("2. Registrar Producto Nuevo")
        print("3. Salir")
        opcion = input("Seleccione opción: ")
        if opcion == "1": mostrar_inventario()
        elif opcion == "2": agregar_producto()
        elif opcion == "3": break