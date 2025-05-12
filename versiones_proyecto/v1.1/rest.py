
from flask import Flask
from flask_restful import Api, Resource, reqparse
import mysql.connector

app = Flask(__name__)
api = Api(app)

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "robot_data"
}

parser = reqparse.RequestParser()
parser.add_argument("tipo", type=str, required=True, help="Tipo de pieza requerido")
parser.add_argument("estado", type=str, required=True, help="Estado de pieza requerido")

class Operaciones(Resource):
    def get(self):
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM operaciones")
        operaciones = cursor.fetchall()
        conn.close()
        return operaciones, 200

    def post(self):
        args = parser.parse_args()
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO operaciones (tipo, estado) VALUES (%s, %s)", (args['tipo'], args['estado']))
        conn.commit()
        conn.close()
        return {"message": "Operación registrada correctamente"}, 201

class Estadisticas(Resource):
    def get(self):
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT estado, COUNT(*) FROM operaciones GROUP BY estado")
        stats = cursor.fetchall()
        conn.close()
        return [{"estado": s[0], "cantidad": s[1]} for s in stats], 200

api.add_resource(Operaciones, "/operaciones")
api.add_resource(Estadisticas, "/estadisticas")

if __name__ == "__main__":
    app.run(debug=True)
