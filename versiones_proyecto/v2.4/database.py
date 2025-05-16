import mysql.connector

def conectar(crear_db=False):
    """Crea y retorna una conexión a la base de datos."""
    try:
        if crear_db:
            # Conexión sin especificar la base de datos para crearla si no existe
            return mysql.connector.connect(
                host="localhost",  # Dirección IP del contenedor
                user="root",
                password=""  # Sin contraseña
            )
        else:
            # Conexión directa a la base de datos
            return mysql.connector.connect(
                host="localhost",  # Dirección IP del contenedor
                user="root",
                password="",  # Sin contraseña
                database="robot_data"
            )
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    # Primero, conecta sin especificar la base de datos para crearla si no existe
    conn = conectar(crear_db=True)
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS robot_data")
            print("Base de datos 'robot_data' creada o ya existía.")
    except mysql.connector.Error as err:
        print(f"Error al crear la base de datos: {err}")
    finally:
        conn.close()

    # Ahora conecta directamente a la base de datos para crear las tablas
    conn = conectar()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            # Tabla Usuario
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Usuario (
                    id CHAR(32) PRIMARY KEY,
                    nick VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(100) NOT NULL
                )
            ''')
            print("Tabla Usuario creada.")

            # Tabla Robot
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Robot (
                    id CHAR(32) PRIMARY KEY,
                    tiempo_inicio TIME NOT NULL,
                    tiempo_final TIME NOT NULL,
                    paro_manual BOOLEAN,
                    min_total INT NOT NULL,
                    seg_total INT NOT NULL,
                    piezas_peque INT DEFAULT 0,
                    piezas_grandes INT DEFAULT 0,
                    tiempo_peque INT DEFAULT 0,
                    tiempo_grande INT DEFAULT 0,
                    posicion_inicial TEXT DEFAULT NULL
                )
            ''')
            print("Tabla Robot creada.")

            # Tabla Sensor Abajo (DI5)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Sensor_DI5 (
                    id CHAR(32) PRIMARY KEY,
                    tiempo_deteccion_peque1 TIME NOT NULL,
                    tiempo_deteccion_peque2 TIME NOT NULL,
                    tiempo_deteccion_peque3 TIME NOT NULL
                )
            ''')
            print("Tabla Sensor_DI5 creada.")

            # Tabla Sensor Arriba (DI1)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Sensor_DI1 (
                    id CHAR(32) PRIMARY KEY,
                    tiempo_deteccion_grande1 TIME NOT NULL,
                    tiempo_deteccion_grande2 TIME NOT NULL,
                    tiempo_deteccion_grande3 TIME NOT NULL
                )
            ''')
            print("Tabla Sensor_DI1 creada.")

            # Tabla Ventosa
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Ventosa (
                    id CHAR(32) PRIMARY KEY,
                    tiempo_agarre1 TIME NOT NULL,
                    tiempo_agarre2 TIME NOT NULL,
                    tiempo_agarre3 TIME NOT NULL,
                    tiempo_dejada1 TIME NOT NULL,
                    tiempo_dejada2 TIME NOT NULL,
                    tiempo_dejada3 TIME NOT NULL
                )
            ''')
            print("Tabla Ventosa creada.")

            # Tabla Posiciones Robot
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posiciones_robot (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    x FLOAT,
                    y FLOAT,
                    z FLOAT,
                    roll FLOAT,
                    pitch FLOAT,
                    yaw FLOAT,
                    connected BOOLEAN NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("Tabla posiciones_robot creada.")

        conn.commit()
        print("Base de datos y tablas creadas correctamente.")
    except mysql.connector.Error as err:
        print(f"Error al inicializar la base de datos: {err}")
    finally:
        conn.close()

# Inicializar la base de datos al ejecutar este script
if __name__ == "__main__":
    init_db()
