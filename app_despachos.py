import datetime
import json
import os

# Nombre del archivo para persistencia
DATA_FILE = "despachos_data.json"

# Lista global para almacenar los despachos en memoria.
# Cada despacho es un diccionario.
lista_despachos = []

# Contador global para generar IDs internos secuenciales y únicos.
# Se carga y guarda junto con los datos para mantener la secuencia entre sesiones.
next_id_interno = 1

# --- Funciones de persistencia de Datos (JSON) ---

def guardar_datos():
    """
    Guarda la lista_despachos actual y el contador next_id_interno en el archivo JSON (DATA_FILE).
    Los objetos datetime se convierten a formato ISO para la serialización.
    """
    global lista_despachos
    datos_para_guardar = []
    for despacho in lista_despachos:
        # Copia para no modificar el original en memoria con strings
        despacho_serializable = despacho.copy()
        if isinstance(despacho_serializable.get("fecha_hora_inicio"), datetime.datetime):
            despacho_serializable["fecha_hora_inicio"] = despacho_serializable["fecha_hora_inicio"].isoformat()
        if isinstance(despacho_serializable.get("fecha_hora_fin"), datetime.datetime):
            despacho_serializable["fecha_hora_fin"] = despacho_serializable["fecha_hora_fin"].isoformat()
        datos_para_guardar.append(despacho_serializable)
    
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({"despachos": datos_para_guardar, "next_id_interno": next_id_interno}, f, indent=4)
    except IOError as e:
        print(f"Error al guardar datos: {e}")

def cargar_datos():
    """
    Carga los despachos y el contador next_id_interno desde el archivo JSON (DATA_FILE).
    Convierte las cadenas de fecha ISO de vuelta a objetos datetime.
    Si el archivo no existe o está corrupto, inicia con datos vacíos y/o valores por defecto.
    También recalcula next_id_interno basado en los IDs "INT-XXX" cargados para seguridad.
    """
    global lista_despachos
    global next_id_interno
    if not os.path.exists(DATA_FILE):
        print("Archivo de datos no encontrado. Se creará uno nuevo al guardar.")
        return

    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            despachos_cargados = data.get("despachos", [])
            next_id_interno = data.get("next_id_interno", 1) # Cargar el contador de ID
            
            lista_despachos.clear() # Limpiar la lista actual antes de cargar
            for despacho_data in despachos_cargados:
                if despacho_data.get("fecha_hora_inicio"):
                    try:
                        despacho_data["fecha_hora_inicio"] = datetime.datetime.fromisoformat(despacho_data["fecha_hora_inicio"])
                    except (ValueError, TypeError):
                        print(f"Advertencia: Formato de fecha_hora_inicio inválido para {despacho_data.get('id_despacho')}. Se dejará como None.")
                        despacho_data["fecha_hora_inicio"] = None
                if despacho_data.get("fecha_hora_fin"):
                    try:
                        despacho_data["fecha_hora_fin"] = datetime.datetime.fromisoformat(despacho_data["fecha_hora_fin"])
                    except (ValueError, TypeError):
                        print(f"Advertencia: Formato de fecha_hora_fin inválido para {despacho_data.get('id_despacho')}. Se dejará como None.")
                        despacho_data["fecha_hora_fin"] = None
                lista_despachos.append(despacho_data)
            print(f"Datos cargados correctamente desde {DATA_FILE}. {len(lista_despachos)} despachos.")
            # Re-calcular next_id_interno basado en los IDs cargados que son "INT-XXX"
            max_int_id = 0
            for d in lista_despachos:
                if d["id_despacho"].startswith("INT-"):
                    try:
                        num_id = int(d["id_despacho"].split("-")[1])
                        if num_id > max_int_id:
                            max_int_id = num_id
                    except (IndexError, ValueError):
                        continue # Ignorar IDs mal formados
            next_id_interno = max_int_id + 1


    except (IOError, json.JSONDecodeError) as e:
        print(f"Error al cargar datos o archivo corrupto: {e}. Se iniciará con una lista vacía.")
        lista_despachos = []
        next_id_interno = 1


