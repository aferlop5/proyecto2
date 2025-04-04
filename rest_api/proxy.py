import mysql.connector

def registrar_pieza(tipo, estado):
    """ Registra una pieza en la base de datos """
    conn = mysql.connector.connect(host="localhost", user="root", password="", database="robot_data")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO operaciones (tipo, estado) VALUES (%s, %s)", (tipo, estado))
    conn.commit()
    conn.close()

def obtener_estadisticas():
    """ Obtiene estadísticas de piezas procesadas """
    conn = mysql.connector.connect(host="localhost", user="root", password="", database="robot_data")
    cursor = conn.cursor()
    cursor.execute("SELECT estado, COUNT(*) FROM operaciones GROUP BY estado")
    estadisticas = cursor.fetchall()
    conn.close()
    return estadisticas

if __name__ == "__main__":
    print("Proxy de base de datos MySQL listo.")
