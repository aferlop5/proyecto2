"""PROYECTO RII 2
   Create the API
"""

from flask import Flask
from resourceFlaskAlchemy import robots
from flask_cors import CORS

db_user = 'root'
# Sin contraseña
db_password = ''

# Conexión usando el nombre del contenedor "mysql_robot"
MYSQL_URI = f"mysql+pymysql://{db_user}:{db_password}@mysql_robot:3306/niryodb"
# We link the database

def create_api():
    api = Flask(__name__)
    CORS(api)
    api.config['CORS_HEADERS']  = 'Content-Type'
    api.config["SQLALCHEMY_DATABASE_URI"] = MYSQL_URI
    api.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    api.register_blueprint(robots)

    return api
