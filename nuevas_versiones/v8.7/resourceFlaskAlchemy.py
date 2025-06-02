"""PROYECTO RII 2
   Resource Models and database
"""

from flask import Blueprint, jsonify, request, Response, url_for
from sqlalchemy.exc import IntegrityError
from modelsFlaskAlchemy import db, Robots
from flask import abort
import xmltodict
#import status
import time

# Control físico
from pyniryo import NiryoRobot, ConveyorDirection

# IP del robot real
ROBOT_IP = "158.42.132.221"
# Estado global de velocidad de la cinta (0-100)
velocidad_cinta = 100
belt_status = "apagada"  # Estado de la cinta
gripper_status = "abierta"  # Estado de la pinza
current_pose = {}  # Nuevo: posición actual del robot
auto_counters = {
    "small": 0,
    "large": 0
}


# Creates the Flask blueprint
robots = Blueprint("robots", __name__)

@robots.route("/api/robots", methods=["GET"])
def all_robots():
    pattern = request.args.get("pattern", default="")
    all_robots = Robots.query.filter(Robots.robot_name.contains(pattern)).all()
    end = request.args.get("end", default=100, type=int)
    start = request.args.get("start", default=0, type=int)
    all_robots = all_robots[start:(start + end)]

    if request.content_type == "application/xml":    
        xml_data = "".join(map(Robots.to_xml, all_robots))
        xml_data = f"<Robots> {xml_data} </Robots>"
        response = Response(xml_data, mimetype="application/xml")
        return response
    else:
        json_data = list(map(Robots.to_json, all_robots))
        return jsonify(json_data)

@robots.route("/api/robots/<int:id>", methods=["GET"], endpoint="get_robot")
def get_robot(id: int):
    robot = Robots.query.filter(Robots.robot_id == id).first()
    if robot is None:
        abort(status.HTTP_404_NOT_FOUND, message=f"Robot {id} does not exists")

    if request.content_type == "application/xml":    
        return robot.to_xml()
    else:
        return robot.to_json()

@robots.route("/robots/<int:id>/modo/manual", methods=["POST"])
def set_modo_manual(id):
    robot = Robots.query.filter_by(robot_id=id).first()
    if not robot:
        return jsonify({"error": "Robot no encontrado"}), 404
    robot.robot_desc = "manual"
    db.session.commit()
    return jsonify({"message": "Modo cambiado a MANUAL"})

# Variable global para pausar el modo automático
pause_auto_mode = False

def wait_if_paused(robot=None, conveyor_id=None):
    """Espera mientras el modo automático esté en pausa.
       Si se recibe robot y conveyor_id, se detiene la cinta."""
    global pause_auto_mode
    while pause_auto_mode:
        if robot is not None and conveyor_id is not None:
            robot.stop_conveyor(conveyor_id)
        time.sleep(0.5)

@robots.route("/robot/pause_auto", methods=["POST"])
def pause_auto():
    global pause_auto_mode
    pause_auto_mode = True
    return jsonify({"message": "Modo automático en pausa"})

@robots.route("/robot/resume_auto", methods=["POST"])
def resume_auto():
    global pause_auto_mode
    pause_auto_mode = False
    return jsonify({"message": "Modo automático reanudado"})

