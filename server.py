from flask import Flask, request, jsonify, render_template
import numpy as np
import cv2
import tensorflow as tf
import os
from datetime import datetime

app = Flask(__name__)

# ============================================================
# CARGAR MODELO DE IA
# ============================================================

print("Cargando modelo de IA (MobileNetV2)...")

model = tf.keras.applications.MobileNetV2(weights="imagenet")

decode_predictions = (
    tf.keras.applications.mobilenet_v2.decode_predictions
)

print("Modelo cargado y listo.")


# ============================================================
# ESTADO ACTUAL DE LOS CONTENEDORES
#
# Por ahora se guarda en memoria.
#
# IMPORTANTE:
# En Render esto se reinicia si el servidor se reinicia.
# Para la primera etapa/prototipo está bien.
# Más adelante podemos utilizar una base de datos.
# ============================================================

niveles = {
    1: {
        "nombre": "PLASTICO",
        "distancia_cm": None,
        "nivel": 0,
        "ultima_actualizacion": None
    },

    2: {
        "nombre": "PAPEL-CARTON",
        "distancia_cm": None,
        "nivel": 0,
        "ultima_actualizacion": None
    },

    3: {
        "nombre": "ORGANICO",
        "distancia_cm": None,
        "nivel": 0,
        "ultima_actualizacion": None
    }
}


# ============================================================
# CLASIFICACIÓN DE IMAGEN
# ============================================================

def clasificar_imagen(img_cv2):

    img_rgb = cv2.cvtColor(
        img_cv2,
        cv2.COLOR_BGR2RGB
    )

    img_resized = cv2.resize(
        img_rgb,
        (224, 224)
    )

    img_array = np.array(img_resized)

    img_final = np.expand_dims(
        img_array,
        axis=0
    )

    img_final = (
        tf.keras.applications.mobilenet_v2
        .preprocess_input(img_final)
    )

    pred = model.predict(
        img_final,
        verbose=0
    )

    resultados = decode_predictions(
        pred,
        top=3
    )[0]

    etiquetas = [
        r[1].lower()
        for r in resultados
    ]

    confianza = float(
        resultados[0][2] * 100
    )

    print(
        f"\n[IA] Predicciones: "
        f"{etiquetas} "
        f"({confianza:.1f}%)"
    )

    # --------------------------------------------------------
    # CLASIFICACIÓN ACTUAL
    #
    # Esto es una aproximación utilizando etiquetas
    # de ImageNet.
    #
    # Más adelante reemplazaremos esto por el modelo
    # entrenado específicamente con las 3 clases.
    # --------------------------------------------------------

    tipo_residuo = 2

    for etiqueta in etiquetas:

        # PLÁSTICO
        if any(
            k in etiqueta
            for k in [
                "bottle",
                "plastic",
                "cup",
                "can"
            ]
        ):
            tipo_residuo = 1
            break

        # PAPEL / CARTÓN
        elif any(
            k in etiqueta
            for k in [
                "paper",
                "book",
                "carton"
            ]
        ):
            tipo_residuo = 2
            break

        # ORGÁNICO
        elif any(
            k in etiqueta
            for k in [
                "banana",
                "food",
                "fruit",
                "orange"
            ]
        ):
            tipo_residuo = 3
            break

    return (
        tipo_residuo,
        resultados[0][1],
        confianza
    )


# ============================================================
# PÁGINA WEB
# ============================================================

@app.route(
    "/web",
    methods=["GET"]
)
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# RECIBIR FOTO DEL ESP32-CAM
#
# ESP32:
#
# POST /
# Content-Type: image/jpeg
#
# Respuesta:
#
# {
#     "tipo_residuo": 1
# }
# ============================================================

