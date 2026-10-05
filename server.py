from flask import Flask, request, jsonify
from PIL import Image
import io
import os

app = Flask(__name__)

# ==============================================================================
# 1. CARGA DE TU MODELO DE INTELIGENCIA ARTIFICIAL
# ==============================================================================
# Aquí importas y ejecutas la predicción según la librería de tu modelo.
# Ejemplo de función de predicción:

def predecir_residuo(imagen_bytes):
    """
    Recibe los bytes de la imagen JPEG recibida del ESP32-CAM,
    la procesa a través de tu modelo entrenado y retorna el tipo de residuo:
      1 -> Plástico
      2 -> Papel / Cartón
      3 -> Orgánico
    """
    image = Image.open(io.BytesIO(imagen_bytes))
    
    # --------------------------------------------------------------------------
    # REEMPLAZA ESTE BLOQUE CON EL CÓDIGO REAL DE TU MODELO ENTRENADO:
    # --------------------------------------------------------------------------
    # Ejemplo conceptual:
    # resultado = modelo.predict(image)
    # clase_detectada = resultado.class_name
    
    # Supongamos que tu modelo retorna una clase: 'plastico', 'papel' u 'organico'
    # Mapeo a los valores numéricos que espera el ESP32-CAM:
    
    # Por defecto, puedes ajustar la lógica de detección aquí:
    # tipo_residuo = 1 (Plástico)
    # tipo_residuo = 2 (Papel)
    # tipo_residuo = 3 (Orgánico)
    
    tipo_residuo = 1  # Cambiar según el resultado de tu modelo
    
    return tipo_residuo

# ==============================================================================
# 2. RUTA HTTP POST PARA RECIBIR LA IMAGEN DEL ESP32-CAM
# ==============================================================================
@app.route('/', methods=['POST'])
def recibir_imagen():
    try:
        # Obtener los bytes directamente desde el cuerpo de la petición HTTP
        imagen_bytes = request.data

        if not imagen_bytes:
            return jsonify({"error": "No se recibieron datos de imagen"}), 400

        print(f"\n--- IMAGEN RECIBIDA DESDE ESP32-CAM ({len(imagen_bytes)} bytes) ---")

        # Pasar la imagen por tu modelo entrenado
        tipo = predecir_residuo(imagen_bytes)

        # Responder al ESP32-CAM con el formato JSON esperado
        respuesta = {
            "status": "success",
            "tipo_residuo": tipo
        }
        
        print(f"Predicción enviada al ESP32: tipo_residuo = {tipo}")
        return jsonify(respuesta), 200

    except Exception as e:
        print(f"Error procesando la imagen: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==============================================================================
# 3. RUTA DE PRUEBA DE SALUD (HEALTH CHECK)
# ==============================================================================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "Servidor EcoSmart en línea"}), 200

# ==============================================================================
# 4. INICIO DEL SERVIDOR
# ==============================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
