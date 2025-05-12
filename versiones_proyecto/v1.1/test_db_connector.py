import mysql.connector

def test_connection():
    try:
        print("Conectando a MySQL...")
        con = mysql.connector.connect(
            user="root",
            host="172.17.0.2",  # Dirección IP del contenedor
            password=""  # Sin contraseña
        )
        print("Conexión exitosa.")
    except mysql.connector.Error as e:
        print("Error al conectar a MySQL:", e)
    finally:
        if 'con' in locals() and con.is_connected():
            con.close()
            print("Conexión cerrada.")

test_connection()