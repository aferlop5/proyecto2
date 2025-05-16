// Configuración de la API
const API_PORT = 5000;  // Puerto principal
const API_ALT_PORT = 5001;  // Puerto alternativo
const API_BASE_URL = "http://localhost:5000";
let userCredentials = JSON.parse(localStorage.getItem("userCredentials")) || null;

// Al inicio del archivo, después de las configuraciones
let commandHistory = JSON.parse(localStorage.getItem('commandHistory')) || [];

function addToHistory(buttonName, success, errorMessage = null) {
    const timestamp = new Date().toLocaleTimeString();
    const historyItem = {
        action: `Botón: ${buttonName}`,
        timestamp,
        success,
        error: errorMessage
    };
    commandHistory.unshift(historyItem);
    if (commandHistory.length > 50) {
        commandHistory.pop();
    }
    localStorage.setItem('commandHistory', JSON.stringify(commandHistory));
    updateHistoryDisplay();
}

function updateHistoryDisplay() {
    const historyList = document.getElementById('historyList');
    if (!historyList) return;

    historyList.innerHTML = commandHistory.map(item => `
        <li class="${item.success ? 'command-success' : 'command-error'}">
            <span>${item.action}${item.error ? `<br><span class="error-message">Error: ${item.error}</span>` : ''}</span>
            <span class="command-timestamp">${item.timestamp}</span>
        </li>
    `).join('');
}

// Añadir el evento para limpiar el historial
document.getElementById('clearHistory')?.addEventListener('click', () => {
    commandHistory = [];
    localStorage.setItem('commandHistory', JSON.stringify(commandHistory));
    updateHistoryDisplay();
});

// Función para verificar la disponibilidad del servidor
async function checkServer() {
    try {
        const response = await fetch(`${API_BASE_URL}/sensores/estado`);
        if (!response.ok) throw new Error('Server not available');
        return true;
    } catch (e) {
        console.log(`Puerto ${API_PORT} no disponible, intentando puerto alternativo...`);
        try {
            const altResponse = await fetch(`${API_BASE_URL}/sensores/estado`);
            if (!altResponse.ok) throw new Error('Alternate server not available');
            console.log(`Conectado exitosamente al puerto ${API_ALT_PORT}`);
            return true;
        } catch (e) {
            console.error('No se pudo conectar a ningún puerto del servidor');
            return false;
        }
    }
}

// Inicializar la conexión
checkServer().then(available => {
    if (!available) {
        alert('No se pudo conectar al servidor. Por favor, verifica que el servidor esté corriendo.');
    }
});

// Configuración de WebSocket con reconexión automática
let socket;

function connectWebSocket() {
    socket = io(API_BASE_URL, {
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        reconnectionAttempts: 5
    });

    socket.on('connect', () => {
        console.log('Conectado al servidor WebSocket');
    });

    socket.on('connect_error', (error) => {
        console.log('Error de conexión WebSocket:', error);
    });

    socket.on('reconnect', (attemptNumber) => {
        console.log('Reconectado al servidor WebSocket después de', attemptNumber, 'intentos');
    });

    socket.on('error_state', (data) => {
        const statusElement = document.getElementById(`${data.component}Status`);
        if (statusElement) {
            statusElement.textContent = data.error;
            statusElement.className = 'status-error';
        }
    });

    socket.on('sensor_update', (data) => {
        updateSensorDisplay(data);
    });

    socket.on('robot_position_update', (data) => {
        updateRobotPositionDisplay(data);
    });

    socket.on('ventosa_update', (data) => {
        updateVentosaDisplay(data);
    });

    socket.on('cinta_update', (data) => {
        updateCintaDisplay(data);
    });

    socket.on('auto_complete', (data) => {
        showAutoModeResults(data);
    });
}

connectWebSocket();

// Manejadores de eventos WebSocket
socket.on('sensor_update', (data) => {
    updateSensorDisplay(data);
});

socket.on('robot_position_update', (data) => {
    updateRobotPositionDisplay(data);
});

socket.on('ventosa_update', (data) => {
    updateVentosaDisplay(data);
});

socket.on('cinta_update', (data) => {
    updateCintaDisplay(data);
});

socket.on('auto_complete', (data) => {
    showAutoModeResults(data);
});

// Funciones de actualización de UI
function updateSensorDisplay(data) {
    const sensorDI1Status = document.getElementById('sensorDI1Status');
    const sensorDI5Status = document.getElementById('sensorDI5Status');
    
    if (sensorDI1Status && data.sensor_di1) {
        sensorDI1Status.textContent = `Estado: ${data.sensor_di1}`;
        sensorDI1Status.className = data.sensor_di1 === 'HIGH' ? 'status-active' : 'status-inactive';
    }
    
    if (sensorDI5Status && data.sensor_di5) {
        sensorDI5Status.textContent = `Estado: ${data.sensor_di5}`;
        sensorDI5Status.className = data.sensor_di5 === 'HIGH' ? 'status-active' : 'status-inactive';
    }
}

