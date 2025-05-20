from control import get_sensor_states
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from functools import wraps
from control import (
    controlSensorDI1, controlSensorDI5, mover_cinta, parar_cinta,
    control_herramienta, mover_robot, controlar_pausa, automatico,
    modo_automatico, init, exitNiryo, robot
)
import mysql.connector
import uuid
import requests
import logging
import time
from threading import Thread
import os
from werkzeug.serving import run_simple

# Configuración de logging
logging.basicConfig(
    filename='robot_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Cache para almacenar estados temporales
cache = {
    'sensor_di1': None,
    'sensor_di5': None,
    'robot_position': None,
    'ventosa_state': None
}

def update_sensor_states():
    """Thread para actualizar estados de sensores en tiempo real"""
    while True:
        try:
            states = get_sensor_states()
            if states != cache['sensor_di1'] or states != cache['sensor_di5']:
                cache.update(states)
                socketio.emit('sensor_update', states)
            time.sleep(0.1)  # Actualizar cada 100ms
        except Exception as e:
            logger.error(f"Error actualizando estados de sensores: {e}")

# Iniciar thread de monitoreo
sensor_thread = Thread(target=update_sensor_states)
sensor_thread.daemon = True
sensor_thread.start()

def get_db_connection():
    return mysql.connector.connect(
        user="root",
        password="",
        host="localhost",
        database="robot_data"
    )

def time_to_string(time_obj):
    if time_obj:
        return str(time_obj)
    return None

# Función para verificar si un usuario está autenticado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_nick = request.headers.get('nick')
        user_password = request.headers.get('password')

        if not user_nick or not user_password:
            return {'message': 'Nick y password son requeridos'}, 401
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Usuario WHERE nick = %s AND password = %s", (user_nick, user_password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if not user:
            return {'message': 'Credenciales incorrectas'}, 401

        return f(*args, **kwargs)
    return decorated_function

class UsuarioResource(Resource):
    def get(self, user_id=None):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if user_id:
            cursor.execute("SELECT * FROM Usuario WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            cursor.close()
            connection.close()
            if not user:
                return {'message': 'Usuario no encontrado'}, 404
            return jsonify(user)
        else:
            nick = request.headers.get('nick')
            password = request.headers.get('password')

            if not nick or not password:
                return {'message': 'Nick y password son requeridos'}, 401

            cursor.execute("SELECT * FROM Usuario WHERE nick = %s AND password = %s", (nick, password))
            user = cursor.fetchone()
            cursor.close()
            connection.close()

            if not user:
                return {'message': 'Credenciales incorrectas'}, 401

            return jsonify(user)

    def post(self):
        data = request.get_json()
        nick = data.get('nick')
        password = data.get('password')

        if not nick or not password:
            return {'message': 'Nick y password son requeridos'}, 400

        user_id = uuid.uuid4().hex
        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO Usuario (id, nick, password) 
                VALUES (%s, %s, %s)
            """, (user_id, nick, password))
            connection.commit()
            return {'message': 'Usuario creado exitosamente', 'id': user_id}, 201
        except mysql.connector.Error as err:
            return {'message': f'Error al crear el usuario: {err}'}, 500
        finally:
            cursor.close()
            connection.close()

    def put(self, user_id):
        data = request.get_json()
        nick = data.get('nick')
        password = data.get('password')

        if not nick or not password:
            return {'message': 'Nick y password son requeridos'}, 400

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                UPDATE Usuario
                SET nick = %s, password = %s
                WHERE id = %s
            """, (nick, password, user_id))
            connection.commit()
            return {'message': 'Usuario actualizado exitosamente'}
        except mysql.connector.Error as err:
            return {'message': f'Error al actualizar el usuario: {err}'}, 500
        finally:
            cursor.close()
            connection.close()

    def delete(self, user_id):
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM Usuario WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            connection.close()
            return {'message': 'Usuario no encontrado'}, 404

        try:
            cursor.execute("DELETE FROM Usuario WHERE id = %s", (user_id,))
            connection.commit()
            return {'message': 'Usuario eliminado exitosamente'}
        except mysql.connector.Error as err:
            return {'message': f'Error al eliminar el usuario: {err}'}, 500
        finally:
            cursor.close()
            connection.close()

class VentosaResource(Resource):
    @login_required
    def get(self):
        con = get_db_connection()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Ventosa")
        ventosas = cur.fetchall()
        con.close()

        for ventosa in ventosas:
            ventosa["tiempo_agarre1"] = time_to_string(ventosa["tiempo_agarre1"])
            ventosa["tiempo_agarre2"] = time_to_string(ventosa["tiempo_agarre2"])
            ventosa["tiempo_agarre3"] = time_to_string(ventosa["tiempo_agarre3"])
            ventosa["tiempo_dejada1"] = time_to_string(ventosa["tiempo_dejada1"])
            ventosa["tiempo_dejada2"] = time_to_string(ventosa["tiempo_dejada2"])
            ventosa["tiempo_dejada3"] = time_to_string(ventosa["tiempo_dejada3"])

        return jsonify(ventosas)

    def post(self):
        data = request.get_json()

        required_fields = [
            'tiempo_agarre1', 'tiempo_agarre2', 'tiempo_agarre3',
            'tiempo_dejada1', 'tiempo_dejada2', 'tiempo_dejada3', 'usuario_id'
        ]
        if not all(field in data for field in required_fields):
            return {"message": "Faltan campos requeridos."}, 400

        usuario_id = data['usuario_id']
        ventosa_id = uuid.uuid4().hex

        con = get_db_connection()
        cur = con.cursor()

        try:
            cur.execute("""
                INSERT INTO Ventosa (
                    id, usuario_id, 
                    tiempo_agarre1, tiempo_agarre2, tiempo_agarre3,
                    tiempo_dejada1, tiempo_dejada2, tiempo_dejada3
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ventosa_id, usuario_id,
                str(data['tiempo_agarre1']),
                str(data['tiempo_agarre2']),
                str(data['tiempo_agarre3']),
                str(data['tiempo_dejada1']),
                str(data['tiempo_dejada2']),
                str(data['tiempo_dejada3'])
            ))

            con.commit()
            con.close()
            return {"id": ventosa_id, "message": "Ventosa creada correctamente"}, 201

        except Exception as e:
            con.close()
            return {"message": f"Error al crear Ventosa: {str(e)}"}, 500

class SensorDI5Resource(Resource):
    @login_required
    def get(self):
        con = get_db_connection()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Sensor_DI5")
        sensores = cur.fetchall()
        con.close()
        
        for sensor in sensores:
            for key in ['tiempo_deteccion_peque1', 'tiempo_deteccion_peque2', 'tiempo_deteccion_peque3']:
                if sensor[key]:
                    sensor[key] = str(sensor[key])
        
        return jsonify(sensores)

    def post(self):
        data = request.get_json()

        required_fields = ['tiempo_deteccion_peque1', 'tiempo_deteccion_peque2', 'tiempo_deteccion_peque3', 'usuario_id'
        ]
        if not all(field in data for field in required_fields):
            return {"message": "Faltan campos requeridos."}, 400

        usuario_id = data['usuario_id']
        sensor_id = uuid.uuid4().hex

        con = get_db_connection()
        cur = con.cursor()

        try:
            cur.execute("""
                INSERT INTO Sensor_DI5 (id, usuario_id, tiempo_deteccion_peque1, tiempo_deteccion_peque2, tiempo_deteccion_peque3)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                sensor_id,
                usuario_id,
                str(data['tiempo_deteccion_peque1']),
                str(data['tiempo_deteccion_peque2']),
                str(data['tiempo_deteccion_peque3'])
            ))

            con.commit()
            con.close()

            return {"id": sensor_id, "message": "Sensor DI5 creado correctamente"}, 201

        except Exception as e:
            con.close()
            return {"message": f"Error al crear sensor DI5: {str(e)}"}, 500