@robots.route("/robots/<int:id>/modo/auto", methods=["POST"])
def set_modo_auto(id):
    global belt_status, gripper_status, pause_auto_mode  # Uso de variables globales
    robot_record = Robots.query.filter_by(robot_id=id).first()
    if not robot_record:
        return jsonify({"error": "Robot no encontrado"}), 404

    # Actualizar el estado en la base de datos a "auto"
    robot_record.robot_desc = "auto"
    db.session.commit()

    try:
        from pyniryo import (
            NiryoRobot,
            ConveyorDirection,
            PinID,
            PinState,
            PoseObject
        )

        # Conectar y calibrar el robot
        robot = NiryoRobot(ROBOT_IP)
        robot.calibrate_auto()
        robot.update_tool()

        DI5 = PinID.DI5
        DI1 = PinID.DI1

        # Inicializar la cinta transportadora y mover a la posición inicial
        conveyor_id = robot.set_conveyor()
        belt_status = "apagada"
        initial_pose = [-0.01, 0.61, -1.29, 0.07, -0.53, -0.2]
        move_joints_and_update(robot, *initial_pose)

        small_pieces = 0
        large_pieces = 0
        auto_counters["small"] = 0
        auto_counters["large"] = 0

        central_pose = PoseObject(x=0.035, y=0.242, z=0.122, roll=-3.092, pitch=1.458, yaw=-1.413)
        offsets = [
            (-0.075, -0.075),  # Círculo inferior izquierdo
            (0.075, -0.075),   # Círculo inferior derecho
            (-0.075, 0.075)    # Círculo superior izquierdo
        ]

        start_time = time.time()

        while small_pieces < 3 or large_pieces < 3:
            # Espera si está en pausa
            wait_if_paused(robot, conveyor_id)

            # Avanzar la cinta hasta detectar la pieza (DI5 en HIGH)
            while robot.digital_read(DI5) == PinState.HIGH:
                wait_if_paused(robot, conveyor_id)
                belt_status = "en marcha"
                robot.run_conveyor(conveyor_id, speed=100, direction=ConveyorDirection.FORWARD)
            robot.stop_conveyor(conveyor_id)
            belt_status = "apagada"

            # Discriminar el tipo de pieza según DI1
            if robot.digital_read(DI1) == PinState.LOW:
                start_time_piece = time.time()
                # Retroceder la cinta durante 8 segundos para desechar pieza grande
                while time.time() - start_time_piece < 8:
                    wait_if_paused(robot, conveyor_id)
                    belt_status = "en marcha"
                    robot.run_conveyor(conveyor_id, speed=100, direction=ConveyorDirection.BACKWARD)
                robot.stop_conveyor(conveyor_id)
                belt_status = "apagada"
                large_pieces += 1
                auto_counters["large"] = large_pieces
            else:
                # Ejecución de rutina pick and place para pieza pequeña
                wait_if_paused()
                move_joints_and_update(robot, 0.057, 0.098, -0.213, -0.075, -1.447, 0.06)
                wait_if_paused()
                move_joints_and_update(robot, 0.47, -0.66, -0.28, -0.01, -0.6, -0.16)
                robot.grasp_with_tool()
                gripper_status = "cerrada"
                wait_if_paused()
                move_joints_and_update(robot, 0.99, -0.225, -0.513, -0.038, -0.632, -0.026)

                if small_pieces < len(offsets):
                    current_offset = offsets[small_pieces]
                else:
                    current_offset = (0, 0)

                paletize_pose = PoseObject(
                    x=central_pose.x + current_offset[0],
                    y=central_pose.y + current_offset[1],
                    z=central_pose.z,
                    roll=central_pose.roll,
                    pitch=central_pose.pitch,
                    yaw=central_pose.yaw,
                )
                wait_if_paused()
                move_pose_and_update(robot, central_pose)
                wait_if_paused()
                move_pose_and_update(robot, paletize_pose)
                robot.release_with_tool()
                gripper_status = "abierta"
                wait_if_paused()
                move_pose_and_update(robot, central_pose)
                wait_if_paused()
                move_joints_and_update(robot, 0.057, 0.098, -0.213, -0.075, -1.447, 0.06)
                small_pieces += 1
                auto_counters["small"] = small_pieces

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Finalización: detener la cinta y cerrar conexión
        robot.unset_conveyor(conveyor_id)
        belt_status = "apagada"
        robot.close_connection()

        return jsonify({
            "message": f"Modo automático ejecutado. {small_pieces} piezas pequeñas paletizadas y {large_pieces} piezas grandes desechadas en {elapsed_time:.2f} segundos. Estado actualizado a 'auto' en la DB.",
            "elapsed_time": f"{elapsed_time:.2f}"
        })

    except Exception as e:
        print(f"[ERROR AUTO] {e}")
        abort(500, description=f"Error en modo automático: {str(e)}")

# ======== CONTROL FÍSICO ========

def modo_manual_requerido():
    robot = Robots.query.filter_by(robot_id=1).first()
    if robot is None or robot.robot_desc != "manual":
        return False
    return True

@robots.route("/robot/grip_open", methods=["POST"])
def grip_open():
    if not modo_manual_requerido():
        return jsonify({"error": "Modo MANUAL requerido"}), 403
    try:
        print("[DEBUG] Conectando con el robot Niryo...")
        robot = NiryoRobot(ROBOT_IP)

        print("[DEBUG] Actualizando herramienta...")
        robot.update_tool()

        tool = robot.get_current_tool_id()
        print(f"[DEBUG] Tool ID detectado: {tool}")
        if tool == -1:
            print("[ERROR] ¡No se ha detectado ninguna herramienta en el robot!")
            abort(status.HTTP_500_INTERNAL_SERVER_ERROR, message="No se ha detectado ninguna herramienta conectada al robot.")

        time.sleep(0.5)
        print("[DEBUG] Abriendo pinza...")
        robot.release_with_tool()
        robot.close_connection()
        return jsonify({"message": "Pinza abierta correctamente"})

    except Exception as e:
        print(f"[ERROR] {e}")
        abort(status.HTTP_500_INTERNAL_SERVER_ERROR, message="Error con el robot Niryo.")

@robots.route("/robot/grip_close", methods=["POST"])
def grip_close():
    if not modo_manual_requerido():
        return jsonify({"error": "Modo MANUAL requerido"}), 403
    try:
        print("[DEBUG] Conectando con el robot Niryo...")
        robot = NiryoRobot(ROBOT_IP)

        print("[DEBUG] Actualizando herramienta...")
        robot.update_tool()

        tool = robot.get_current_tool_id()
        print(f"[DEBUG] Tool ID detectado: {tool}")
        if tool == -1:
            print("[ERROR] ¡No se ha detectado ninguna herramienta en el robot!")
            abort(status.HTTP_500_INTERNAL_SERVER_ERROR, message="No se ha detectado ninguna herramienta conectada al robot.")

        time.sleep(0.5)
        print("[DEBUG] Cerrando pinza...")
        robot.grasp_with_tool()
        robot.close_connection()
        return jsonify({"message": "Pinza cerrada correctamente"})

    except Exception as e:
        print(f"[ERROR] {e}")
        abort(status.HTTP_500_INTERNAL_SERVER_ERROR, message="Error con el robot Niryo.")
        
