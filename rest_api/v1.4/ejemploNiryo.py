from pyniryo import * 
import random #borrar 
from datetime import time
import time

robot = None
sensorDI5 = None
sensorDI1 = None
conveyor_id = None

def init():
    print("Hola desde init()")
    global robot, sensorDI5, sensorDI1, conveyor_id
    robot = NiryoRobot("localhost")
    robot.calibrate_auto()
    robot.update_tool()
    sensorDI5 = PinID.DI5
    sensorDI1 = PinID.DI1
    conveyor_id = robot.set_conveyor()
    

def exitNiryo():
    print("Adiós desde exit()")
    
    global robot, conveyor_id
    if robot is not None:
        robot.unset_conveyor(conveyor_id)
        robot.close_connection()
    

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
    '''
    if robot.digital_read(sensorDI5) == PinState.HIGH:
        return "HIGH"
    else:
        return "LOW"
    '''

def mover_cinta(velocidad, direccion):
    print(f"No hago nada, pero tengo {direccion} y {velocidad} :)")
    
    if direccion == 'forward':
        robot.run_conveyor(conveyor_id, speed=velocidad, direction=ConveyorDirection.FORWARD)
    elif direccion == 'backward':
        robot.run_conveyor(conveyor_id, speed=velocidad, direction=ConveyorDirection.BACKWARD)
    

def parar_cinta():
    print("No hago nada x2 :)")
    '''
    robot.stop_conveyor(conveyor_id)
    '''

def control_herramienta(accion):
    print(f"{accion} herramienta")
    '''
    if (accion == 'activar'):
        robot.activate_tool()
    else:
        robot.deactivate_tool()
    '''

def mover_robot(x, y, z, roll, pitch, yaw):
    print(f"Moviendo robot a: {x}, {y}, {z}, {roll}, {pitch}, {yaw}")
    '''
    robot.move_joints(x, y, z, roll, pitch, yaw)
    '''

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