function updateRobotPositionDisplay(data) {
    const positionDisplay = document.getElementById('robotPosition');
    if (positionDisplay) {
        positionDisplay.textContent = `Posición: X=${data.x}, Y=${data.y}, Z=${data.z}`;
        positionDisplay.className = 'status-active';
    }
}

function updateVentosaDisplay(data) {
    const ventosaStatus = document.getElementById('ventosaStatus');
    if (ventosaStatus) {
        ventosaStatus.textContent = `Estado: ${data.estado}`;
        ventosaStatus.className = data.estado === 'activar' ? 'status-active' : 'status-inactive';
    }
}

function updateCintaDisplay(data) {
    const cintaStatus = document.getElementById('cintaStatus');
    if (cintaStatus) {
        cintaStatus.textContent = `Estado: ${data.estado} - Dirección: ${data.direccion} - Velocidad: ${data.velocidad}`;
        cintaStatus.className = data.estado === 'running' ? 'status-active' : 'status-inactive';
    }
}

function showAutoModeResults(data) {
    const resultsDiv = document.getElementById('autoModeResults');
    if (resultsDiv) {
        resultsDiv.classList.remove('hidden');
        resultsDiv.innerHTML = `
            <h4>Resultados del Modo Automático:</h4>
            <p>Tiempo total: ${data.robot.min_total} minutos y ${data.robot.seg_total} segundos</p>
            <p>Piezas pequeñas: ${data.robot.piezas_peque} (Tiempo: ${data.robot.tiempo_peque}s)</p>
            <p>Piezas grandes: ${data.robot.piezas_grandes} (Tiempo: ${data.robot.tiempo_grande}s)</p>
            <p>Paro manual: ${data.robot.paro_manual ? 'Sí' : 'No'}</p>
        `;
    }
}

// Manejo de Usuarios
document.getElementById("loginForm").addEventListener("submit", (event) => {
    event.preventDefault();

    const nick = document.getElementById("nick").value;
    const password = document.getElementById("password").value;

    fetch(`${API_BASE_URL}/usuario`, {
        method: "GET",
        headers: {
            "nick": nick,
            "password": password
        }
    })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error("Credenciales incorrectas");
            }
        })
        .then(data => {
            userCredentials = { nick, password };
            localStorage.setItem("userCredentials", JSON.stringify(userCredentials));
            alert("Inicio de sesión exitoso");
            toggleSections(true);
        })
        .catch(error => {
            alert(error.message);
            console.error("Error:", error);
        });
});

document.getElementById("registerButton").addEventListener("click", () => {
    const nick = prompt("Introduce un nick:");
    const password = prompt("Introduce una contraseña:");

    if (nick && password) {
        fetch(`${API_BASE_URL}/usuario`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nick, password })
        })
            .then(response => {
                if (response.ok) {
                    alert("Usuario registrado exitosamente");
                } else {
                    return response.json().then(data => {
                        throw new Error(data.message || "Error al registrar usuario");
                    });
                }
            })
            .catch(error => {
                alert(error.message);
                console.error("Error:", error);
            });
    }
});

// Función para mostrar/ocultar secciones
function toggleSections(isLoggedIn) {
    const sections = document.querySelectorAll("section");
    sections.forEach(section => {
        if (section.id !== "userSection") {
            section.classList.toggle("hidden", !isLoggedIn);
        }
    });

    // Oculta la sección de login si el usuario está autenticado
    document.getElementById("userSection").classList.toggle("hidden", isLoggedIn);

    // Muestra el botón de cerrar sesión si el usuario está autenticado
    document.getElementById("logoutButton").classList.toggle("hidden", !isLoggedIn);
}

// Verifica si el usuario ya está autenticado al cargar la página
if (userCredentials) {
    toggleSections(true);
} else {
    toggleSections(false);
}

// Función para cerrar sesión
document.getElementById("logoutButton").addEventListener("click", () => {
    localStorage.removeItem("userCredentials"); // Elimina las credenciales del almacenamiento local
    userCredentials = null;
    toggleSections(false); // Vuelve a la pantalla de login
    alert("Sesión cerrada exitosamente");
});

// Control de la cinta
document.getElementById("startCintaForward").addEventListener("click", () => {
    fetch(`${API_BASE_URL}/cinta/run`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "nick": userCredentials.nick,
            "password": userCredentials.password
        },
        body: JSON.stringify({ direccion: "forward", velocidad: 100 })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addToHistory("Iniciar Cinta Adelante", false, data.error);
                throw new Error(data.error);
            }
            addToHistory("Iniciar Cinta Adelante", true);
        })
        .catch(error => {
            console.error("Error:", error);
            addToHistory("Iniciar Cinta Adelante", false, error.message);
        });
});

