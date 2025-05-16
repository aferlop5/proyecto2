Este proyecto permite controlar un robot Niryo a través de una API REST y una interfaz web. A continuación, se describe brevemente el propósito de cada archivo y su funcionalidad.

---

## Archivos y Descripción

### 1. `rest.py`
- Implementa la API REST usando Flask.
- Contiene rutas para manejar usuarios, sensores, ventosas y el modo automático.
- Verifica credenciales de usuarios y realiza operaciones CRUD en la base de datos.
- Expone rutas para controlar la cinta transportadora, ventosa y movimientos del robot.

---

### 2. `app.js`
- Archivo JavaScript para el frontend.
- Maneja el inicio de sesión, registro y cierre de sesión de usuarios.
- Envía comandos al backend para controlar la cinta, ventosa, robot y modo automático.
- Muestra/oculta secciones de la interfaz según el estado de autenticación del usuario.

---

### 3. `index.html`
- Define la estructura de la interfaz web.
- Contiene secciones para login, control de la cinta, ventosa, robot y modo automático.
- Incluye botones y formularios para interactuar con las funcionalidades del backend.

---

### 4. `styles.css`
- Archivo CSS que define el diseño visual de la interfaz.
- Estiliza botones, formularios y secciones, con efectos como hover y transiciones.

---

### 5. `control.py` (anteriormente `ejemploNiryo.py`)
- Simula el comportamiento del robot para pruebas.
- Genera estados aleatorios para sensores y simula el control de la cinta y ventosa.
- Incluye un flujo automatizado para el modo automático.
- Contiene funciones para inicializar y cerrar la conexión simulada con el robot.

---

### 6. `database.py`
- Maneja la conexión a la base de datos MySQL.
- Crea la base de datos y tablas necesarias si no existen.
- Configura las tablas para almacenar datos de usuarios, sensores y ventosas.

---

### 7. `id.txt` (Eliminado)
- Archivo previamente usado para generar IDs únicos.
- Reemplazado por la generación de UUIDs directamente en el código.

---

## Cómo Funciona

1. **Inicio de Sesión y Registro:**
   - Los usuarios pueden registrarse y autenticarse desde la interfaz web.
   - Las credenciales se verifican contra la base de datos.

2. **Control del Robot:**
   - Desde la interfaz, se pueden enviar comandos para mover el robot, controlar la cinta y la ventosa.

3. **Modo Automático:**
   - Permite ejecutar un flujo automatizado de movimientos y acciones del robot.

4. **Base de Datos:**
   - Almacena información de usuarios, sesiones del robot y datos de sensores.

---

## Requisitos

- **Backend:** Python 3, Flask, MySQL.
- **Frontend:** Navegador web moderno.
- **Base de Datos:** MySQL.

---

## Ejecución

1. Configura la base de datos ejecutando `database.py` (docker exec -it mysql_robot mysql -u root).
2. Inicia el servidor Flask con `rest.py`.
3. Abre `index.html` en un navegador para interactuar con la interfaz (python3 -m http.server) y (http://localhost:5000).

---

## Cambios Realizados

- El archivo `ejemploNiryo.py` fue renombrado a `control.py`.
- Todas las referencias a `ejemploNiryo.py` en el código fueron actualizadas a `control.py`.
- Eliminada la dependencia de `id.txt` para la generación de IDs únicos.