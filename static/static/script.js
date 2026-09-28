// Función para cambiar de vista 
function mostrarSeccion(seccion) {
    if(seccion === 'contenedores') {
        alert("Mostrando todos los puntos de recolección registrados en el sistema...");
    } else {
        console.log("Cargando Dashboard principal...");
    }
}

// Función que actualiza los datos
function actualizarNiveles() {
    fetch('/niveles')
        .then(response => response.json())
        .then(sedes => {
            // Buscamos en la lista la sede que tiene el ID "piso10"
            const piso10 = sedes.find(s => s.id === "piso10");
            
            if(piso10) {
                // Actualizar Plástico
                document.getElementById('val-plastico').innerText = piso10.contenedores.plastico + "%";
                document.getElementById('bar-plastico').style.width = piso10.contenedores.plastico + "%";
                document.getElementById('loc-plastico').innerText = piso10.nombre;

                // Actualizar Papel
                document.getElementById('val-papel').innerText = piso10.contenedores.papel + "%";
                document.getElementById('bar-papel').style.width = piso10.contenedores.papel + "%";
                document.getElementById('loc-papel').innerText = piso10.nombre;

                // Actualizar Orgánico
                document.getElementById('val-organico').innerText = piso10.contenedores.organico + "%";
                document.getElementById('bar-organico').style.width = piso10.contenedores.organico + "%";
                document.getElementById('loc-organico').innerText = piso10.nombre;
            }
        })
        .catch(error => console.error('Error al obtener niveles:', error));
}

// Configuración del gráfico 
const ctx = document.getElementById('lineChart').getContext('2d');
const myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['18/05', '19/05', '20/05', '21/05', '22/05', '23/05', '24/05'],
        datasets: [
            { label: 'Plástico', data: [20, 30, 35, 45, 55, 65, 70], borderColor: '#3b82f6', tension: 0.4 },
            { label: 'Papel', data: [10, 15, 20, 30, 35, 40, 45], borderColor: '#10b981', tension: 0.4 },
            { label: 'Orgánico', data: [40, 50, 60, 65, 75, 85, 95], borderColor: '#ef4444', tension: 0.4 }
        ]
    },
    options: {
        responsive: true,
        plugins: { legend: { position: 'bottom' } }
    }
});

// Ejecutar cada 5 segundos
setInterval(actualizarNiveles, 5000);
actualizarNiveles();