def generar_id_interno():
    """Genera un ID secuencial simple para los despachos."""
    global next_id_interno
    # Asegurarse que next_id_interno es al menos 1
    if next_id_interno == 0: next_id_interno =1
    
    # Verificar si ya existe un ID generado con el valor actual de next_id_interno
    # Esto es para evitar colisiones si se borra el json y se vuelve a empezar
    # o si se manipula el json externamente.
    while True:
        id_gen = f"INT-{next_id_interno:03d}"
        if not any(d['id_despacho'] == id_gen for d in lista_despachos):
            break
        next_id_interno += 1
        
    next_id_interno_actual = next_id_interno # Guardamos el valor antes de incrementar para retornarlo
    next_id_interno +=1 # Incrementamos para la proxima llamada
    return f"INT-{next_id_interno_actual:03d}" # Retorna el ID generado y ya incrementó next_id_interno para la próxima.

# --- Funciones del Menú y Operaciones de Despacho ---

def mostrar_menu():
    """Imprime el menú principal de opciones en la consola."""
    print("\n-------------------------------------")
    print("Gestor de Despachos de Bodega")
    print("-------------------------------------")
    print("1. Registrar Nuevo Despacho (Iniciar Tarea)")
    print("2. Marcar Despacho como Completado (Finalizar Tarea)")
    print("3. Ver Todos los Despachos")
    print("4. Ver Despachos En Curso")
    print("5. Ver Despachos Completados")
    # print("6. Ver Despachos Pendientes") # Opción futura
    print("6. Salir") # Ajustado el número por quitar pendientes temporalmente
    print("-------------------------------------")

def registrar_nuevo_despacho():
    """
    Solicita al usuario la información para un nuevo despacho,
    lo crea con estado 'En curso' y la fecha/hora actual,
    y lo añade a la lista_despachos. Luego guarda los datos.
    Permite IDs manuales o generación automática.
    """
    print("\n--- Registrar Nuevo Despacho ---")
    print("Tipos de Despacho: 1: MercadoLibre, 2: Flex, 3: Bluexpress")
    tipo_opcion = input("Seleccione el Tipo de Despacho (1/2/3): ")
    
    tipo_despacho_map = {"1": "MercadoLibre", "2": "Flex", "3": "Bluexpress"}
    if tipo_opcion not in tipo_despacho_map:
        print("Opción de tipo de despacho no válida.")
        return
    tipo_despacho = tipo_despacho_map[tipo_opcion]

    id_despacho_usr = input(f"Ingrese el ID del despacho para {tipo_despacho} (o presione Enter para ID automático): ").strip()
    if not id_despacho_usr:
        id_despacho = generar_id_interno()
        print(f"ID generado automáticamente: {id_despacho}")
    else:
        # Verificar si el ID ya existe para evitar duplicados manuales
        if any(d['id_despacho'] == id_despacho_usr for d in lista_despachos):
            print(f"Error: El ID de despacho '{id_despacho_usr}' ya existe.")
            return
        id_despacho = id_despacho_usr

    detalles = input("Detalles adicionales (opcional): ").strip()
    
    nuevo_despacho = {
        "id_despacho": id_despacho,
        "tipo_despacho": tipo_despacho,
        "estado": "En curso",
        "fecha_hora_inicio": datetime.datetime.now(),
        "fecha_hora_fin": None,
        "detalles": detalles
    }
    lista_despachos.append(nuevo_despacho)
    print(f"Despacho '{id_despacho}' ({tipo_despacho}) registrado y 'En curso'.")
    guardar_datos() # Guardar después de registrar

