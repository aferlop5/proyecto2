from pyniryo import *

# Conexión al robot
robot = NiryoRobot("158.42.132.223")

# Activar conexión con la cinta transportadora
conveyor_id = robot.set_conveyor()

try:
    while True:
        accion = int(input("Introduce 1 para arrancar la cinta, 0 para detenerla, o 9 para salir: "))

        if accion == 1:
            print("Arrancando la cinta transportadora...")
            robot.run_conveyor(conveyor_id)
        elif accion == 0:
            print("Deteniendo la cinta transportadora...")
            robot.stop_conveyor(conveyor_id)
        elif accion == 9:
            print("Saliendo del programa...")
            break
        else:
            print("Número no válido. Introduce 0, 1 o 9 para salir.")

finally:
    # Desactivar la cinta y cerrar la conexión antes de salir
    robot.unset_conveyor(conveyor_id)
    robot.close_connection()