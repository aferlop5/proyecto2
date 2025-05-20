from pyniryo import NiryoRobot, PinID, PinState, ConveyorDirection, PoseObject
import time
import threading
import random  # Asegúrate de importar random si no está ya importado

# Variables globales
robot = None
sensorDI5 = None
sensorDI1 = None
conveyor_id = None
is_initialized = False
start_time = None  # Para calcular el tiempo transcurrido en modo automático
pausa_event = threading.Event()
pausa_event.set()

def init():
    """Inicializa la conexión con el robot."""
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
    """Cierra la conexión con el robot."""
    global robot, conveyor_id, is_initialized
    if robot is not None:
        robot.unset_conveyor(conveyor_id)
        robot.close_connection()
    is_initialized = False

def _pin_to_str(state):
    """Convierte el estado de un pin a una cadena legible."""
    if isinstance(state, PinState):
        return "HIGH" if state == PinState.HIGH else "LOW"
    return "HIGH" if state else "LOW"

def get_sensor_states():
    """Obtiene el estado de los sensores DI1 y DI5."""
    global robot, sensorDI1, sensorDI5
    try:
        if robot is None:
            return {"sensor_di1": "OFFLINE", "sensor_di5": "OFFLINE"}
        di1 = _pin_to_str(robot.digital_read(sensorDI1))
        di5 = _pin_to_str(robot.digital_read(sensorDI5))
        return {"sensor_di1": di1, "sensor_di5": di5}
    except Exception as e:
        print(f"Error leyendo sensores: {e}")
        return {"sensor_di1": "ERROR", "sensor_di5": "ERROR"}

def mover_cinta(velocidad, direccion):
    """Mueve la cinta transportadora en la dirección y velocidad especificadas."""
    global robot, conveyor_id
    if robot is None:
        print("Error: Robot no inicializado.")
        return False

    try:
        if direccion == 'forward':
            robot.run_conveyor(conveyor_id, speed=velocidad, direction=ConveyorDirection.FORWARD)
        elif direccion == 'backward':
            robot.run_conveyor(conveyor_id, speed=velocidad, direction=ConveyorDirection.BACKWARD)
        else:
            print("Error: Dirección inválida. Use 'forward' o 'backward'.")
        return True
    except Exception as e:
        print(f"Error al mover la cinta: {e}")
        return False

def parar_cinta():
    """Detiene la cinta transportadora."""
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
    """Activa o desactiva la herramienta del robot."""
    if robot is None:
        print("Error: Robot no inicializado.")
        return False

    try:
        if accion == 'activar':
            robot.activate_tool()
        else:
            robot.deactivate_tool()
        return True
    except Exception as e:
        print(f"Error controlando herramienta: {e}")
        return False

def controlar_pausa(orden):
    """Controla la pausa del modo automático."""
    if orden == "p":
        pausa_event.clear()
        print("Pausado.")
    elif orden == "m":
        pausa_event.set()
        print("Reanudado.")

