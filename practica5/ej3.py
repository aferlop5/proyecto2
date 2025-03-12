import datetime

def log_key_event(key, counter, log_file="datos.txt"):
    """
    Registra en el fichero 'datos.txt' la pulsación de una tecla junto con:
    - El número de evento (contador).
    - La fecha y hora en que se pulsó.
    - La tecla pulsada.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_line = f"{counter},{timestamp},{key}\n"
    with open(log_file, "a") as f:
        f.write(data_line)

def main():
    event_counter = 0
    while True:
        key = input("Presiona una tecla y pulsa Enter: ")
        event_counter += 1
        log_key_event(key, event_counter)
        print(f"Evento {event_counter} registrado: {key}")

if __name__ == "__main__":
    main()
