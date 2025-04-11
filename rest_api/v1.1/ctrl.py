import argparse
import proxy

def main():
    parser = argparse.ArgumentParser(description="Cliente de control para el robot Niryo")
    parser.add_argument("action", choices=["start", "stop", "status"], help="Acción a realizar")
    args = parser.parse_args()
    
    if args.action == "start":
        print("Iniciando proceso de clasificación y paletizado...")
        # Aquí iría la llamada al código del robot
    elif args.action == "stop":
        print("Deteniendo proceso...")
        # Aquí se detendría el proceso
    elif args.action == "status":
        stats = proxy.obtener_estadisticas()
        print("Estado actual del sistema:")
        for estado, cantidad in stats:
            print(f"{estado}: {cantidad} piezas")
    
if __name__ == "__main__":
    main()