@robots.route("/robot/belt_speed/<int:porcentaje>", methods=["POST"])
def set_belt_speed(porcentaje):
    global velocidad_cinta
    # En la v1 no se requiere el modo manual para ajustar la velocidad
    if porcentaje not in [25, 50, 75, 100]:
        return jsonify({"error": "Velocidad no válida"}), 400
    velocidad_cinta = porcentaje
    return jsonify({"message": f"Velocidad de cinta establecida a {porcentaje}%"})

@robots.route("/robot/belt_forward", methods=["POST"])
def belt_forward():
    # Se elimina la verificación de modo manual, comportamiento similar a v1
    robot = NiryoRobot(ROBOT_IP)
    conveyor_id = robot.set_conveyor()
    robot.run_conveyor(conveyor_id, speed=velocidad_cinta, direction=ConveyorDirection.FORWARD)
    return jsonify({"message": "Cinta moviéndose hacia adelante"})


@robots.route("/robot/belt_backward", methods=["POST"])
def belt_backward():
    # Se elimina la verificación de modo manual, comportamiento similar a v1
    robot = NiryoRobot(ROBOT_IP)
    conveyor_id = robot.set_conveyor()
    robot.run_conveyor(conveyor_id, speed=velocidad_cinta, direction=ConveyorDirection.BACKWARD)
    return jsonify({"message": "Cinta moviéndose hacia atrás"})


@robots.route("/robot/belt_stop", methods=["POST"])
def belt_stop():
    # Se elimina la verificación de modo manual, comportamiento similar a v1
    try:
        robot = NiryoRobot(ROBOT_IP)
        conveyor_id = robot.set_conveyor()
        robot.stop_conveyor(conveyor_id)
        robot.unset_conveyor(conveyor_id)
        robot.close_connection()
        return jsonify({"message": "Cinta detenida"})
    except Exception as e:
        print(f"[ERROR PARO CINTA] {e}")
        return jsonify({"error": "No se pudo detener la cinta"}), 500



@robots.route("/robot/sensors", methods=["GET"])
def leer_sensores():
    robot = None
    try:
        # Importar los identificadores y estados de pines
        from pyniryo import PinID, PinState
        robot = NiryoRobot(ROBOT_IP)
        # Leer los pines DI5 y DI1
        estado_DI5 = robot.digital_read(PinID.DI5)
        estado_DI1 = robot.digital_read(PinID.DI1)

        # Interpretar el estado leído
        result_DI5 = "ALTO" if estado_DI5 == PinState.HIGH else "BAJO"
        result_DI1 = "ALTO" if estado_DI1 == PinState.HIGH else "BAJO"

        return jsonify({
            "DI5": result_DI5,
            "DI1": result_DI1
        })

    except Exception as e:
        print(f"[ERROR SENSOR] {e}")
        return jsonify({
            "DI5": "error",
            "DI1": "error"
        }), 200

    finally:
        if robot is not None:
            try:
                robot.close_connection()
            except Exception as err:
                print(f"[ERROR] al cerrar conexión: {err}")

@robots.route("/robot/move", methods=["POST"])
def move_robot():
    try:
        data = request.get_json()
        if not data or "joints" not in data:
            return jsonify({"error": "No se proporcionaron las articulaciones"}), 400

        joints_str = data["joints"]
        joints = [float(valor.strip()) for valor in joints_str.split(',')]
        if len(joints) != 6:
            return jsonify({"error": "Se deben proporcionar 6 valores"}), 400

        robot = NiryoRobot(ROBOT_IP)
        robot.update_tool()
        print(f"[DEBUG] Moviendo robot a la posición: {joints}")
        move_joints_and_update(robot, *joints)
        robot.close_connection()
        return jsonify({"message": f"Robot movido a la posición {joints}"}), 200

    except Exception as e:
        print(f"[ERROR MOVE ROBOT] {e}")
        return jsonify({"error": f"Error al mover el robot: {str(e)}"}), 500

# Nuevo endpoint para obtener los contadores en tiempo real
@robots.route("/robot/counters", methods=["GET"])
def get_counters():
    return jsonify({
        "small": auto_counters["small"],
        "large": auto_counters["large"],
        "belt": belt_status,      # Estado de la cinta
        "gripper": gripper_status,  # Estado de la pinza
        "pose": current_pose       # Posición actual del robot
    })

def move_joints_and_update(robot, *joints):
    global current_pose
    robot.move_joints(*joints)
    # Actualiza la pose con los valores de las articulaciones.
    current_pose = {"joints": joints}

def move_pose_and_update(robot, pose):
    global current_pose
    robot.move_pose(pose)
    current_pose = {
        "x": pose.x,
        "y": pose.y,
        "z": pose.z,
        "roll": pose.roll,
        "pitch": pose.pitch,
        "yaw": pose.yaw
    }








