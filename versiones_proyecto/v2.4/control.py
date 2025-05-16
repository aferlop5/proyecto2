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
    print("Intentando conectar con el robot...")
    global robot, sensorDI5, sensorDI1, conveyor_id, is_initialized
    if is_initialized:
        print("El robot ya está conectado.")
        return True

    attempts = 0
    max_attempts = 2

    while attempts < max_attempts:
        try:
            robot = NiryoRobot("10.0.0.101")
            robot.calibrate_auto()
            robot.update_tool()
            sensorDI5 = PinID.DI5
            sensorDI1 = PinID.DI1
            conveyor_id = robot.set_conveyor()
            is_initialized = True
            print("Conexión con el robot establecida.")
            return True
        except Exception as e:
            attempts += 1
            print(f"Intento {attempts} fallido: No se pudo conectar al robot. Error: {e}")

    print("No se pudo establecer conexión con el robot después de 2 intentos. Esto es una simulación.")
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
    global robot, sensorDI5, sensorDI1, conveyor_id

    small_pieces = 0
    large_pieces = 0

    # Posición central de la zona de paletizado
    central_pose = PoseObject(x=0.035, y=0.242, z=0.122, roll=-3.092, pitch=1.458, yaw=-1.413)

    # Offsets(en metros)
    offsets = [
        (-0.075, -0.075),  # Círculo inferior izquierdo
        (0.075, -0.075),   # Círculo inferior derecho
        (-0.075, 0.075),   # Círculo superior izquierdo
    ]

    # Iniciar el cronómetro
    start_time = time.time()

    while small_pieces < 3 or large_pieces < 3:
        # Esperar si está pausado
        while not pausa_event.is_set():
            time.sleep(0.1)

        # Avanzar la cinta hasta detectar una pieza con DI5
        while robot.digital_read(sensorDI5) == PinState.HIGH:
            robot.run_conveyor(conveyor_id, speed=100, direction=ConveyorDirection.FORWARD)
        robot.stop_conveyor(conveyor_id)

        # Analizar la pieza detectada con DI1
        if robot.digital_read(sensorDI1) == PinState.LOW:
            # Retroceder la cinta durante 5 segundos para desechar la pieza grande
            start_time_piece = time.time()
            while time.time() - start_time_piece < 8:
                robot.run_conveyor(conveyor_id, speed=100, direction=ConveyorDirection.BACKWARD)
            robot.stop_conveyor(conveyor_id)
            large_pieces += 1
        else:
            # Paletizar la pieza pequeña
            robot.move_joints(0.057, 0.098, -0.213, -0.075, -1.447, 0.06)
            robot.move_joints(0.47, -0.66, -0.28, -0.01, -0.6, -0.16)
            robot.grasp_with_tool()
            robot.move_joints(0.99, -0.225, -0.513, -0.038, -0.632, -0.026)

            # Paletizar la pieza pequeña en la zona de trabajo
            current_offset = offsets[small_pieces]  # Seleccionar offset

            paletize_pose = PoseObject(
                x=central_pose.x + current_offset[0],
                y=central_pose.y + current_offset[1],
                z=central_pose.z,
                roll=central_pose.roll,
                pitch=central_pose.pitch,
                yaw=central_pose.yaw,
            )
            robot.move_pose(central_pose)
            robot.move_pose(paletize_pose)
            robot.release_with_tool()
            robot.move_pose(central_pose)  # Volver a la posición central después de soltar

            robot.move_joints(0.057, 0.098, -0.213, -0.075, -1.447, 0.06)
            small_pieces += 1

    # Detener el cronómetro
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Desactivar la cinta transportadora
    robot.unset_conveyor(conveyor_id)

    # Finalizar conexión con el robot
    robot.close_connection()

    print(f"Proceso completado: 3 piezas pequeñas colocadas y 3 piezas grandes desechadas.")
    print(f"Tiempo total transcurrido: {elapsed_time:.2f} segundos.")

    # Write to database
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO Robot (tiempo_inicio, tiempo_final, piezas_peque, piezas_grandes)
            VALUES (%s, %s, %s, %s)
        """, (start_time, end_time, small_pieces, large_pieces))
        connection.commit()
    except Exception as e:
        print(f"Error al escribir en la base de datos: {e}")
    finally:
        cursor.close()
        connection.close()

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
    if not init():
        print("Modo automático no puede iniciarse sin conexión al robot.")
        return None  # Indicate failure to start

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

# Function to get the elapsed time since automatic mode started
elapsed_time = 0
def get_elapsed_time():
    global elapsed_time
    if start_time:
        elapsed_time = time.time() - start_time
    return elapsed_time
