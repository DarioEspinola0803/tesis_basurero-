from flask import Flask, request, jsonify, render_template
import os

app = Flask(__name__)

# ESTADO INICIAL DE LOS CONTENEDORES
estado_contenedores = {
    "plastico": {"porcentaje": 0, "ubicación": "Piso 1 - Pasillo", "estado": "Bajo"},
    "papel": {"porcentaje": 0, "ubicación": "Piso 1 - Biblioteca", "estado": "Bajo"},
    "organico": {"porcentaje": 0, "ubicación": "Piso 1 - Cafetería", "estado": "Bajo"}
}

# ==============================================================================
# RUTA PRINCIPAL (GET: Muestra la página web / POST: Recibe foto de la cámara)
# ==============================================================================
@app.route('/', methods=['GET', 'POST'])
def recibir_imagen():
    # Si entras tú desde el navegador web (método GET):
    if request.method == 'GET':
        return render_template('index.html')

    # Si la ESP32-CAM envía una foto (método POST):
    try:
        imagen_bytes = request.data
        if not imagen_bytes:
            return jsonify({"error": "No se recibieron datos de imagen"}), 400

        print(f"\n--- IMAGEN RECIBIDA DESDE ESP32-CAM ({len(imagen_bytes)} bytes) ---")

        # Clasificación del modelo de IA:
        # 1: Plástico, 2: Papel, 3: Orgánico
        tipo_residuo = 1  

        return jsonify({
            "status": "success",
            "tipo_residuo": tipo_residuo
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==============================================================================
# RUTAS DE API PARA ACTUALIZAR Y LEER EL NIVEL EN TIEMPO REAL
# ==============================================================================
@app.route('/api/estado', methods=['GET'])
def obtener_estado():
    return jsonify(estado_contenedores), 200

@app.route('/api/actualizar', methods=['POST'])
def actualizar_estado():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos no válidos"}), 400

    for tipo in ['plastico', 'papel', 'organico']:
        if tipo in data and 'porcentaje' in data[tipo]:
            p = data[tipo]['porcentaje']
            estado_contenedores[tipo]['porcentaje'] = p
            if p >= 80:
                estado_contenedores[tipo]['estado'] = "Lleno"
            elif p >= 50:
                estado_contenedores[tipo]['estado'] = "Normal"
            else:
                estado_contenedores[tipo]['estado'] = "Bajo"

    return jsonify({"status": "ok", "estado_actual": estado_contenedores}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "Servidor EcoSmart en línea"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