class SensorDI1Resource(Resource):
    @login_required
    def get(self):
        con = get_db_connection()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Sensor_DI1")
        sensores = cur.fetchall()
        con.close()
        
        for sensor in sensores:
            for key in ['tiempo_deteccion_grande1', 'tiempo_deteccion_grande2', 'tiempo_deteccion_grande3']:
                if sensor[key]:
                    sensor[key] = str(sensor[key])
        
        return jsonify(sensores)

    def post(self):
        data = request.get_json()

        required_fields = ['tiempo_deteccion_grande1', 'tiempo_deteccion_grande2', 'tiempo_deteccion_grande3', 'usuario_id']
        if not all(field in data for field in required_fields):
            return {"message": "Faltan campos requeridos."}, 400

        usuario_id = data['usuario_id']
        sensor_id = uuid.uuid4().hex

        con = get_db_connection()
        cur = con.cursor()

        try:
            cur.execute("""
                INSERT INTO Sensor_DI1 (id, usuario_id, tiempo_deteccion_grande1, tiempo_deteccion_grande2, tiempo_deteccion_grande3)
                VALUES (%s, %s, %s, %s, %s)
            """, (sensor_id, usuario_id, str(data['tiempo_deteccion_grande1']), str(data['tiempo_deteccion_grande2']), str(data['tiempo_deteccion_grande3'])))
            con.commit()
            con.close()

            return {"id": sensor_id, "message": "Sensor DI1 creado correctamente"}, 201

        except Exception as e:
            con.close()
            return {"message": f"Error al crear sensor DI1: {str(e)}"}, 500

