
from flask import Flask, request, jsonify
from flask_restful import Api, Resource, reqparse
import proxy

app = Flask(__name__)
api = Api(app)

# Parser para registrar piezas
parser_pieza = reqparse.RequestParser()
parser_pieza.add_argument("tipo", type=str, required=True, help="Tipo de pieza requerido (pequeña o grande)")
parser_pieza.add_argument("estado", type=str, required=True, help="Estado de la pieza requerido (paletizada o desechada)")

# Parser para guardar datos del robot
parser_robot = reqparse.RequestParser()
parser_robot.add_argument("robot_id", type=str, required=True, help="ID del robot requerido")
parser_robot.add_argument("tiempo_inicio", type=str, required=True, help="Tiempo de inicio requerido")
parser_robot.add_argument("tiempo_final", type=str, required=True, help="Tiempo final requerido")
parser_robot.add_argument("paro_manual", type=bool, required=True, help="Paro manual requerido")
parser_robot.add_argument("min_total", type=int, required=True, help="Minutos totales requeridos")
parser_robot.add_argument("seg_total", type=int, required=True, help="Segundos totales requeridos")
parser_robot.add_argument("piezas_peque", type=int, required=True, help="Cantidad de piezas pequeñas")
parser_robot.add_argument("piezas_grandes", type=int, required=True, help="Cantidad de piezas grandes")
parser_robot.add_argument("tiempo_peque", type=int, required=True, help="Tiempo total de piezas pequeñas")
parser_robot.add_argument("tiempo_grande", type=int, required=True, help="Tiempo total de piezas grandes")
parser_robot.add_argument("posicion_inicial", type=str, required=True, help="Posición inicial requerida")

# Parser para guardar tiempos de sensores
parser_sensor = reqparse.RequestParser()
parser_sensor.add_argument("id_robot", type=str, required=True, help="ID del robot requerido")
parser_sensor.add_argument("tiempos", type=list, location='json', required=True, help="Lista de tiempos requerida")

class RegistrarPieza(Resource):
    def post(self):
        args = parser_pieza.parse_args()
        proxy.registrar_pieza(args['tipo'], args['estado'])
        return {"message": "Pieza registrada correctamente"}, 201

class GuardarDatosRobot(Resource):
    def post(self):
        args = parser_robot.parse_args()
        robot_id = proxy.guardar_datos_robot(
            robot_id=args['robot_id'],
            tiempo_inicio=args['tiempo_inicio'],
            tiempo_final=args['tiempo_final'],
            paro_manual=args['paro_manual'],
            min_total=args['min_total'],
            seg_total=args['seg_total'],
            piezas_peque=args['piezas_peque'],
            piezas_grandes=args['piezas_grandes'],
            tiempo_peque=args['tiempo_peque'],
            tiempo_grande=args['tiempo_grande'],
            posicion_inicial=args['posicion_inicial']
        )
        if robot_id:
            return {"message": "Datos del robot guardados correctamente", "robot_id": robot_id}, 201
        else:
            return {"message": "Error al guardar los datos del robot"}, 500

class GuardarSensorAbajo(Resource):
    def post(self):
        args = parser_sensor.parse_args()
        proxy.guardar_sensor_abajo(args['id_robot'], args['tiempos'])
        return {"message": "Tiempos del sensor DI5 guardados correctamente"}, 201

class GuardarSensorArriba(Resource):
    def post(self):
        args = parser_sensor.parse_args()
        proxy.guardar_sensor_arriba(args['id_robot'], args['tiempos'])
        return {"message": "Tiempos del sensor DI1 guardados correctamente"}, 201

class Estadisticas(Resource):
    def get(self):
        stats = proxy.obtener_estadisticas()
        return [{"estado": s[0], "cantidad": s[1]} for s in stats], 200

# Añadir recursos a la API
api.add_resource(RegistrarPieza, "/registrar_pieza")
api.add_resource(GuardarDatosRobot, "/guardar_datos_robot")
api.add_resource(GuardarSensorAbajo, "/guardar_sensor_abajo")
api.add_resource(GuardarSensorArriba, "/guardar_sensor_arriba")
api.add_resource(Estadisticas, "/estadisticas")

if __name__ == "__main__":
    app.run(debug=True)