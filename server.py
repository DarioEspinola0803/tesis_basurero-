from flask import Flask, request, jsonify, render_template
import numpy as np
import cv2 
import tensorflow as tf
import os

app = Flask(__name__)

print("Cargando modelo de IA (MobileNetV2)...")
model = tf.keras.applications.MobileNetV2(weights="imagenet")
decode_predictions = tf.keras.applications.mobilenet_v2.decode_predictions
print("Modelo cargado y listo.")

def clasificar_imagen(img_cv2):
    img_rgb = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (224, 224))
    img_array = np.array(img_resized)
    
    img_final = np.expand_dims(img_array, axis=0)
    img_final = tf.keras.applications.mobilenet_v2.preprocess_input(img_final)
    
    pred = model.predict(img_final)
    resultados = decode_predictions(pred, top=3)[0]
    
    etiquetas = [r[1].lower() for r in resultados]
    confianza = float(resultados[0][2] * 100)
    print(f"\n[IA] Predicciones: {etiquetas} ({confianza:.1f}%)")
    
    tipo_residuo = 2  # Por defecto papel
    for etiqueta in etiquetas:
        if any(k in etiqueta for k in ["bottle", "plastic", "cup", "can"]):
            tipo_residuo = 1  # Plástico
            break
        elif any(k in etiqueta for k in ["paper", "book", "carton"]):
            tipo_residuo = 2  # Papel
            break
        elif any(k in etiqueta for k in ["banana", "food", "fruit", "orange"]):
            tipo_residuo = 3  # Orgánico
            break
            
    return tipo_residuo, resultados[0][1], confianza

# --- RUTA PARA VISUALIZAR LA PÁGINA WEB ---
@app.route("/web", methods=["GET"])
def home():
    return render_template("index.html")

# --- RECIBE LA FOTO DIRECTAMENTE EN LA RAÍZ "/" ---
@app.route("/", methods=["POST"])
def clasificar():
    try:
        print("\n--> ¡Foto recibida en el servidor!")
        img_bytes = request.data
        if not img_bytes:
            return jsonify({"error": "No se recibieron datos"}), 400

        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({"error": "Imagen corrupta"}), 400

        tipo, etiqueta, confianza = clasificar_imagen(img)
        nombres = {1: "PLASTICO", 2: "PAPEL", 3: "ORGANICO"}
        nombre_detectado = nombres.get(tipo, "DESCONOCIDO")

        print(f"--> Resultado: {nombre_detectado} (Tipo: {tipo})")

        # --- SECCIÓN DE INTERFAZ GRÁFICA DESACTIVADA PARA SERVIDOR EN LA NUBE ---
        # vista = cv2.resize(img, (640, 480))
        # texto = f"{nombre_detectado} ({confianza:.1f}%)"
        # cv2.putText(vista, texto, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
        # cv2.imshow("Camara ESP32-CAM", vista)
        # cv2.waitKey(500)

        return jsonify({"tipo_residuo": tipo})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Toma el puerto que le asigna Render dinámicamente, o usa el 5000 por defecto en local
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=False)
