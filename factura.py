import os
from datetime import datetime

# Simulamos un pequeño inventario disponible para vender
productos_disponibles = {
    1: {"nombre": "Escritorio Madera", "precio": 120.0},
    2: {"nombre": "Silla Ergonómica", "precio": 85.0},
    3: {"nombre": "Archivador Metal", "precio": 45.0}
}

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def obtener_fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def mostrar_productos_venta():
    print("\n--- PRODUCTOS DISPONIBLES ---")
    print(f"{'ID':<5} | {'Producto':<20} | {'Precio Unitario':<15}")
    print("-" * 45)
    for idx, datos in productos_disponibles.items():
        print(f"{idx:<5} | {datos['nombre']:<20} | ${datos['precio']:<14.2f}")
    print("-" * 45)

def generar_factura():
    limpiar_pantalla()
    print("========================================")
    print("       NUEVA FACTURA DE VENTA           ")
    print("========================================")
    
    # 1. Datos del Cliente o Empresa
    cliente = input("Nombre del Cliente o Empresa: ")
    if not cliente.strip():
        cliente = "Consumidor Final"
        
    rif_cedula = input("RIF / Cédula de Identidad: ")
    
    # Lista para almacenar los productos que compra este cliente
    # Estructura: {"nombre": str, "cantidad": int, "precio_uni": float, "total_item": float}
    carrito = []
    
    # 2. Bucle para agregar productos a la factura
    while True:
        mostrar_productos_venta()
        try:
            opcion = input("\nIngrese el ID del producto a vender (o 'F' para finalizar la factura): ")
            
            if opcion.upper() == 'F':
                if not carrito:
                    print("\nNo puedes generar una factura vacía.")
                    input("Presiona Enter para continuar...")
                    continue
                break
                
            idx = int(opcion)
            if idx not in productos_disponibles:
                print("\nError: ID de producto no válido.")
                input("Presiona Enter para continuar...")
                limpiar_pantalla()
                continue
                
            cantidad = int(input(f"Cantidad de '{productos_disponibles[idx]['nombre']}': "))
            if cantidad <= 0:
                print("\nError: La cantidad debe ser mayor a 0.")
                input("Presiona Enter para continuar...")
                limpiar_pantalla()
                continue
            
            # Calcular datos del item y añadir al carrito
            prod_info = productos_disponibles[idx]
            total_item = prod_info['precio'] * cantidad
            
            carrito.append({
                "nombre": prod_info['nombre'],
                "cantidad": cantidad,
                "precio_uni": prod_info['precio'],
                "total_item": total_item
            })
            
            print(f"\n¡{prod_info['nombre']} (x{cantidad}) añadido!")
            input("Presiona Enter para seguir agregando...")
            limpiar_pantalla()
            
        except ValueError:
            print("\nError: Entrada inválida. Ingrese un número o 'F'.")
            input("Presiona Enter para continuar...")
            limpiar_pantalla()

    # 3. Cálculos de la Factura
    subtotal = sum(item['total_item'] for item in carrito)
    iva = subtotal * 0.16  # Asumiendo un IVA del 16%
    total_pagar = subtotal + iva

    # 4. Diseño e Impresión Visual de la Factura en CMD
    limpiar_pantalla()
    print("==========================================================")
    print("                     DAJUSCA MUEBLES                      ")
    print("                 DOCUMENTO DE FACTURACIÓN                 ")
    print("==========================================================")
    print(f"Fecha/Hora: {obtener_fecha_actual()}")
    print(f"Nro. Factura: #0001 (Simulado)")
    print("-" * 58)
    print(f"CLIENTE: {cliente}")
    print(f"RIF/CI:  {rif_cedula if rif_cedula else 'N/A'}")
    print("==========================================================")
    
    # Cabecera de la tabla de artículos
    print(f"{'Cant.':<6} | {'Descripción':<22} | {'P. Unit':<10} | {'Total':<12}")
    print("-" * 58)
    
    # Listar los productos comprados
    for item in carrito:
        print(f"{item['cantidad']:<6} | {item['nombre']:<22} | ${item['precio_uni']:<9.2f} | ${item['total_item']:<11.2f}")
        
    print("-" * 58)
    # Totales alineados a la derecha
    print(f"{'':<30}{'SUBTOTAL:':<14} ${subtotal:>10.2f}")
    print(f"{'':<30}{'I.V.A. (16%):':<14} ${iva:>10.2f}")
    print(f"{'':<30}{'TOTAL A PAGAR:':<14} ${total_pagar:>10.2f}")
    print("==========================================================")
    print("          ¡Gracias por su compra en Dajusca!              ")
    print("==========================================================")
    print("\n")
    input("Presione Enter para finalizar y salir...")

if __name__ == "__main__":
    generar_factura()