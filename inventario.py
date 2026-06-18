import os
from datetime import datetime

# Base de datos temporal (Diccionario de productos)
# Ahora incluye campos para 'fecha_registro' y 'fecha_modificacion'
inventario = {
    1: {
        "nombre": "Escritorio Madera", 
        "cantidad": 5, 
        "precio": 120.0,
        "fecha_registro": "2026-06-15 10:30",
        "fecha_modificacion": "Sin modificaciones"
    },
    2: {
        "nombre": "Silla Ergonómica", 
        "cantidad": 12, 
        "precio": 85.0,
        "fecha_registro": "2026-06-16 14:15",
        "fecha_modificacion": "Sin modificaciones"
    }
}

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def obtener_fecha_actual():
    # Retorna la fecha y hora actual en un formato legible (Año-Mes-Día Hora:Minuto)
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def mostrar_menu():
    print("=========================================================================")
    print("                       SISTEMA DE INVENTARIO CMD                         ")
    print("=========================================================================")
    print("1. Ver Inventario Completo")
    print("2. Agregar Nuevo Producto")
    print("3. Actualizar Stock de Producto")
    print("4. Salir")
    print("=========================================================================")

def mostrar_inventario():
    limpiar_pantalla()
    print("--- INVENTARIO ACTUAL ---")
    if not inventario:
        print("El inventario está vacío.")
    else:
        # Ajustamos el ancho de la tabla para dar espacio a las columnas de fechas
        print(f"{'ID':<5} | {'Producto':<18} | {'Stock':<6} | {'Precio':<8} | {'Fecha Registro':<16} | {'Última Modif.':<16}")
        print("-" * 85)
        for idx, datos in inventario.items():
            print(f"{idx:<5} | {datos['nombre']:<18} | {datos['cantidad']:<6} | ${datos['precio']:<7.2f} | {datos['fecha_registro']:<16} | {datos['fecha_modificacion']:<16}")
    print("\n")
    input("Presione Enter para volver al menú...")

def agregar_producto():
    limpiar_pantalla()
    print("--- REGISTRAR NUEVO PRODUCTO ---")
    try:
        idx = int(input("Ingrese el ID único (número): "))
        if idx in inventario:
            print("\nError: El ID ya existe en el sistema.")
            input("\nPresione Enter para continuar...")
            return
        
        nombre = input("Nombre del producto: ")
        cantidad = int(input("Cantidad inicial: "))
        precio = float(input("Precio unitario: "))
        
        # Asignamos la fecha actual al crear el registro
        fecha_actual = obtener_fecha_actual()
        
        inventario[idx] = {
            "nombre": nombre, 
            "cantidad": cantidad, 
            "precio": precio,
            "fecha_registro": fecha_actual,
            "fecha_modificacion": "Sin modificaciones"
        }
        print("\n¡Producto agregado con éxito!")
    except ValueError:
        print("\nError: Entrada de datos inválida (ej. texto en lugar de números).")
    
    input("\nPresione Enter para volver al menú...")

def actualizar_stock():
    limpiar_pantalla()
    print("--- ACTUALIZAR STOCK ---")
    try:
        idx = int(input("Ingrese el ID del producto que desea modificar: "))
        
        # Verificamos si el producto realmente existe
        if idx not in inventario:
            print("\nError: El producto con ese ID no existe.")
            input("\nPresione Enter para continuar...")
            return
        
        producto = inventario[idx]
        print(f"\nProducto seleccionado: {producto['nombre']}")
        print(f"Stock actual: {producto['cantidad']}")
        
        nuevo_stock = int(input("Ingrese la NUEVA cantidad de stock: "))
        if nuevo_stock < 0:
            print("\nError: El stock no puede ser un número negativo.")
            input("\nPresione Enter para continuar...")
            return
            
        # Actualizamos el stock y registramos la fecha de la modificación
        producto['cantidad'] = nuevo_stock
        producto['fecha_modificacion'] = obtener_fecha_actual()
        
        print("\n¡Stock actualizado correctamente!")
    except ValueError:
        print("\nError: Entrada de datos inválida.")
        
    input("\nPresione Enter para volver al menú...")

def ejecucion_principal():
    while True:
        limpiar_pantalla()
        mostrar_menu()
        opcion = input("Seleccione una opción (1-4): ")
        
        if opcion == "1":
            mostrar_inventario()
        elif opcion == "2":
            agregar_producto()
        elif opcion == "3":
            actualizar_stock()  
        elif opcion == "4":
            print("\nSaliendo del sistema... ¡Buen día!")
            break
        else:
            print("\nOpción no válida. Intente de nuevo.")
            input("Presione Enter para continuar...")

if __name__ == "__main__":
    ejecucion_principal()