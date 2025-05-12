from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_cors import CORS
from functools import wraps
from ejemploNiryo import controlSensorDI1, controlSensorDI5, mover_cinta, parar_cinta, control_herramienta, mover_robot, controlar_pausa, automatico, modo_automatico, init, exitNiryo, robot
import mysql.connector
import uuid
import requests

ID_FILE = "id.txt"

def get_next_id():
    with open(ID_FILE, "r") as f:
        current_id = f.read().strip().lower()

    next_id = decrement_id(current_id)

    with open(ID_FILE, "w") as f:
        f.write(next_id)

    return current_id

def decrement_id(id_str):
    id_chars = list(id_str)
    for i in range(len(id_chars)-1, -1, -1):
        if id_chars[i] > 'a':
            id_chars[i] = chr(ord(id_chars[i]) - 1)
            break
        else:
            id_chars[i] = 'z'
    return ''.join(id_chars)

app = Flask(__name__)
api = Api(app)
CORS(app)

def get_db_connection():
    return mysql.connector.connect(
        user="root",
        password="root",
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
        # Obtenemos los datos del usuario desde el header (en un escenario real sería más seguro usar JWT o similar)
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
            cursor.execute("SELECT * FROM Usuario")
            usuarios = cursor.fetchall()
            cursor.close()
            connection.close()
            return jsonify(usuarios)

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
    # Obtener todos los registros de la tabla Ventosa
    @login_required
    def get(self):
        con = get_db_connection()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Ventosa")
        ventosas = cur.fetchall()
        con.close()

        # Convertir los valores de tiempo a cadenas antes de enviarlos
        for ventosa in ventosas:
            ventosa["tiempo_agarre1"] = time_to_string(ventosa["tiempo_agarre1"])
            ventosa["tiempo_agarre2"] = time_to_string(ventosa["tiempo_agarre2"])
            ventosa["tiempo_agarre3"] = time_to_string(ventosa["tiempo_agarre3"])
            ventosa["tiempo_dejada1"] = time_to_string(ventosa["tiempo_dejada1"])
            ventosa["tiempo_dejada2"] = time_to_string(ventosa["tiempo_dejada2"])
            ventosa["tiempo_dejada3"] = time_to_string(ventosa["tiempo_dejada3"])

        return jsonify(ventosas)

    # Crear un nuevo registro en la tabla Ventosa
    # @login_required
    def post(self):
        data = request.get_json()

        # Validación de campos requeridos
        required_fields = [
            'tiempo_agarre1', 'tiempo_agarre2', 'tiempo_agarre3',
            'tiempo_dejada1', 'tiempo_dejada2', 'tiempo_dejada3', 'usuario_id'
        ]
        if not all(field in data for field in required_fields):
            return {"message": "Faltan campos requeridos."}, 400

        # Obtener usuario_id desde los datos
        usuario_id = data['usuario_id']

        # Generación de un ID único para la ventosa
        ventosa_id = get_next_id()

        con = get_db_connection()
        cur = con.cursor()

        try:
            # Inserción en la tabla Ventosa
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

    # Obtener un registro específico de Ventosa por ID
    @login_required
    def get_ventosa(self, ventosa_id):
        con = get_db_connection()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Ventosa WHERE id = %s", (ventosa_id,))
        ventosa = cur.fetchone()
        con.close()
        if ventosa:
            # Convertir los valores de tiempo a cadenas antes de enviarlos
            ventosa["tiempo_agarre1"] = time_to_string(ventosa["tiempo_agarre1"])
            ventosa["tiempo_agarre2"] = time_to_string(ventosa["tiempo_agarre2"])
            ventosa["tiempo_agarre3"] = time_to_string(ventosa["tiempo_agarre3"])
            ventosa["tiempo_dejada1"] = time_to_string(ventosa["tiempo_dejada1"])
            ventosa["tiempo_dejada2"] = time_to_string(ventosa["tiempo_dejada2"])
            ventosa["tiempo_dejada3"] = time_to_string(ventosa["tiempo_dejada3"])

            return jsonify(ventosa)
        else:
            return {"message": "Ventosa no encontrada."}, 404

    # Actualizar un registro específico de Ventosa por ID
    @login_required
    def put(self, ventosa_id):
        data = request.get_json()

        required_fields = ['tiempo_agarre1', 'tiempo_agarre2', 'tiempo_agarre3', 
                           'tiempo_dejada1', 'tiempo_dejada2', 'tiempo_dejada3']
        
        if not all(field in data for field in required_fields):
            return {"message": "Faltan campos requeridos."}, 400
        
        con = get_db_connection()
        cur = con.cursor()

        try:
            cur.execute(""" 
                UPDATE Ventosa
                SET tiempo_agarre1 = %s, tiempo_agarre2 = %s, tiempo_agarre3 = %s,
                    tiempo_dejada1 = %s, tiempo_dejada2 = %s, tiempo_dejada3 = %s
                WHERE id = %s
            """, (data['tiempo_agarre1'], data['tiempo_agarre2'], data['tiempo_agarre3'],
                  data['tiempo_dejada1'], data['tiempo_dejada2'], data['tiempo_dejada3'], ventosa_id))
            con.commit()
            con.close()
            return {"message": "Ventosa actualizada correctamente."}, 200
        except Exception as e:
            con.close()
            return {"message": f"Error al actualizar ventosa: {str(e)}"}, 500

    # Eliminar un registro específico de Ventosa por ID
    @login_required
    def delete(self, ventosa_id):
        con = get_db_connection()
        cur = con.cursor()

        try:
            cur.execute("DELETE FROM Ventosa WHERE id = %s", (ventosa_id,))
            con.commit()
            con.close()
            return {"message": "Ventosa eliminada correctamente."}, 200
        except Exception as e:
            con.close()
            return {"message": f"Error al eliminar ventosa: {str(e)}"}, 500

class SensorDI5Resource(Resource):
    # Obtener todos los registros de la tabla Sensor_DI5
    @login_required
    def get(self):
        con = get_db_connection()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Sensor_DI5")
        sensores = cur.fetchall()
        con.close()
        
        # Convertimos los tiempos de la base de datos a string antes de devolverlos
        for sensor in sensores:
            for key in ['tiempo_deteccion_peque1', 'tiempo_deteccion_peque2', 'tiempo_deteccion_peque3']:
                if sensor[key]:
                    sensor[key] = str(sensor[key])
        
        return jsonify(sensores)

    # Crear un nuevo registro en la tabla Sensor_DI5
    # @login_required
    def post(self):
        data = request.get_json()

        # Validación de campos
        required_fields = ['tiempo_deteccion_peque1', 'tiempo_deteccion_peque2', 'tiempo_deteccion_peque3', 'usuario_id']
        if not all(field in data for field in required_fields):
            return {"message": "Faltan campos requeridos."}, 400

        # Obtener usuario_id desde los datos
        usuario_id = data['usuario_id']

        # Generación de un ID único para el sensor DI5
        sensor_id = get_next_id()

        con = get_db_connection()
        cur = con.cursor()

        try:
            # Inserción en la tabla Sensor_DI5
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


    # Obtener un registro específico de Sensor_DI5 por ID
    @login_required
    def get_sensor(self, sensor_id):
        con = get_db_connection()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Sensor_DI5 WHERE id = %s", (sensor_id,))
        sensor = cur.fetchone()
        con.close()
        
        if sensor:
            # Convertimos los tiempos a string antes de devolverlos
            for key in ['tiempo_deteccion_peque1', 'tiempo_deteccion_peque2', 'tiempo_deteccion_peque3']:
                if sensor[key]:
                    sensor[key] = str(sensor[key])
            return jsonify(sensor)
        else:
            return {"message": "Sensor DI5 no encontrado."}, 404

    # Actualizar un registro específico de Sensor_DI5 por ID
    @login_required
    def put(self, sensor_id):
        data = request.get_json()

        required_fields = ['tiempo_deteccion_peque1', 'tiempo_deteccion_peque2', 'tiempo_deteccion_peque3']
        
        if not all(field in data for field in required_fields):
            return {"message": "Faltan campos requeridos."}, 400
        
        con = get_db_connection()
        cur = con.cursor()

        try:
            # Convertimos los tiempos a string antes de actualizarlos
            cur.execute("""
                UPDATE Sensor_DI5
                SET tiempo_deteccion_peque1 = %s, tiempo_deteccion_peque2 = %s, tiempo_deteccion_peque3 = %s
                WHERE id = %s
            """, (str(data['tiempo_deteccion_peque1']), 
                  str(data['tiempo_deteccion_peque2']), 
                  str(data['tiempo_deteccion_peque3']), 
                  sensor_id))
            con.commit()
            con.close()
            return {"message": "Sensor DI5 actualizado correctamente."}, 200
        except Exception as e:
            con.close()
            return {"message": f"Error al actualizar sensor DI5: {str(e)}"}, 500

    # Eliminar un registro específico de Sensor_DI5 por ID
    @login_required
    def delete(self, sensor_id):
        con = get_db_connection()
        cur = con.cursor()

        try:
            cur.execute("DELETE FROM Sensor_DI5 WHERE id = %s", (sensor_id,))
            con.commit()
            con.close()
            return {"message": "Sensor DI5 eliminado correctamente."}, 200
        except Exception as e:
            con.close()
            return {"message": f"Error al eliminar sensor DI5: {str(e)}"}, 500

class SensorDI1Resource(Resource):
    @login_required
    def get(self):
        con = get_db_connection()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Sensor_DI1")
        sensores = cur.fetchall()
        con.close()
        
        # Convertimos los tiempos de la base de datos a string antes de devolverlos
        for sensor in sensores:
            for key in ['tiempo_deteccion_grande1', 'tiempo_deteccion_grande2', 'tiempo_deteccion_grande3']:
                if sensor[key]:
                    sensor[key] = str(sensor[key])
        
        return jsonify(sensores)

    # @login_required
    def post(self):
        data = request.get_json()

        # Comprobamos que los campos requeridos estén presentes
        required_fields = ['tiempo_deteccion_grande1', 'tiempo_deteccion_grande2', 'tiempo_deteccion_grande3', 'usuario_id']
        if not all(field in data for field in required_fields):
            return {"message": "Faltan campos requeridos."}, 400

        # Extraemos los datos
        usuario_id = data['usuario_id']
        tiempo_deteccion_grande1 = str(data['tiempo_deteccion_grande1'])
        tiempo_deteccion_grande2 = str(data['tiempo_deteccion_grande2'])
        tiempo_deteccion_grande3 = str(data['tiempo_deteccion_grande3'])

        # Generación de un ID único para el sensor
        sensor_id = get_next_id()

        # Conectar a la base de datos
        con = get_db_connection()
        cur = con.cursor()

        try:
            # Inserción de datos en la tabla Sensor_DI1
            cur.execute("""
                INSERT INTO Sensor_DI1 (id, usuario_id, tiempo_deteccion_grande1, tiempo_deteccion_grande2, tiempo_deteccion_grande3)
                VALUES (%s, %s, %s, %s, %s)
            """, (sensor_id, usuario_id, tiempo_deteccion_grande1, tiempo_deteccion_grande2, tiempo_deteccion_grande3))

            con.commit()
            con.close()

            return {"id": sensor_id, "message": "Sensor DI1 creado correctamente"}, 201

        except Exception as e:
            con.close()
            return {"message": f"Error al crear sensor DI1: {str(e)}"}, 500



    @login_required
    def get_sensor(self, sensor_id):
        con = get_db_connection()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Sensor_DI1 WHERE id = %s", (sensor_id,))
        sensor = cur.fetchone()
        con.close()
        
        if sensor:
            # Convertimos los tiempos a string antes de devolverlos
            for key in ['tiempo_deteccion_grande1', 'tiempo_deteccion_grande2', 'tiempo_deteccion_grande3']:
                if sensor[key]:
                    sensor[key] = str(sensor[key])
            return jsonify(sensor)
        else:
            return {"message": "Sensor DI1 no encontrado."}, 404

    @login_required
    def put(self, sensor_id):
        data = request.get_json()

        required_fields = ['tiempo_deteccion_grande1', 'tiempo_deteccion_grande2', 'tiempo_deteccion_grande3']
        
        if not all(field in data for field in required_fields):
            return {"message": "Faltan campos requeridos."}, 400
        
        con = get_db_connection()
        cur = con.cursor()

        try:
            # Convertimos los tiempos a string antes de actualizarlos
            cur.execute("""
                UPDATE Sensor_DI1
                SET tiempo_deteccion_grande1 = %s, tiempo_deteccion_grande2 = %s, tiempo_deteccion_grande3 = %s
                WHERE id = %s
            """, (str(data['tiempo_deteccion_grande1']), 
                  str(data['tiempo_deteccion_grande2']), 
                  str(data['tiempo_deteccion_grande3']), 
                  sensor_id))
            con.commit()
            con.close()
            return {"message": "Sensor DI1 actualizado correctamente."}, 200
        except Exception as e:
            con.close()
            return {"message": f"Error al actualizar sensor DI1: {str(e)}"}, 500

    @login_required
    def delete(self, sensor_id):
        con = get_db_connection()
        cur = con.cursor()

        try:
            cur.execute("DELETE FROM Sensor_DI1 WHERE id = %s", (sensor_id,))
            con.commit()
            con.close()
            return {"message": "Sensor DI1 eliminado correctamente."}, 200
        except Exception as e:
            con.close()
            return {"message": f"Error al eliminar sensor DI1: {str(e)}"}, 500

class RobotResource(Resource):
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

    # @login_required
    def post(self):
        # Obtener datos de la solicitud
        data = request.get_json()

        # Verificar que el usuario_id esté presente en los datos
        print(f"Datos recibidos: {data}")

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
        
        # Generación de un ID único para el robot
        robot_id = get_next_id()

        # Conectar a la base de datos
        con = get_db_connection()
        cur = con.cursor()

        try:
            # Inserción en la tabla Robot, asegurándose de incluir el usuario_id
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

    @login_required
    def put(self, robot_id):
        data = request.get_json()

        tiempo_inicio = data['tiempo_inicio']
        tiempo_final = data['tiempo_final']
        paro_manual = data['paro_manual']
        min_total = data['min_total']
        seg_total = data['seg_total']
        piezas_peque = data.get('piezas_peque', 0)
        piezas_grandes = data.get('piezas_grandes', 0)
        tiempo_peque = data.get('tiempo_peque', 0)
        tiempo_grande = data.get('tiempo_grande', 0)
        
        con = get_db_connection()
        cur = con.cursor()
        
        try:
            cur.execute("""
                UPDATE Robot
                SET tiempo_inicio = %s, tiempo_final = %s, paro_manual = %s, min_total = %s, seg_total = %s, piezas_peque = %s, piezas_grandes = %s, tiempo_peque = %s, tiempo_grande = %s
                WHERE id = %s
            """, (tiempo_inicio, tiempo_final, paro_manual, min_total, seg_total, piezas_peque, piezas_grandes, tiempo_peque, tiempo_grande, robot_id))
            con.commit()
            con.close()
            return {'message': 'Robot actualizado'}, 200
        except Exception as e:
            con.close()
            return {'message': str(e)}, 400

    @login_required
    def delete(self, robot_id):
        con = get_db_connection()
        cur = con.cursor()

        try:
            cur.execute("DELETE FROM Robot WHERE id = %s", (robot_id,))
            con.commit()
            con.close()
            return {'message': 'Robot eliminado'}, 200
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
    direccion = data.get('direccion')  # 'forward' o 'backward'
    velocidad = data.get('velocidad')  # valor numérico (0-100)

    # Ensure the robot is initialized
    if robot is None:
        init()

    mover_cinta(velocidad, direccion)

    return jsonify({
        "estado": "RUN",
        "direccion": direccion,
        "velocidad": velocidad
    }), 200

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

    control_herramienta(accion)

    return jsonify({
        "accion": accion,
    }), 200

@app.route('/control_robot', methods=['POST'])
def controlar_robot():
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')
    z = data.get('z')
    roll = data.get('roll')
    pitch = data.get('pitch')
    yaw = data.get('yaw')

    mover_robot(x, y, z, roll, pitch, yaw)

    return jsonify({
        "x": x,
        "y": y,
        "z": z,
        "roll": roll,
        "pitch": pitch,
        "yaw": yaw
    }), 200

# Ruta para controlar pausa ("p") o marcha ("m")
@app.route('/marchaparo', methods=['POST'])
def marcha_paro():
    data = request.get_json()
    accion = data.get('accion')
    controlar_pausa(accion)
    return jsonify({"accion": accion}), 200

# Ruta principal para modo automático
@app.route('/auto', methods=['POST'])
def auto():
    data = request.get_json()
    user_id = data.get('usuario_id')

    # Ejecutar modo automático (en segundo plano) y obtener resultados
    ventosa, sensordi1, sensordi5, robot = automatico()

    # Añadir usuario_id a cada diccionario
    for dic in [ventosa, sensordi1, sensordi5, robot]:
        dic['usuario_id'] = user_id

    # Enviar POST a cada una de las rutas
    try:
        responses = {
            "ventosa": requests.post('http://localhost:5000/ventosa', json=ventosa).json(),
            "sensor_di1": requests.post('http://localhost:5000/sensor_di1', json=sensordi1).json(),
            "sensor_di5": requests.post('http://localhost:5000/sensor_di5', json=sensordi5).json(),
            "robot": requests.post('http://localhost:5000/robot', json=robot).json(),
        }

        print("Datos registrados:", responses)
        return jsonify({'message': 'Datos registrados correctamente'}), 200

    except requests.exceptions.RequestException as e:
        print('Error al registrar los datos:', e)
        return jsonify({'message': 'Error al registrar los datos'}), 500


api.add_resource(UsuarioResource, '/usuario', '/usuario/<string:user_id>')
api.add_resource(VentosaResource, '/ventosa', '/ventosa/<string:ventosa_id>')
api.add_resource(SensorDI5Resource, '/sensor_di5', '/sensor_di5/<string:sensor_id>')
api.add_resource(SensorDI1Resource, '/sensor_di1', '/sensor_di1/<string:sensor_id>')
api.add_resource(RobotResource, '/robot', '/robot/<string:robot_id>')

app.run(debug=True)
