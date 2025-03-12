import time
from pyniryo import NiryoRobot


estado = "START"  


frecuencia = 1  
X, Y, Z = 0, 0, 0  
X_obj, Y_obj, Z_obj = 0, 0, 0  

def leer_ficheros():
    global frecuencia, X, Y, Z, X_obj, Y_obj, Z_obj

    
    try:
        with open("frecuencia.txt", "r") as f:
            frecuencia = float(f.read().strip())  
            print(f"Frecuencia de captura: {frecuencia} Hz")
    except FileNotFoundError:
        print("Error: frecuencia.txt no encontrado.")
        return False
    except Exception as e:
        print(f"Error al leer frecuencia.txt: {e}")
        return False

    
    try:
        with open("palet.txt", "r") as f:
            palet = f.read().strip().split(',')
            
            X, Y, Z = [float(x.strip()) for x in palet]
            print(f"Formación del palet: X={X}, Y={Y}, Z={Z}")
    except FileNotFoundError:
        print("Error: palet.txt no encontrado.")
        return False  
    except Exception as e:
        print(f"Error al leer palet.txt: {e}")
        return False

    
    try:
        with open("objetos.txt", "r") as f:
           
            objetos = f.read().strip().replace('\n', ',').split(',')
            
            X_obj, Y_obj, Z_obj = [float(x.strip()) for x in objetos]
            print(f"Objetos en el palet: X={X_obj}, Y={Y_obj}, Z={Z_obj}")
    except FileNotFoundError:
        print("Error: objetos.txt no encontrado.")
        return False  
    except Exception as e:
        print(f"Error al leer objetos.txt: {e}")
        return False

    return True  


def guardar_posiciones(posiciones):
    try:
        with open("posiciones_robot.txt", "w") as f:
            for posicion in posiciones:
                f.write(f"{posicion[0]}, {posicion[1]}, {posicion[2]}, {posicion[3]}, {posicion[4]}, {posicion[5]}\n")
            print("Posiciones guardadas correctamente en posiciones_robot.txt")
    except Exception as e:
        print(f"Error al guardar las posiciones: {e}")

def mover_robot():
    
    robot = NiryoRobot("localhost")
    robot.calibrate_auto() 

    
    posiciones = []
    
    
    punto_a = [0.2, -0.3, 0.1, 0.0, 0.5, -0.8]  
    robot.move_joints(*punto_a)
    posiciones.append(punto_a) 

    
    punto_b = [0.3, -0.2, 0.15, 0.0, 0.4, -0.7]  
    robot.move_joints(*punto_b)
    posiciones.append(punto_b)  

    
    guardar_posiciones(posiciones)

    
    robot.close_connection()

def maquina():
    global estado
    if estado == "START":
        print("Robot en funcionamiento...")
        
        if leer_ficheros():
            print("Todos los archivos leídos correctamente.")
            mover_robot()  
        else:
            print("Hubo un error al leer los archivos. El programa terminará.")
    elif estado == "STOP":
        print("Robot apagado...")

def controlar_robot():
    global estado
    comando = input("Introduce el comando (START o STOP): ").strip().upper()  
    if comando == "START":
        estado = "START"
        print("Robot encendido. El robot está en funcionamiento.")
        maquina()  
    elif comando == "STOP":
        estado = "STOP"
        print("Robot apagado. El robot no está en funcionamiento.")
    else:
        print("Comando no reconocido. Usa 'START' o 'STOP'.")

if __name__ == "__main__":
    controlar_robot()  