document.getElementById("startCintaBackward").addEventListener("click", () => {
    fetch(`${API_BASE_URL}/cinta/run`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "nick": userCredentials.nick,
            "password": userCredentials.password
        },
        body: JSON.stringify({ direccion: "backward", velocidad: 100 })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addToHistory("Iniciar Cinta Atrás", false, data.error);
                throw new Error(data.error);
            }
            addToHistory("Iniciar Cinta Atrás", true);
        })
        .catch(error => {
            console.error("Error:", error);
            addToHistory("Iniciar Cinta Atrás", false, error.message);
        });
});

document.getElementById("stopCinta").addEventListener("click", () => {
    fetch(`${API_BASE_URL}/cinta/stop`, {
        method: "POST",
        headers: {
            "nick": userCredentials.nick,
            "password": userCredentials.password
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addToHistory("Detener Cinta", false, data.error);
                throw new Error(data.error);
            }
            addToHistory("Detener Cinta", true);
        })
        .catch(error => {
            console.error("Error:", error);
            addToHistory("Detener Cinta", false, error.message);
        });
});

// Control de la ventosa
document.getElementById("activarVentosa").addEventListener("click", () => {
    fetch(`${API_BASE_URL}/control_ventosa`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "nick": userCredentials.nick,
            "password": userCredentials.password
        },
        body: JSON.stringify({ accion: "activar" })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addToHistory("Activar Ventosa", false, data.error);
                throw new Error(data.error);
            }
            addToHistory("Activar Ventosa", true);
        })
        .catch(error => {
            console.error("Error:", error);
            addToHistory("Activar Ventosa", false, error.message);
        });
});

document.getElementById("desactivarVentosa").addEventListener("click", () => {
    fetch(`${API_BASE_URL}/control_ventosa`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "nick": userCredentials.nick,
            "password": userCredentials.password
        },
        body: JSON.stringify({ accion: "desactivar" })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addToHistory("Desactivar Ventosa", false, data.error);
                throw new Error(data.error);
            }
            addToHistory("Desactivar Ventosa", true);
        })
        .catch(error => {
            console.error("Error:", error);
            addToHistory("Desactivar Ventosa", false, error.message);
        });
});

// Control del robot
document.getElementById("robotForm").addEventListener("submit", (event) => {
    event.preventDefault();

    const x = document.getElementById("x").value;
    const y = document.getElementById("y").value;
    const z = document.getElementById("z").value;
    const roll = document.getElementById("roll").value;
    const pitch = document.getElementById("pitch").value;
    const yaw = document.getElementById("yaw").value;

    fetch(`${API_BASE_URL}/control_robot`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "nick": userCredentials.nick,
            "password": userCredentials.password
        },
        body: JSON.stringify({ x, y, z, roll, pitch, yaw })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addToHistory("Mover Robot", false, data.error);
                throw new Error(data.error);
            }
            addToHistory("Mover Robot", true);
        })
        .catch(error => {
            console.error("Error:", error);
            addToHistory("Mover Robot", false, error.message);
        });
});

// Modo automático
document.getElementById("startAuto").addEventListener("click", () => {
    fetch(`${API_BASE_URL}/auto`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "nick": userCredentials.nick,
            "password": userCredentials.password
        },
        body: JSON.stringify({ usuario_id: userCredentials.nick })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addToHistory("Modo Automático", false, data.error);
                throw new Error(data.error);
            }
            // Añadir al historial con detalles del modo automático
            const details = `Piezas procesadas - Pequeñas: ${data.data.robot.piezas_peque}, Grandes: ${data.data.robot.piezas_grandes}`;
            addToHistory("Modo Automático", true, details);
            showAutoModeResults(data.data);
        })
        .catch(error => {
            console.error("Error:", error);
            addToHistory("Modo Automático", false, error.message);
        });
});

function actualizarSensores() {
  fetch('http://localhost:5000/sensores/estado')
    .then(response => response.json())
    .then(data => {
      const di1 = document.getElementById("sensorDI1");
      const di5 = document.getElementById("sensorDI5");

      if (data.DI1) {
        di1.classList.add("on");
        di1.classList.remove("off");
      } else {
        di1.classList.add("off");
        di1.classList.remove("on");
      }

      if (data.DI5) {
        di5.classList.add("on");
        di5.classList.remove("off");
      } else {
        di5.classList.add("off");
        di5.classList.remove("on");
      }
    });
}

// Llamar al actualizarSensores cada segundo
setInterval(actualizarSensores, 1000);

// Cargar el historial al iniciar
document.addEventListener('DOMContentLoaded', () => {
    updateHistoryDisplay();
});

document.getElementById('startButton').addEventListener('click', function() {
    fetch('/start_automatic_mode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => response.json())
      .then(data => console.log(data.message))
      .catch(error => console.error('Error:', error));
});

document.getElementById('stopButton').addEventListener('click', function() {
    fetch('/stop_automatic_mode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => response.json())
      .then(data => console.log(data.message))
      .catch(error => console.error('Error:', error));
});
