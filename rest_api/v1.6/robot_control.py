from pyniryo import *
import time
from datetime import datetime
import proxy

# Conexión con el robot
robot_ip = "158.42.132.223"  # IP del robot
robot = NiryoRobot(robot_ip)
robot.calibrate_auto()
robot.update_tool()

# Pines de sensores
DI5 = PinID.DI5
DI1 = PinID.DI1

# Inicializar cinta transportadora
conveyor_id = robot.set_conveyor()

# Posición inicial (joints y pose)
initial_joints = [-0.01, 0.61, -1.29, 0.07, -0.53, -0.2]
initial_pose = PoseObject(x=0.035, y=0.242, z=0.122, roll=-3.092, pitch=1.458, yaw=-1.413)
robot.move_joints(*initial_joints)

# Guardar posición inicial como string
posicion_inicial = f"Joints: {initial_joints}, Pose: ({initial_pose.x}, {initial_pose.y}, {initial_pose.z}, {initial_pose.roll}, {initial_pose.pitch}, {initial_pose.yaw})"

# Guardar inicio
tiempo_inicio = datetime.now().time()
start_timestamp = time.time()

# Iniciar registro
small_pieces = 0
large_pieces = 0
peque_tiempos = []
grande_tiempos = []
offsets = [
    (-0.075, -0.075),
    (0.075, -0.075),
    (-0.075, 0.075),
]

# Proceso
while small_pieces < 3 or large_pieces < 3:
    while robot.digital_read(DI5) == PinState.HIGH:
        robot.run_conveyor(conveyor_id, speed=100, direction=ConveyorDirection.FORWARD)
    robot.stop_conveyor(conveyor_id)
    now = datetime.now().time()

    if robot.digital_read(DI1) == PinState.LOW:
        start_time_piece = time.time()
        while time.time() - start_time_piece < 8:
            robot.run_conveyor(conveyor_id, speed=100, direction=ConveyorDirection.BACKWARD)
        robot.stop_conveyor(conveyor_id)
        grande_tiempos.append(now)
        proxy.registrar_pieza("grande", "desechada")
        large_pieces += 1
    else:
        robot.move_joints(0.057, 0.098, -0.213, -0.075, -1.447, 0.06)
        robot.move_joints(0.47, -0.66, -0.28, -0.01, -0.6, -0.16)
        robot.grasp_with_tool()
        robot.move_joints(0.99, -0.225, -0.513, -0.038, -0.632, -0.026)

        current_offset = offsets[small_pieces]
        paletize_pose = PoseObject(
            x=initial_pose.x + current_offset[0],
            y=initial_pose.y + current_offset[1],
            z=initial_pose.z,
            roll=initial_pose.roll,
            pitch=initial_pose.pitch,
            yaw=initial_pose.yaw,
        )

        robot.move_pose(initial_pose)
        robot.move_pose(paletize_pose)
        robot.release_with_tool()
        robot.move_pose(initial_pose)
        robot.move_joints(0.057, 0.098, -0.213, -0.075, -1.447, 0.06)

        peque_tiempos.append(now)
        proxy.registrar_pieza("pequeña", "paletizada")
        small_pieces += 1

robot.unset_conveyor(conveyor_id)
robot.close_connection()

tiempo_final = datetime.now().time()
elapsed = time.time() - start_timestamp

robot_id = proxy.guardar_datos_robot(
    robot_id=robot_ip,  # Usar la IP como ID
    tiempo_inicio=tiempo_inicio,
    tiempo_final=tiempo_final,
    paro_manual=False,
    min_total=int(elapsed // 60),
    seg_total=int(elapsed % 60),
    piezas_peque=small_pieces,
    piezas_grandes=large_pieces,
    tiempo_peque=len(peque_tiempos),
    tiempo_grande=len(grande_tiempos),
    posicion_inicial=posicion_inicial
)

proxy.guardar_sensor_abajo(robot_id, peque_tiempos)
proxy.guardar_sensor_arriba(robot_id, grande_tiempos)

print(f"Proceso terminado. ID sesión: {robot_id}")