# Modificar la función init() para manejar mejor el modo simulación
def init_robot():
    try:
        init()
        return True
    except Exception as e:
        logger.warning(f"Ejecutando en modo simulación. Error de conexión: {e}")
        return False

class RobotResource(Resource):
    def __init__(self):
        self.simulation_mode = not init_robot()

    @login_required
    def get(self, robot_id=None):
        con = get_db_connection()
        cur = con.cursor(dictionary=True)
        
        if robot_id:
            cur.execute("SELECT * FROM Robot WHERE id = %s", (robot_id,))
            robot = cur.fetchone()
            con.close()
            if robot:
                robot["tiempo_inicio"] = time_to_string(robot["tiempo_inicio"])
                robot["tiempo_final"] = time_to_string(robot["tiempo_final"])
                return jsonify(robot) 
            else:
                return {'message': 'Robot no encontrado'}, 404
        else:
            cur.execute("SELECT * FROM Robot")
            robots = cur.fetchall()
            con.close()
            
            for robot in robots:
                robot["tiempo_inicio"] = time_to_string(robot["tiempo_inicio"])
                robot["tiempo_final"] = time_to_string(robot["tiempo_final"])
            
            return jsonify(robots)

    def post(self):
        data = request.get_json()

        usuario_id = data['usuario_id']
        tiempo_inicio = data['tiempo_inicio']
        tiempo_final = data['tiempo_final']
        paro_manual = data['paro_manual']
        min_total = data['min_total']
        seg_total = data['seg_total']
        piezas_peque = data.get('piezas_peque', 0)
        piezas_grandes = data.get('piezas_grandes', 0)
        tiempo_peque = data.get('tiempo_peque', 0)
        tiempo_grande = data.get('tiempo_grande', 0)
        
        robot_id = uuid.uuid4().hex

        con = get_db_connection()
        cur = con.cursor()

        try:
            cur.execute("""
                INSERT INTO Robot (id, usuario_id, tiempo_inicio, tiempo_final, paro_manual, min_total, seg_total, piezas_peque, piezas_grandes, tiempo_peque, tiempo_grande)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (robot_id, usuario_id, tiempo_inicio, tiempo_final, paro_manual, min_total, seg_total, piezas_peque, piezas_grandes, tiempo_peque, tiempo_grande))
            con.commit()
            con.close()

            return {'message': 'Robot creado', 'id': robot_id}, 201
        except Exception as e:
            con.close()
            return {'message': str(e)}, 400

#PROXY

@app.route('/iniciar_conexion', methods=['POST'])
def iniciar_conexion():
    try:
        init()
        return jsonify({"mensaje": "Conexión iniciada correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cerrar_conexion', methods=['POST'])
def cerrar_conexion():
    try:
        exitNiryo()
        return jsonify({"mensaje": "Conexión cerrada correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/control_sensor_DI1', methods=['POST'])
def controlar_sensor_DI1():
    estado_sensor_DI1 = controlSensorDI1()
    return jsonify({"estado_sensor_DI1": estado_sensor_DI1}), 200

@app.route('/control_sensor_DI5', methods=['POST'])
def controlar_sensor_DI5():
    estado_sensor_DI5 = controlSensorDI5()
    return jsonify({"estado_sensor_DI5": estado_sensor_DI5}), 200

@app.route('/cinta/run', methods=['POST'])
def run_cinta():
    data = request.get_json()
    direccion = data.get('direccion')
    velocidad = data.get('velocidad')

    try:
        logger.info(f"Iniciando cinta: dirección={direccion}, velocidad={velocidad}")
        resultado = mover_cinta(velocidad, direccion)
        if resultado:
            socketio.emit('cinta_update', {'estado': 'running', 'direccion': direccion, 'velocidad': velocidad})
            return jsonify({
                "status": "success",
                "estado": "RUN",
                "direccion": direccion,
                "velocidad": velocidad
            }), 200
        else:
            error_msg = "Error: Robot o cinta no inicializados."
            socketio.emit('error_state', {'component': 'cinta', 'error': error_msg})
            return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_msg = f"Error iniciando cinta: {str(e)}"
        logger.error(error_msg)
        socketio.emit('error_state', {'component': 'cinta', 'error': error_msg})
        return jsonify({"error": error_msg}), 500

@app.route('/cinta/stop', methods=['POST'])
def stop_cinta():
    parar_cinta()
    return jsonify({
        "estado": "STOP"
    }), 200
    
@app.route('/control_ventosa', methods=['POST'])
def controlar_herramienta():
    data = request.get_json()
    accion = data.get('accion')

    try:
        logger.info(f"Controlando ventosa: {accion}")
        resultado = control_herramienta(accion)
        if resultado:
            cache['ventosa_state'] = accion
            socketio.emit('ventosa_update', {'estado': accion})
            return jsonify({
                "status": "success",
                "accion": accion,
            }), 200
        else:
            error_msg = "Error: Robot o ventosa no inicializados."
            socketio.emit('error_state', {'component': 'ventosa', 'error': error_msg})
            return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_msg = f"Error controlando ventosa: {str(e)}"
        logger.error(error_msg)
        socketio.emit('error_state', {'component': 'ventosa', 'error': error_msg})
        return jsonify({"error": error_msg}), 500

@app.route('/control_robot', methods=['POST'])
def controlar_robot():
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')
    z = data.get('z')
    roll = data.get('roll')
    pitch = data.get('pitch')
    yaw = data.get('yaw')

    try:
        logger.info(f"Moviendo robot a posición: x={x}, y={y}, z={z}, roll={roll}, pitch={pitch}, yaw={yaw}")
        resultado = mover_robot(x, y, z, roll, pitch, yaw)
        if resultado:
            cache['robot_position'] = {'x': x, 'y': y, 'z': z, 'roll': roll, 'pitch': pitch, 'yaw': yaw}
            socketio.emit('robot_position_update', cache['robot_position'])
            return jsonify({
                "status": "success",
                "message": "Robot movido correctamente",
                "position": cache['robot_position']
            }), 200
        else:
            error_msg = "Error: Robot no inicializado."
            socketio.emit('error_state', {'component': 'robot', 'error': error_msg})
            return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_msg = f"Error moviendo robot: {str(e)}"
        logger.error(error_msg)
        socketio.emit('error_state', {'component': 'robot', 'error': error_msg})
        return jsonify({"error": error_msg}), 500

@app.route('/marchaparo', methods=['POST'])
def marcha_paro():
    data = request.get_json()
    accion = data.get('accion')
    controlar_pausa(accion)
    return jsonify({"accion": accion}), 200

@app.route('/auto', methods=['POST'])
def auto():
    data = request.get_json()
    user_id = data.get('usuario_id')

    try:
        logger.info(f"Iniciando modo automático para usuario: {user_id}")
        ventosa, sensordi1, sensordi5, robot_data = automatico()

        for dic in [ventosa, sensordi1, sensordi5, robot_data]:
            dic['usuario_id'] = user_id

        responses = {
            "ventosa": requests.post('http://localhost:5000/ventosa', json=ventosa).json(),
            "sensor_di1": requests.post('http://localhost:5000/sensor_di1', json=sensordi1).json(),
            "sensor_di5": requests.post('http://localhost:5000/sensor_di5', json=sensordi5).json(),
            "robot": requests.post('http://localhost:5000/robot', json=robot_data).json(),
        }

        logger.info(f"Modo automático completado: {responses}")
        socketio.emit('auto_complete', responses)
        return jsonify({'message': 'Datos registrados correctamente', 'data': responses}), 200

    except Exception as e:
        logger.error(f"Error en modo automático: {str(e)}")
        return jsonify({'error': str(e)}), 500

class SensorStatus(Resource):
    def get(self):
        return get_sensor_states()

@app.route('/start_automatic_mode', methods=['POST'])
def start_automatic_mode():
    try:
        controlar_pausa('m')  # Resume the automatic mode
        return jsonify({"message": "Automatic mode started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stop_automatic_mode', methods=['POST'])
def stop_automatic_mode():
    try:
        controlar_pausa('p')  # Pause the automatic mode
        return jsonify({"message": "Automatic mode stopped"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

api.add_resource(UsuarioResource, '/usuario', '/usuario/<string:user_id>')
api.add_resource(VentosaResource, '/ventosa', '/ventosa/<string:ventosa_id>')
api.add_resource(SensorDI5Resource, '/sensor_di5', '/sensor_di5/<string:sensor_id>')
api.add_resource(SensorDI1Resource, '/sensor_di1', '/sensor_di1/<string:sensor_id>')
api.add_resource(RobotResource, '/robot', '/robot/<string:robot_id>')
api.add_resource(SensorStatus, "/sensores/estado")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  # Cambiar a puerto 5000
