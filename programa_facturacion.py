import os
import sqlite3
from datetime import datetime

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def obtener_fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

import sync_db

def obtener_inventario_bd():
    # Nos aseguramos de que las tablas existan
    sync_db.inicializar_bd_local()
    
    conexion = sqlite3.connect("local.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, cantidad, precio FROM inventario")
    productos = cursor.fetchall()
    conexion.close()
    # Lo convertimos a diccionario para mantener la lógica cómoda del carrito
    return {p[0]: {"nombre": p[1], "cantidad": p[2], "precio": p[3]} for p in productos}

def generar_factura():
    limpiar_pantalla()
    print("=== MÓDULO DE FACTURACIÓN INDEPENDIENTE ===")
    cliente = input("Cliente: ") or "Consumidor Final"
    carrito = []
    
    while True:
        limpiar_pantalla()
        # Consulta la BD en tiempo real en cada ciclo del bucle
        inventario_actual = obtener_inventario_bd()
        
        print("--- PRODUCTOS EN SISTEMA ---")
        for idx, d in inventario_actual.items():
            print(f"ID: {idx} | {d['nombre']:<18} | Stock: {d['cantidad']:<4} | Pr: ${d['precio']}")
        print("-" * 50)
        
        opcion = input("ID del producto a vender (o 'F' para facturar): ")
        if opcion.upper() == 'F':
            if not carrito: continue
            break
            
        try:
            idx = int(opcion)
            if idx not in inventario_actual:
                input("ID no existe. Enter para continuar...")
                continue
                
            prod = inventario_actual[idx]
            cant = int(input(f"Cantidad (Disponibles: {prod['cantidad']}): "))
            
            if cant <= 0 or cant > prod['cantidad']:
                input("Cantidad inválida o superior al stock. Enter...")
                continue
                
            carrito.append({"id": idx, "nombre": prod['nombre'], "cantidad": cant, "precio": prod['precio']})
            input("¡Añadido! Enter para continuar...")
        except ValueError:
            pass

    # PROCESAR TRANSACCIÓN EN LA BD
    import json
    conexion = sqlite3.connect("local.db")
    cursor = conexion.cursor()
    fecha = obtener_fecha_actual()
    
    subtotal = sum(item['cantidad'] * item['precio'] for item in carrito)
    total_factura = subtotal * 1.16
    detalles_txt = json.dumps(carrito)
    
    # 1. Guardar en cola de facturas pendientes localmente
    cursor.execute("""
        INSERT INTO facturas_pendientes (cliente, rif_cedula, fecha, monto_total, detalles_json)
        VALUES (?, ?, ?, ?, ?)
    """, (cliente, "N/A", fecha, total_factura, detalles_txt))
    
    # 2. Descontar del stock local
    for item in carrito:
        cursor.execute("""
            UPDATE inventario 
            SET cantidad = cantidad - ?, fecha_modificacion = ? 
            WHERE id = ?
        """, (item['cantidad'], fecha, item['id']))
        
    conexion.commit()
    conexion.close()
    
    # 3. Sincronizar automáticamente en segundo plano si hay internet
    sync_db.sincronizar_y_descargar(silencioso=True)
    
    # Imprimir Factura en pantalla
    limpiar_pantalla()
    print("==========================================================")
    print("                     DAJUSCA MUEBLES                      ")
    print("==========================================================")
    print(f"Cliente: {cliente} | Fecha: {fecha}")
    print("-" * 58)
    subtotal = 0
    for item in carrito:
        tot = item['cantidad'] * item['precio']
        subtotal += tot
        print(f"{item['cantidad']:<5} | {item['nombre']:<22} | ${item['precio']:<8.2f} | ${tot:<10.2f}")
    print("-" * 58)
    print(f"TOTAL PAGAR: ${subtotal * 1.16:>10.2f} (Con IVA)")
    print("==========================================================")
    input("\nFactura procesada. Enter para volver...")

if __name__ == "__main__":
    # Intentar sincronizar al arrancar el programa
    sync_db.sincronizar_y_descargar(silencioso=True)
    
    while True:
        limpiar_pantalla()
        print("=== SISTEMA DE FACTURACIÓN ===")
        print("1. Crear Nueva Factura")
        print("2. Salir")
        op = input("Seleccione opción: ")
        if op == "1": generar_factura()
        elif op == "2": break