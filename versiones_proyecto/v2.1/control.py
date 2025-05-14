from pyniryo import * 
import random #borrar 
from datetime import time
import time

robot = None
sensorDI5 = None
sensorDI1 = None
conveyor_id = None
is_initialized = False

def init():
    print("Hola desde init()")
    global robot, sensorDI5, sensorDI1, conveyor_id, is_initialized
    if is_initialized:
        return True
    try:
        robot = NiryoRobot("10.0.0.101")
        robot.calibrate_auto()
        robot.update_tool()
        sensorDI5 = PinID.DI5
        sensorDI1 = PinID.DI1
        conveyor_id = robot.set_conveyor()
        is_initialized = True
        return True
    except Exception as e:
        print(f"Simulación: No se pudo conectar al robot. Error: {e}")
        robot = None  # Simula que no hay robot conectado
        is_initialized = False
        return False

def exitNiryo():
    print("Adiós desde exit()")
    global robot, conveyor_id, is_initialized
    if robot is not None:
        robot.unset_conveyor(conveyor_id)
        robot.close_connection()
    is_initialized = False

def controlSensorDI1():
    # Genera aleatoriamente "HIGH" o "LOW"
    estado = random.choice(["HIGH", "LOW"])
    return estado

    if robot.digital_read(sensorDI1) == PinState.HIGH:
        return "HIGH"
    else:
        return "LOW"
    

def controlSensorDI5():
    # Genera aleatoriamente "HIGH" o "LOW"
    estado = random.choice(["HIGH", "LOW"])
    return estado
    
    if robot.digital_read(sensorDI5) == PinState.HIGH:
        return "HIGH"
    else:
        return "LOW"
    

def mover_cinta(velocidad, direccion):
    global robot, conveyor_id
    if robot is None:
        print("Error: Robot no inicializado.")
        return False

    try:
        if direccion == 'forward':
            robot.run_conveyor(conveyor_id, speed=velocidad, direction=ConveyorDirection.FORWARD)
            print(f"Cinta moviéndose hacia adelante a velocidad {velocidad}.")
        elif direccion == 'backward':
            robot.run_conveyor(conveyor_id, speed=velocidad, direction=ConveyorDirection.BACKWARD)
            print(f"Cinta moviéndose hacia atrás a velocidad {velocidad}.")
        else:
            print("Error: Dirección inválida. Use 'forward' o 'backward'.")
        return True
    except Exception as e:
        print(f"Error al mover la cinta: {e}")
        return False

def parar_cinta():
    global robot, conveyor_id
    if robot is None or conveyor_id is None:
        print("Error: Robot o cinta no inicializados.")
        return

    try:
        robot.stop_conveyor(conveyor_id)
        print("Cinta detenida correctamente.")
    except Exception as e:
        print(f"Error al detener la cinta: {e}")


def control_herramienta(accion):
    print(f"{accion} herramienta")
    if robot is None:
        print("Error: Robot no inicializado.")
        return False
    
    try:
        if (accion == 'activar'):
            robot.activate_tool()
        else:
            robot.deactivate_tool()
        return True
    except Exception as e:
        print(f"Error controlando herramienta: {e}")
        return False

def mover_robot(x, y, z, roll, pitch, yaw):
    print(f"Moviendo robot a: {x}, {y}, {z}, {roll}, {pitch}, {yaw}")
    if robot is None:
        print("Error: Robot no inicializado.")
        return False
    
    try:
        robot.move_joints(x, y, z, roll, pitch, yaw)
        return True
    except Exception as e:
        print(f"Error moviendo robot: {e}")
        return False

# ESTA PARTE ES EXCLUSIVA DEL MODO AUTOMÁTICO
import threading
pausa_event = threading.Event()
pausa_event.set()

# Función para simular el modo automático
def modo_automatico():
    print("Modo automático activado")

    for i in range(1, 6):
        # Esperar si está pausado
        while not pausa_event.is_set():
            time.sleep(0.1)

        print(f"{i} segundos...")
        time.sleep(1)

    ventosa = {
        "tiempo_agarre1": "12:15:10",
        "tiempo_agarre2": "09:17:22",
        "tiempo_agarre3": "09:20:35",
        "tiempo_dejada1": "09:16:05",
        "tiempo_dejada2": "09:18:30",
        "tiempo_dejada3": "09:21:45",
    }

    # Diccionario sensordi1
    sensordi1 = {
        "tiempo_deteccion_grande1": "09:14:50",
        "tiempo_deteccion_grande2": "09:17:00",
        "tiempo_deteccion_grande3": "09:19:55",
    }

    # Diccionario sensordi5
    sensordi5 = {
        "tiempo_deteccion_peque1": "09:15:30",
        "tiempo_deteccion_peque2": "09:18:10",
        "tiempo_deteccion_peque3": "09:20:40",
    }

    # Diccionario robot
    robot = {
        "tiempo_inicio": "09:14:30",
        "tiempo_final": "09:22:00",
        "paro_manual": False,
        "min_total": 7,
        "seg_total": 30,
        "piezas_peque": 3,
        "piezas_grandes": 3,
        "tiempo_peque": 210,   # en segundos
        "tiempo_grande": 260,  # en segundos
    }

    return ventosa, sensordi1, sensordi5, robot

# Función para el control
def controlar_pausa(orden):
    if orden == "p":
        pausa_event.clear()
        print("Pausado.")
    elif orden == "m":
        pausa_event.set()
        print("Reanudado.")

# Función que ejecuta el modo automático y el control de pausa
def automatico():
    resultados = []

    def wrapper():
        resultados.extend(modo_automatico())

    hilo_robot = threading.Thread(target=wrapper)
    hilo_robot.start()
    hilo_robot.join()

    print("Proceso finalizado.")
    return resultados[0], resultados[1], resultados[2], resultados[3]

def get_sensor_states():
    global sensorDI1, sensorDI5
    try:
        return {
            "DI1": robot.digital_read(sensorDI1),
            "DI5": robot.digital_read(sensorDI5)
        }
    except Exception as e:
        return {
            "DI1": False,
            "DI5": False
        }
