from flask import Flask, request, jsonify, render_template
import tensorflow as tf
import numpy as np
import cv2
import os
from datetime import datetime

app = Flask(__name__)

# ==========================================================
# CONFIGURACIÓN
# ==========================================================

MODEL_PATH = "modelo_residuos.h5"

# IMPORTANTE:
# Este orden debe coincidir con el orden de las clases
# utilizado durante el entrenamiento.
CLASES = [
    "organico",
    "papel-carton",
    "plastico"
]

# ==========================================================
# ESTADO ACTUAL DE LOS CONTENEDORES
# ==========================================================

niveles = {
    "organico": {
        "distancia": 0,
        "porcentaje": 0
    },
    "papel-carton": {
        "distancia": 0,
        "porcentaje": 0
    },
    "plastico": {
        "distancia": 0,
        "porcentaje": 0
    }
}

ultimo_residuo = {
    "tipo": "Ninguno",
    "confianza": 0,
    "hora": "--:--:--"
}


# ==========================================================
# CARGAR MODELO
# ==========================================================

print("=" * 50)
print("CARGANDO MODELO DE IA...")
print("=" * 50)

if not os.path.exists(MODEL_PATH):
    print(f"ERROR: No se encuentra {MODEL_PATH}")
    exit()

model = tf.keras.models.load_model(MODEL_PATH)

print("Modelo cargado correctamente.")
print("Clases:", CLASES)
print("=" * 50)


# ==========================================================
# FUNCIÓN PARA CLASIFICAR IMAGEN
# ==========================================================

def predecir_imagen(ruta_imagen):

    img = cv2.imread(ruta_imagen)

    if img is None:
        print("ERROR: No se pudo leer la imagen.")
        return None

    # OpenCV lee BGR
    # TensorFlow trabaja normalmente con RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Mismo tamaño utilizado durante entrenamiento
    img_resized = cv2.resize(img_rgb, (224, 224))

    # Convertir a array
    img_array = tf.keras.preprocessing.image.img_to_array(img_resized)

    # Agregar dimensión de batch
    img_array = np.expand_dims(img_array, axis=0)

    # NO dividir entre 255
    # El modelo ya posee:
    # Rescaling(1./255)

    predicciones = model.predict(img_array, verbose=0)

    indice = np.argmax(predicciones[0])

    clase = CLASES[indice]

    confianza = float(predicciones[0][indice])

    print("\n" + "=" * 50)
    print("RESULTADO DE LA DETECCIÓN")
    print("=" * 50)

    for i, nombre in enumerate(CLASES):
        porcentaje = predicciones[0][i] * 100
        print(f"{nombre}: {porcentaje:.2f}%")

    print("-" * 50)
    print(f"RESIDUO: {clase.upper()}")
    print(f"CONFIANZA: {confianza * 100:.2f}%")
    print("=" * 50)

    return clase, confianza


# ==========================================================
# PÁGINA PRINCIPAL
# ==========================================================

@app.route("/")
def inicio():
    return render_template(
        "index.html",
        niveles=niveles,
        ultimo=ultimo_residuo
    )


# ==========================================================
# API - CLASIFICAR IMAGEN
# ==========================================================

@app.route("/clasificar", methods=["POST"])
def clasificar():

    if "imagen" not in request.files:
        return jsonify({
            "error": "No se recibió ninguna imagen"
        }), 400

    archivo = request.files["imagen"]

    if archivo.filename == "":
        return jsonify({
            "error": "Nombre de archivo vacío"
        }), 400

    ruta_imagen = "imagen_recibida.jpg"

    try:

        archivo.save(ruta_imagen)

        print("\nImagen recibida desde ESP32-CAM.")

        resultado = predecir_imagen(ruta_imagen)

        if resultado is None:
            return jsonify({
                "error": "No se pudo procesar la imagen"
            }), 500

        clase, confianza = resultado

        # Guardar último resultado
        ultimo_residuo["tipo"] = clase
        ultimo_residuo["confianza"] = round(confianza * 100, 2)
        ultimo_residuo["hora"] = datetime.now().strftime("%H:%M:%S")

        return jsonify({
            "residuo": clase,
            "confianza": round(confianza * 100, 2)
        })

    except Exception as e:

        print("ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================================
# API - RECIBIR NIVELES DE LLENADO
# ==========================================================

@app.route("/niveles", methods=["POST"])
def recibir_niveles():

    try:

        datos = request.get_json()

        if not datos:
            return jsonify({
                "error": "No se recibieron datos"
            }), 400

        # --------------------------------------------------
        # ORGÁNICO
        # --------------------------------------------------

        if "organico" in datos:

            distancia = float(datos["organico"])

            niveles["organico"]["distancia"] = round(distancia, 1)

            niveles["organico"]["porcentaje"] = calcular_porcentaje(
                distancia
            )

        # --------------------------------------------------
        # PAPEL-CARTÓN
        # --------------------------------------------------

        if "papel-carton" in datos:

            distancia = float(datos["papel-carton"])

            niveles["papel-carton"]["distancia"] = round(distancia, 1)

            niveles["papel-carton"]["porcentaje"] = calcular_porcentaje(
                distancia
            )

        # --------------------------------------------------
        # PLÁSTICO
        # --------------------------------------------------

        if "plastico" in datos:

            distancia = float(datos["plastico"])

            niveles["plastico"]["distancia"] = round(distancia, 1)

            niveles["plastico"]["porcentaje"] = calcular_porcentaje(
                distancia
            )

        print("\nNIVELES ACTUALIZADOS")

        print(
            "Orgánico:",
            niveles["organico"]["porcentaje"],
            "%"
        )

        print(
            "Papel-cartón:",
            niveles["papel-carton"]["porcentaje"],
            "%"
        )

        print(
            "Plástico:",
            niveles["plastico"]["porcentaje"],
            "%"
        )

        return jsonify({
            "mensaje": "Niveles actualizados correctamente"
        })

    except Exception as e:

        print("ERROR NIVELES:", e)

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================================
# CALCULAR PORCENTAJE DE LLENADO
# ==========================================================

def calcular_porcentaje(distancia):

    # MODIFICAR ESTOS VALORES SEGÚN TU CONTENEDOR REAL

    DISTANCIA_VACIO = 35.0
    DISTANCIA_LLENO = 5.0

    if distancia >= DISTANCIA_VACIO:
        return 0

    if distancia <= DISTANCIA_LLENO:
        return 100

    porcentaje = (
        (DISTANCIA_VACIO - distancia)
        /
        (DISTANCIA_VACIO - DISTANCIA_LLENO)
    ) * 100

    porcentaje = max(0, min(100, porcentaje))

    return round(porcentaje)


# ==========================================================
# API - CONSULTAR ESTADO
# ==========================================================

@app.route("/estado", methods=["GET"])
def estado():

    return jsonify({
        "niveles": niveles,
        "ultimo_residuo": ultimo_residuo
    })


# ==========================================================
# INICIAR SERVIDOR
# ==========================================================

if __name__ == "__main__":

    print("\n======================================")
    print(" SERVIDOR DEL BASURERO INTELIGENTE")
    print("======================================")
    print("Servidor iniciado en puerto 5000")
    print("Página: http://TU_IP:5000")
    print("======================================\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