@app.route(
    "/",
    methods=["POST"]
)
def clasificar():

    try:

        print(
            "\n--> ¡Foto recibida "
            "en el servidor!"
        )

        img_bytes = request.data

        if not img_bytes:

            return jsonify({
                "error":
                "No se recibieron datos"
            }), 400

        # Convertir bytes a imagen
        nparr = np.frombuffer(
            img_bytes,
            np.uint8
        )

        img = cv2.imdecode(
            nparr,
            cv2.IMREAD_COLOR
        )

        if img is None:

            return jsonify({
                "error":
                "Imagen corrupta"
            }), 400

        # Clasificar
        tipo, etiqueta, confianza = (
            clasificar_imagen(img)
        )

        nombres = {
            1: "PLASTICO",
            2: "PAPEL-CARTON",
            3: "ORGANICO"
        }

        nombre_detectado = nombres.get(
            tipo,
            "DESCONOCIDO"
        )

        print(
            f"--> Resultado: "
            f"{nombre_detectado} "
            f"(Tipo: {tipo})"
        )

        print(
            f"--> Etiqueta IA: "
            f"{etiqueta}"
        )

        print(
            f"--> Confianza: "
            f"{confianza:.1f}%"
        )

        # Respuesta al ESP32-CAM
        return jsonify({
            "tipo_residuo": tipo
        })

    except Exception as e:

        print(
            f"ERROR clasificación: {e}"
        )

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# RECIBIR NIVEL DE CONTENEDOR
#
# ESP32 envía:
#
# {
#     "tipo_residuo": 2,
#     "distancia_cm": 18.5,
#     "nivel": 67
# }
#
# El servidor guarda el dato correspondiente.
# ============================================================

@app.route(
    "/nivel",
    methods=["POST"]
)
def recibir_nivel():

    try:

        datos = request.get_json(
            silent=True
        )

        if not datos:

            return jsonify({
                "error":
                "No se recibió JSON"
            }), 400

        # ------------------------------------
        # Obtener datos
        # ------------------------------------

        tipo = datos.get(
            "tipo_residuo"
        )

        distancia = datos.get(
            "distancia_cm"
        )

        nivel = datos.get(
            "nivel"
        )

        print(
            "\n--> NIVEL RECIBIDO"
        )

        print(
            f"Tipo: {tipo}"
        )

        print(
            f"Distancia: {distancia} cm"
        )

        print(
            f"Nivel: {nivel}%"
        )

        # ------------------------------------
        # Validar tipo
        # ------------------------------------

        if tipo not in [1, 2, 3]:

            return jsonify({
                "error":
                "Tipo de residuo inválido"
            }), 400

        # ------------------------------------
        # Validar nivel
        # ------------------------------------

        if nivel is None:

            return jsonify({
                "error":
                "No se recibió nivel"
            }), 400

        nivel = float(nivel)

        if nivel < 0:
            nivel = 0

        if nivel > 100:
            nivel = 100

        # ------------------------------------
        # Guardar
        # ------------------------------------

        niveles[tipo][
            "distancia_cm"
        ] = distancia

        niveles[tipo][
            "nivel"
        ] = nivel

        niveles[tipo][
            "ultima_actualizacion"
        ] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        print(
            f"--> Contenedor "
            f"{niveles[tipo]['nombre']} "
            f"actualizado: "
            f"{nivel:.0f}%"
        )

        # ------------------------------------
        # Respuesta al ESP32
        # ------------------------------------

        return jsonify({
            "ok": True,
            "tipo_residuo": tipo,
            "nivel": nivel
        })

    except Exception as e:

        print(
            f"ERROR recibiendo nivel: {e}"
        )

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# CONSULTAR ESTADO DE LOS CONTENEDORES
#
# GET /estado
#
# Devuelve los tres niveles.
# Esto será útil para el dashboard.
# ============================================================

@app.route(
    "/estado",
    methods=["GET"]
)
def obtener_estado():

    return jsonify({
        "plastico": niveles[1],
        "papel_carton": niveles[2],
        "organico": niveles[3]
    })


# ============================================================
# RUTA DE PRUEBA
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def inicio():

    return jsonify({
        "sistema": "EcoSmart",
        "estado": "online",
        "endpoints": {
            "clasificacion": "POST /",
            "nivel": "POST /nivel",
            "estado": "GET /estado",
            "dashboard": "GET /web"
        }
    })


# ============================================================
# EJECUTAR SERVIDOR
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        threaded=False
    )

if __name__ == "__main__":
    # Toma el puerto que le asigna Render dinámicamente, o usa el 5000 por defecto en local
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=False)
