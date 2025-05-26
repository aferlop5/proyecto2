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
ROBOT_IP = "158.42.132.223"
# Estado global de velocidad de la cinta (0-100)
velocidad_cinta = 100


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

@robots.route("/robots/<int:id>/modo/auto", methods=["POST"])
def set_modo_auto(id):
    robot = Robots.query.filter_by(robot_id=id).first()
    if not robot:
        return jsonify({"error": "Robot no encontrado"}), 404
    robot.robot_desc = "auto"
    db.session.commit()
    return jsonify({"message": "Modo cambiado a AUTOMÁTICO"})

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
    if porcentaje not in [25, 50, 75, 100]:
        return jsonify({"error": "Velocidad no válida"}), 400
    velocidad_cinta = porcentaje
    return jsonify({"message": f"Velocidad de cinta establecida a {porcentaje}%"})

@robots.route("/robot/belt_forward", methods=["POST"])
def belt_forward():
    if not modo_manual_requerido():
        return jsonify({"error": "Modo MANUAL requerido"}), 403
    robot = NiryoRobot(ROBOT_IP)
    conveyor_id = robot.set_conveyor()
    robot.run_conveyor(conveyor_id, speed=velocidad_cinta, direction=ConveyorDirection.FORWARD)
    return jsonify({"message": "Cinta moviéndose hacia adelante"})


@robots.route("/robot/belt_backward", methods=["POST"])
def belt_backward():
    if not modo_manual_requerido():
        return jsonify({"error": "Modo MANUAL requerido"}), 403
    robot = NiryoRobot(ROBOT_IP)
    conveyor_id = robot.set_conveyor()
    robot.run_conveyor(conveyor_id, speed=velocidad_cinta, direction=ConveyorDirection.BACKWARD)
    return jsonify({"message": "Cinta moviéndose hacia atrás"})


@robots.route("/robot/belt_stop", methods=["POST"])
def belt_stop():
    if not modo_manual_requerido():
        return jsonify({"error": "Modo MANUAL requerido"}), 403

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
    try:
        robot = NiryoRobot(ROBOT_IP)
        d1 = robot.digital_read(1)
        d5 = robot.digital_read(5)
        robot.close_connection()

        d1_val = d1[0] if isinstance(d1, tuple) else d1
        d5_val = d5[0] if isinstance(d5, tuple) else d5

        if d1_val == 0 and d5_val == 0:
            estado = "pieza alta"
        elif d1_val == 0:
            estado = "pieza baja"
        else:
            estado = "sin pieza"

        return jsonify({
            "D1": d1_val,
            "D5": d5_val,
            "estado": estado
        })

    except Exception as e:
        print(f"[ERROR SENSOR] {e}")
        return jsonify({
            "D1": 1,
            "D5": 1,
            "estado": "error"
        }), 200

        