def marcar_despacho_completado():
    """
    Muestra los despachos actualmente 'En curso'.
    Permite al usuario seleccionar uno para marcarlo como 'Completado',
    registrando la fecha/hora de finalización. Luego guarda los datos.
    """
    print("\n--- Marcar Despacho como Completado ---")
    despachos_en_curso = [d for d in lista_despachos if d["estado"] == "En curso"]
    
    if not despachos_en_curso:
        print("No hay despachos 'En curso' para marcar como completados.")
        return

    print("Despachos 'En curso':")
    for i, despacho in enumerate(despachos_en_curso):
        print(f"{i + 1}. ID: {despacho['id_despacho']} ({despacho['tipo_despacho']}) - Inicio: {despacho['fecha_hora_inicio'].strftime('%Y-%m-%d %H:%M')}")

    try:
        opcion = int(input("Seleccione el número del despacho a completar: ")) -1
        if 0 <= opcion < len(despachos_en_curso):
            despacho_a_completar = despachos_en_curso[opcion]
            # Actualizar el despacho original en lista_despachos
            for d in lista_despachos:
                if d["id_despacho"] == despacho_a_completar["id_despacho"]:
                    d["estado"] = "Completado"
                    d["fecha_hora_fin"] = datetime.datetime.now()
                    print(f"Despacho '{d['id_despacho']}' marcado como 'Completado'.")
                    guardar_datos() # Guardar después de completar
                    break
        else:
            print("Opción no válida.")
    except ValueError:
        print("Entrada no válida. Debe ingresar un número.")

def formatear_fecha(fecha):
    """
    Formatea un objeto datetime a una cadena 'YYYY-MM-DD HH:MM:SS'.
    Retorna 'N/A' si la fecha es None.
    
    Args:
        fecha (datetime.datetime | None): El objeto datetime a formatear.
        
    Returns:
        str: La fecha formateada o 'N/A'.
    """
    if fecha:
        return fecha.strftime('%Y-%m-%d %H:%M:%S')
    return "N/A"

def mostrar_despachos(despachos_a_mostrar, titulo):
    """
    Muestra una lista de despachos formateados en la consola.
    
    Args:
        despachos_a_mostrar (list): Lista de diccionarios de despacho.
        titulo (str): Título a mostrar antes de la lista de despachos.
    """
    print(f"\n--- {titulo} ---")
    if not despachos_a_mostrar:
        print(f"No hay despachos para mostrar en esta categoría.")
        return
        
    for despacho in despachos_a_mostrar:
        print(f"ID: {despacho['id_despacho']:<15} | Tipo: {despacho['tipo_despacho']:<15} | "
              f"Estado: {despacho['estado']:<12} | "
              f"Inicio: {formatear_fecha(despacho['fecha_hora_inicio']):<20} | "
              f"Fin: {formatear_fecha(despacho['fecha_hora_fin']):<20} | "
              f"Detalles: {despacho['detalles']}")

def ver_todos_los_despachos():
    """Filtra y muestra todos los despachos registrados."""
    mostrar_despachos(lista_despachos, "Todos los Despachos")

def ver_despachos_en_curso():
    """Filtra y muestra solo los despachos con estado 'En curso'."""
    despachos_filtrados = [d for d in lista_despachos if d["estado"] == "En curso"]
    mostrar_despachos(despachos_filtrados, "Despachos En Curso")

def ver_despachos_completados():
    """Filtra y muestra solo los despachos con estado 'Completado'."""
    despachos_filtrados = [d for d in lista_despachos if d["estado"] == "Completado"]
    mostrar_despachos(despachos_filtrados, "Despachos Completados")

# --- Función Principal ---

def main():
    """
    Función principal que ejecuta el bucle del programa.
    Carga los datos al inicio y luego muestra el menú,
    procesando la opción del usuario hasta que decide salir.
    """
    cargar_datos() # Cargar datos guardados al iniciar el programa
    
    while True:
        mostrar_menu()
        opcion = input("Ingrese su opción: ")

        if opcion == '1':
            registrar_nuevo_despacho()
        elif opcion == '2':
            marcar_despacho_completado()
        elif opcion == '3':
            ver_todos_los_despachos()
        elif opcion == '4':
            ver_despachos_en_curso()
        elif opcion == '5':
            ver_despachos_completados()
        elif opcion == '6': # Opción de Salir
            print("Saliendo del programa...")
            break
        else:
            print("Opción no válida. Por favor, intente de nuevo.")

if __name__ == "__main__":
    # Punto de entrada del script: ejecuta la función main.
    main()
