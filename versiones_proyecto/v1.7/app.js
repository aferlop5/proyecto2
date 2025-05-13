const API_BASE_URL = "http://localhost:5000";
let userCredentials = JSON.parse(localStorage.getItem("userCredentials")) || null;

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
            localStorage.setItem("userCredentials", JSON.stringify(userCredentials)); // Guarda las credenciales en localStorage
            alert("Inicio de sesión exitoso");
            toggleSections(true); // Muestra las secciones protegidas
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
        .then(data => alert(`Cinta iniciada: ${JSON.stringify(data)}`))
        .catch(error => console.error("Error:", error));
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
        .then(data => alert(`Cinta iniciada: ${JSON.stringify(data)}`))
        .catch(error => console.error("Error:", error));
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
        .then(data => alert(`Cinta detenida: ${JSON.stringify(data)}`))
        .catch(error => console.error("Error:", error));
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
        .then(data => alert(`Ventosa activada: ${JSON.stringify(data)}`))
        .catch(error => console.error("Error:", error));
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
        .then(data => alert(`Ventosa desactivada: ${JSON.stringify(data)}`))
        .catch(error => console.error("Error:", error));
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
        .then(data => alert(`Robot movido: ${JSON.stringify(data)}`))
        .catch(error => console.error("Error:", error));
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
        .then(data => alert(`Modo automático iniciado: ${JSON.stringify(data)}`))
        .catch(error => console.error("Error:", error));
});