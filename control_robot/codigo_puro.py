from pyniryo import *
import time  

robot = NiryoRobot("158.42.132.223")
robot.calibrate_auto()
robot.update_tool()

DI5 = PinID.DI5
DI1 = PinID.DI1

# Inicializar la cinta transportadora
conveyor_id = robot.set_conveyor()

# Pose inicial del robot
initial_pose = [-0.01, 0.61, -1.29, 0.07, -0.53, -0.2]
robot.move_joints(*initial_pose)

small_pieces = 0
large_pieces = 0

# PosiciÃ³n central de la zona de paletizado
central_pose = PoseObject(x=0.035, y=0.242, z=0.122, roll=-3.092, pitch=1.458, yaw=-1.413)

# Offsets(en metros)
offsets = [
    (-0.075, -0.075),  # CÃ­rculo inferior izquierdo
    (0.075, -0.075),   # CÃ­rculo inferior derecho
    (-0.075, 0.075),   # CÃ­rculo superior izquierdo
]

# Iniciar el cronÃ³metro
start_time = time.time()

while small_pieces < 3 or large_pieces < 3:
    # Avanzar la cinta hasta detectar una pieza con DI5
    while robot.digital_read(DI5) == PinState.HIGH:
        robot.run_conveyor(conveyor_id, speed=100, direction=ConveyorDirection.FORWARD)
    robot.stop_conveyor(conveyor_id)

    # Analizar la pieza detectada con DI1
    if robot.digital_read(DI1) == PinState.LOW:
        # Retroceder la cinta durante 5 segundos para desechar la pieza grande
        start_time_piece = time.time()
        while time.time() - start_time_piece < 8:
            robot.run_conveyor(conveyor_id, speed=100, direction=ConveyorDirection.BACKWARD)
        robot.stop_conveyor(conveyor_id)
        large_pieces += 1
    else:
        # Paletizar la pieza pequeÃ±a
        robot.move_joints(0.057, 0.098, -0.213, -0.075, -1.447, 0.06)
        robot.move_joints(0.47, -0.66, -0.28, -0.01, -0.6, -0.16)
        robot.grasp_with_tool()
        robot.move_joints(0.99, -0.225, -0.513, -0.038, -0.632, -0.026)

        # Paletizar la pieza pequeÃ±a en la zona de trabajo
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
        robot.move_pose(central_pose)  # Volver a la posiciÃ³n central despuÃ©s de soltar

        robot.move_joints(0.057, 0.098, -0.213, -0.075, -1.447, 0.06)
        small_pieces += 1

# Detener el cronÃ³metro
end_time = time.time()
elapsed_time = end_time - start_time

# Desactivar la cinta transportadora
robot.unset_conveyor(conveyor_id)

# Finalizar conexiÃ³n con el robot
robot.close_connection()

print(f"Proceso completado: 3 piezas pequeÃ±as colocadas y 3 piezas grandes desechadas.")
print(f"Tiempo total transcurrido: {elapsed_time:.2f} segundos.")
