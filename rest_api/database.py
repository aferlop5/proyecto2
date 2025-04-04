import mysql.connector

import mysql.connector

def conectar():
    """Crea y retorna una conexión a la base de datos."""
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="robot_data"
        )
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    conn = conectar()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operaciones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tipo VARCHAR(50) NOT NULL,
                    estado VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuracion (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    parametro VARCHAR(100) NOT NULL,
                    valor VARCHAR(100) NOT NULL
                )
            ''')

        conn.commit()
        print("Base de datos y tablas creadas correctamente.")
    except mysql.connector.Error as err:
        print(f"Error al inicializar la base de datos: {err}")
    finally:
        conn.close()

def registrar_operacion(tipo, estado):
    """Registra una nueva operación en la base de datos."""
    conn = conectar()
    if not conn:
        return
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO operaciones (tipo, estado) VALUES (%s, %s)", (tipo, estado))
        conn.commit()
        print("Operación registrada con éxito.")
    except mysql.connector.Error as err:
        print(f"Error al registrar la operación: {err}")
    finally:
        conn.close()

def obtener_operaciones():
    """Obtiene todas las operaciones registradas."""
    conn = conectar()
    if not conn:
        return []

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM operaciones")
            return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error al obtener las operaciones: {err}")
        return []
    finally:
        conn.close()

# Inicializar la base de datos al ejecutar este script
if __name__ == "__main__":
    init_db()
