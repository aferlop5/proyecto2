import threading
import time
import os

update_file_flag = False
alarm_flag = False

def keyboard_listener():
    global update_file_flag, alarm_flag
    while True:
        key = input("Presiona una tecla (X para incrementar, Y para alarma): ").strip().upper()
        if key == "X":
            update_file_flag = True
        elif key == "Y":
            alarm_flag = True

def main():
    global update_file_flag, alarm_flag  
    
    listener = threading.Thread(target=keyboard_listener, daemon=True)
    listener.start()

    while True:
        time.sleep(1)
        if update_file_flag:
            filename = "numero.txt"
            if os.path.exists(filename):
                try:
                    with open(filename, "r") as f:
                        content = f.read().strip()
                    number = int(content)
                except Exception as e:
                    print("Error al leer el número. Se asigna 0 por defecto.", e)
                    number = 0
                number += 1
                with open(filename, "w") as f:
                    f.write(str(number))
                print(f"El fichero {filename} se ha actualizado. Nuevo valor: {number}")
            else:
                print(f"El fichero {filename} no existe. No se ha realizado ninguna acción.")
            update_file_flag = False  # Reinicia la bandera

        if alarm_flag:
            with open("alarma.txt", "w") as f:
                f.write("1")
            print("Se ha escrito '1' en el fichero alarma.txt.")
            alarm_flag = False  # Reinicia la bandera

if __name__ == "__main__":
    main()
