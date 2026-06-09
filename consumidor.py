"""
consumidor.py — VERSIÓN ACTUALIZADA para AC-04 + AC-05
Ahora recibe y guarda el texto de la conversación además de los metadatos.

CONTRATO DE MENSAJE ACTUALIZADO:
{
  "id_interaccion": "UUID",
  "modulo_origen": "chatbot | resolutor | sentimiento",
  "timestamp": "ISO 8601",
  "resultado": "EXITOSO | FALLIDO",
  "paso_fallido": "string o null",
  "sentimiento_final": "POSITIVO | NEUTRAL | NEGATIVO",
  "texto_usuario": "Lo que escribió el usuario",         <-- NUEVO
  "respuesta_agente": "Lo que respondió el bot/sistema"  <-- NUEVO
}
"""

import pika
import json
import psycopg2
from datetime import datetime

# =====================================================================
# 1. CONFIGURACIÓN DE LA BASE DE DATOS
# =====================================================================
def conectar_db():
    return psycopg2.connect(
        host="localhost",
        database="aprendizaje_db",
        user="usuario_learning",
        password="password_secreto",
        port="5432"
    )

# =====================================================================
# AC-04: LÓGICA DE DETECCIÓN DEL PUNTO DE RUPTURA (sin cambios)
# =====================================================================
def analizar_punto_ruptura(datos):
    resultado    = datos.get('resultado')
    paso_fallido = datos.get('paso_fallido')
    sentimiento  = datos.get('sentimiento_final')

    if resultado == "EXITOSO":
        return None  # Sin error — None es más limpio que "N/A"

    if paso_fallido == "transferencia_a_humano" and sentimiento == "NEGATIVO":
        return "FRUSTRACION_CLIENTE"
    elif paso_fallido in ["verificacion_pago_crm", "timeout_api", "conexion_base_datos"]:
        return "FALLO_INTEGRACION_TECNICA"
    elif paso_fallido == "intencion_no_reconocida":
        return "FALLO_ENTRENAMIENTO_NLP"
    else:
        return "CAUSA_DESCONOCIDA"

# =====================================================================
# INICIALIZACIÓN — Crear tabla si no existe
# =====================================================================
try:
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs_interacciones (
            id_interaccion      UUID PRIMARY KEY,
            modulo_origen       VARCHAR(50)  NOT NULL,
            fecha_interaccion   TIMESTAMP WITH TIME ZONE NOT NULL,
            resultado           VARCHAR(10)  NOT NULL,
            paso_fallido        VARCHAR(100),
            sentimiento_final   VARCHAR(10)  NOT NULL,
            texto_usuario       TEXT,
            respuesta_agente    TEXT,
            correccion_esperada TEXT,
            clasificacion_error VARCHAR(100),
            incluido_en_dataset BOOLEAN DEFAULT FALSE,
            fecha_captura       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print(" [✓] Conexión a PostgreSQL exitosa.", flush=True)
except Exception as e:
    print(f" [X] Error en PostgreSQL: {e}", flush=True)

# =====================================================================
# 2. CONFIGURACIÓN DE RABBITMQ
# =====================================================================
credenciales = pika.PlainCredentials('invitado', 'invitado_pass')
conexion     = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost', port=5672, credentials=credenciales)
)
canal = conexion.channel()
canal.queue_declare(queue='atencion_cliente_logs', durable=True)

print(" [*] Escuchando mensajes (AC-04 + AC-05). Para salir presiona CTRL+C...\n", flush=True)

# =====================================================================
# 3. RECEPCIÓN Y PROCESAMIENTO
# =====================================================================
def recibir_mensaje(ch, method, properties, body):
    try:
        datos = json.loads(body.decode('utf-8'))
        id_interaccion = datos.get('id_interaccion')
        print(f"\n[!] Procesando Interacción ID: {id_interaccion}", flush=True)

        # AC-04: Clasificar punto de ruptura
        clasificacion = analizar_punto_ruptura(datos)
        if datos.get('resultado') == "FALLIDO":
            print(f" 🔍 [PUNTO DE RUPTURA]: {clasificacion}", flush=True)
        else:
            print(" [✓] Interacción exitosa sin errores.", flush=True)

        # AC-05 prep: registrar texto si viene en el mensaje
        texto_usuario    = datos.get('texto_usuario')
        respuesta_agente = datos.get('respuesta_agente')
        if texto_usuario:
            print(f" 📝 Texto del usuario capturado: {texto_usuario[:60]}...", flush=True)

        # Guardar en PostgreSQL
        conn   = conectar_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO logs_interacciones (
                id_interaccion, modulo_origen, fecha_interaccion,
                resultado, paso_fallido, sentimiento_final,
                texto_usuario, respuesta_agente, clasificacion_error
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id_interaccion) DO NOTHING;
        """, (
            id_interaccion,
            datos.get('modulo_origen'),
            datos.get('timestamp'),
            datos.get('resultado'),
            datos.get('paso_fallido'),
            datos.get('sentimiento_final'),
            texto_usuario,
            respuesta_agente,
            clasificacion,
        ))
        conn.commit()
        cursor.close()
        conn.close()
        print(" [✓] Guardado en PostgreSQL con texto y clasificación.", flush=True)

    except Exception as error:
        print(f" [X] Error procesando mensaje: {error}", flush=True)

    ch.basic_ack(delivery_tag=method.delivery_tag)

canal.basic_consume(queue='atencion_cliente_logs', on_message_callback=recibir_mensaje)
canal.start_consuming()