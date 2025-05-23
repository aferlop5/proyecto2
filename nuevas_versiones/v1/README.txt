==============================
PROYECTO: Clasificación y Paletizado con Niryo Ned2
==============================

Este archivo explica cómo ejecutar el proyecto desde el ZIP proporcionado (nachjp.zip), incluyendo instalación de entorno, configuración y puesta en marcha.

------------------------------
1. EXTRAER EL ZIP
------------------------------
Descomprime el archivo nachjp.zip y accede a la carpeta extraída:

    unzip nachjp.zip
    cd nachjp

------------------------------
2. CREAR UN ENTORNO VIRTUAL
------------------------------
Crea y activa un entorno virtual de Python:

    python3 -m venv venv
    source venv/bin/activate

O el Conda:

	conda activate Niryo


------------------------------
3. INICIAR BASE DE DATOS
------------------------------
Puedes usar Docker para levantar MySQL fácilmente:

    docker run --name mysql-niryodb \
      -e MYSQL_ROOT_PASSWORD=root \
      -e MYSQL_DATABASE=niryodb \
      -e MYSQL_USER=niryouser \
      -e MYSQL_PASSWORD=user2025 \
      -p 3306:3306 -d mysql:8

O crea la base de datos manualmente en tu sistema local (opcional).

------------------------------
4. OPCIONAL: CONFIGURAR IP DEL ROBOT
------------------------------
Abre resourceFlaskAlchemy.py y cambia la línea:

    ROBOT_IP = "158.42.132.223"

Pon la IP actual del robot si vas a usar el Niryo Ned2 real.

------------------------------
5. ARRANCAR LA API
------------------------------
Desde el entorno virtual, ejecuta:

    python initFlaskAlchemy.py

Esto creará las tablas necesarias y arrancará el servidor Flask en:

    http://127.0.0.1:5000

------------------------------
6. USAR LA INTERFAZ WEB
------------------------------
Abre el archivo index-rest.html con doble clic o arrastrándolo a tu navegador.
Desde ahí podrás activar robot, cinta y pinza desde botones.

------------------------------
7. USAR EL PROXY DESDE TERMINAL
------------------------------
Puedes enviar comandos directamente desde terminal:

    python proxy.py              # muestra los comandos disponibles
    python proxy.py grip_close
    python proxy.py belt_speed 40
    python proxy.py modo_auto

------------------------------
8. DETENER
------------------------------
Para cerrar el servidor, pulsa CTRL+C.

Para eliminar el contenedor de MySQL (opcional):

    docker stop mysql-niryodb
    docker rm mysql-niryodb

==============================
