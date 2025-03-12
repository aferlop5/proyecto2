import threading
import queue
import time
import os

# Variable global que mantiene el estado actual de la máquina: "START" o "STOP".
machine_state = "STOP" 


command_queue = queue.Queue()

def machine_controller():
    """
    Hilo que se encarga de recibir órdenes para arrancar o parar la máquina.
    Las órdenes se reciben desde la cola 'command_queue' y se actúa en consecuencia.
    """
    global machine_state
    while True:
        command = command_queue.get()  
        if command == "START":
            print("Recibido comando: ARRANCAR la máquina.")
            machine_state = "START"
            print("Máquina arrancada. Estado actual:", machine_state)
        elif command == "STOP":
            print("Recibido comando: PARAR la máquina.")
            machine_state = "STOP"
            print("Máquina parada. Estado actual:", machine_state)
        command_queue.task_done()

def file_reader():
    """
    Función que lee periódicamente el fichero 'estado.txt'.
    Si se detecta que el fichero contiene un "1" y la máquina está en STOP,
    se envía la orden de arrancar; si contiene un "0" y la máquina está en START,
    se envía la orden de parar.
    """
    global machine_state
    while True:
        if os.path.exists("estado.txt"):
            try:
                with open("estado.txt", "r") as f:
                    content = f.read().strip()
                if content not in ["0", "1"]:
                    print("Contenido no válido en 'estado.txt':", content)
                else:
                    if content == "1" and machine_state == "STOP":
                        print("Se detectó orden START en 'estado.txt'.")
                        command_queue.put("START")
                    elif content == "0" and machine_state == "START":
                        print("Se detectó orden STOP en 'estado.txt'.")
                        command_queue.put("STOP")
            except Exception as e:
                print("Error al leer 'estado.txt':", e)
        else:
            print("El archivo 'estado.txt' no existe.")
        time.sleep(1) 

if __name__ == "__main__":
    controller_thread = threading.Thread(target=machine_controller, daemon=True)
    controller_thread.start()
    reader_thread = threading.Thread(target=file_reader, daemon=True)
    reader_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nPrograma finalizado por el usuario.")
