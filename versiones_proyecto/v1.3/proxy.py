import mysql.connector
from datetime import datetime
import uuid

# Guardar pieza como antes
def registrar_pieza(tipo, estado):
    conn = mysql.connector.connect(host="localhost", user="root", password="", database="robot_data")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO operaciones (tipo, estado) VALUES (%s, %s)", (tipo, estado))
    conn.commit()
    conn.close()

# Guardar datos de la tabla robot (posición inicial incluida)
def guardar_datos_robot(robot_id, tiempo_inicio, tiempo_final, paro_manual, min_total, seg_total, piezas_peque, piezas_grandes, tiempo_peque, tiempo_grande, posicion_inicial):
    """
    Guarda los datos del robot en la base de datos.
    """
    conn = mysql.connector.connect(host="localhost", user="root", password="", database="robot_data")
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO robot (
                    id, tiempo_inicio, tiempo_final, paro_manual, min_total, seg_total,
                    piezas_peque, piezas_grandes, tiempo_peque, tiempo_grande, posicion_inicial
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                robot_id, tiempo_inicio, tiempo_final, paro_manual, min_total, seg_total,
                piezas_peque, piezas_grandes, tiempo_peque, tiempo_grande, posicion_inicial
            ))
        conn.commit()
        return robot_id
    except Exception as e:
        print(f"Error al guardar datos del robot: {e}")
        return None
    finally:
        conn.close()

# Sensor abajo (DI5) detección de pequeñas
def guardar_sensor_abajo(id_robot, tiempos):
    conn = mysql.connector.connect(host="localhost", user="root", password="", database="robot_data")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sensor_abajo (id, tiempo_deteccion_peque1, tiempo_deteccion_peque2, tiempo_deteccion_peque3)
        VALUES (%s, %s, %s, %s)
    """, (id_robot, *tiempos))
    conn.commit()
    conn.close()

# Sensor arriba (DI1) detección de grandes
def guardar_sensor_arriba(id_robot, tiempos):
    conn = mysql.connector.connect(host="localhost", user="root", password="", database="robot_data")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sensor_arriba (id, tiempo_deteccion_grande1, tiempo_deteccion_grande2, tiempo_deteccion_grande3)
        VALUES (%s, %s, %s, %s)
    """, (id_robot, *tiempos))
    conn.commit()
    conn.close()

# Obtener estadísticas como antes
def obtener_estadisticas():
    conn = mysql.connector.connect(host="localhost", user="root", password="", database="robot_data")
    cursor = conn.cursor()
    cursor.execute("SELECT estado, COUNT(*) FROM operaciones GROUP BY estado")
    estadisticas = cursor.fetchall()
    conn.close()
    return estadisticas

if __name__ == "__main__":
    print("Proxy de base de datos MySQL listo.")