def modo_automatico():
    """Ejecuta el modo automático."""
    global robot, sensorDI5, sensorDI1, conveyor_id, start_time

    # Verificar si el robot está inicializado
    if robot is None:
        print("Modo automático no puede iniciarse: Robot no inicializado.")
        return False

    small_pieces = 0
    large_pieces = 0
    central_pose = PoseObject(x=0.035, y=0.242, z=0.122, roll=-3.092, pitch=1.458, yaw=-1.413)
    offsets = [(-0.075, -0.075), (0.075, -0.075), (-0.075, 0.075)]
    start_time = time.time()  # Inicia el contador solo si el robot está conectado

    while small_pieces < 3 or large_pieces < 3:
        while not pausa_event.is_set():
            time.sleep(0.1)

        while robot.digital_read(sensorDI5) == PinState.HIGH:
            robot.run_conveyor(conveyor_id, speed=100, direction=ConveyorDirection.FORWARD)
        robot.stop_conveyor(conveyor_id)

        if robot.digital_read(sensorDI1) == PinState.LOW:
            start_time_piece = time.time()
            while time.time() - start_time_piece < 8:
                robot.run_conveyor(conveyor_id, speed=100, direction=ConveyorDirection.BACKWARD)
            robot.stop_conveyor(conveyor_id)
            large_pieces += 1
        else:
            robot.move_joints(0.057, 0.098, -0.213, -0.075, -1.447, 0.06)
            robot.move_joints(0.47, -0.66, -0.28, -0.01, -0.6, -0.16)
            robot.grasp_with_tool()
            robot.move_joints(0.99, -0.225, -0.513, -0.038, -0.632, -0.026)

            current_offset = offsets[small_pieces]
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
            robot.move_pose(central_pose)
            robot.move_joints(0.057, 0.098, -0.213, -0.075, -1.447, 0.06)
            small_pieces += 1

    end_time = time.time()
    elapsed_time = end_time - start_time
    robot.unset_conveyor(conveyor_id)
    robot.close_connection()
    print(f"Proceso completado: 3 piezas pequeñas colocadas y 3 piezas grandes desechadas.")
    print(f"Tiempo total transcurrido: {elapsed_time:.2f} segundos.")

    # Crear los diccionarios para devolver
    ventosa_dict = {
        "tiempo_agarre1": "valor1",
        "tiempo_agarre2": "valor2",
        "tiempo_agarre3": "valor3",
        "tiempo_dejada1": "valor4",
        "tiempo_dejada2": "valor5",
        "tiempo_dejada3": "valor6",
    }

    di1_dict = {
        "tiempo_deteccion_grande1": "valor1",
        "tiempo_deteccion_grande2": "valor2",
        "tiempo_deteccion_grande3": "valor3",
    }

    di5_dict = {
        "tiempo_deteccion_peque1": "valor1",
        "tiempo_deteccion_peque2": "valor2",
        "tiempo_deteccion_peque3": "valor3",
    }

    robot_dict = {
        "tiempo_inicio": start_time,
        "tiempo_final": end_time,
        "paro_manual": False,
        "min_total": int(elapsed_time // 60),
        "seg_total": int(elapsed_time % 60),
        "piezas_peque": small_pieces,
        "piezas_grandes": large_pieces,
        "tiempo_peque": "valor_peque",
        "tiempo_grande": "valor_grande",
    }

    return ventosa_dict, di1_dict, di5_dict, robot_dict

def get_elapsed_time():
    """Devuelve el tiempo transcurrido desde el inicio del modo automático."""
    global start_time
    if start_time:
        return time.time() - start_time
    return 0

def controlSensorDI1():
    """Controla el estado del sensor DI1."""
    global robot, sensorDI1
    if robot is None:
        # Simulación: retorna un valor aleatorio
        return "HIGH" if random.choice([True, False]) else "LOW"
    return _pin_to_str(robot.digital_read(sensorDI1))

def controlSensorDI5():
    """Controla el estado del sensor DI5."""
    global robot, sensorDI5
    if robot is None:
        # Simulación: retorna un valor aleatorio
        return "HIGH" if random.choice([True, False]) else "LOW"
    return _pin_to_str(robot.digital_read(sensorDI5))

def mover_robot(x, y, z, roll, pitch, yaw):
    """Mueve el robot a la posición especificada usando juntas."""
    global robot
    if robot is None:
        print("Error: Robot no inicializado.")
        return False

    try:
        # Cambiar a move_joints para trabajar con juntas
        robot.move_joints(x, y, z, roll, pitch, yaw)
        return True
    except Exception as e:
        print(f"Error al mover el robot: {e}")
        return False

def automatico():
    """Ejecuta el modo automático."""
    try:
        return modo_automatico()  # Llama a la función existente `modo_automatico`
    except Exception as e:
        print(f"Error en modo automático: {e}")
        return False
