"""
consumidor.py — VERSIÓN FINAL para el ecosistema Agentic completo.
Recibe eventos CognizeEvent (estructura anidada) desde agentic_exchange,
los transforma al formato legado de la tabla logs_interacciones,
y los guarda en PostgreSQL para el módulo de aprendizaje continuo.
"""

import pika
import json
import psycopg2
from datetime import datetime
from uuid import UUID

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
# 2. DETECCIÓN DEL PUNTO DE RUPTURA (adaptado al nuevo esquema)
# =====================================================================
def analizar_punto_ruptura(resultado, intent, sentiment):
    if resultado == "EXITOSO":
        return None

    # Fallos según el contexto actual (no hay 'paso_fallido' explícito)
    emotion = sentiment.get('emotion')
    if emotion and 'frustracion' in emotion.lower():
        return "FRUSTRACION_CLIENTE"
    elif intent.get('confidence', 1.0) < 0.5:
        return "FALLO_ENTRENAMIENTO_NLP"
    else:
        return "CAUSA_DESCONOCIDA"

# =====================================================================
# 3. PREPARACIÓN DE LA BASE DE DATOS
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
# 4. CONFIGURACIÓN DE RABBITMQ (exchange tal cual lo define FastAPI)
# =====================================================================
EXCHANGE_NAME = "agentic_exchange"
QUEUE_NAME    = "atencion_cliente_logs"
BINDING_KEY   = "cognicion.#"   # captura 'cognicion.evaluada' y derivados

credenciales = pika.PlainCredentials('invitado', 'invitado_pass')
conexion     = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost', port=5672, credentials=credenciales)
)
canal = conexion.channel()
canal.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)
canal.queue_declare(queue=QUEUE_NAME, durable=True)
canal.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=BINDING_KEY)
print(f" [*] Conectado a '{EXCHANGE_NAME}' con binding '{BINDING_KEY}'. Esperando mensajes...", flush=True)

# =====================================================================
# 5. PROCESAMIENTO DE MENSAJES (ahora con el esquema CognizeEvent)
# =====================================================================
def recibir_mensaje(ch, method, properties, body):
    try:
        datos = json.loads(body.decode('utf-8'))
        event_id = datos.get('event_id')        # UUID
        session  = datos.get('session_id')
        payload  = datos.get('payload', {})
        timestamp = datos.get('timestamp')

        # Extraer los datos planos que necesita la tabla
        texto_usuario    = payload.get('raw_text')
        intent           = payload.get('intent', {})
        sentiment        = payload.get('sentiment', {})
        respuesta_agente = payload.get('generated_response')

        # Derivar 'resultado': EXITOSO si hay respuesta generada y no es vacía
        if respuesta_agente and respuesta_agente.strip():
            resultado = "EXITOSO"
        else:
            resultado = "FALLIDO"

        # Sentimiento plano para la columna
        sentimiento_label = sentiment.get('label', 'NEUTRAL').upper()

        print(f"\n[!] Procesando evento {event_id} | Sesión: {session}", flush=True)

        # Clasificación del error
        clasificacion = analizar_punto_ruptura(resultado, intent, sentiment)
        if resultado == "FALLIDO":
            print(f" 🔍 [PUNTO DE RUPTURA]: {clasificacion}", flush=True)

        if texto_usuario:
            print(f" 📝 Texto: {texto_usuario[:60]}...", flush=True)

        # Guardar en PostgreSQL con el formato heredado
        conn = conectar_db()
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
            event_id,
            'cognicion',                  # módulo_origen fijo para este flujo
            timestamp,
            resultado,
            None,                         # ya no tenemos paso_fallido explícito
            sentimiento_label,
            texto_usuario,
            respuesta_agente,
            clasificacion,
        ))
        conn.commit()
        cursor.close()
        conn.close()
        print(" [✓] Guardado en PostgreSQL.", flush=True)

    except Exception as error:
        print(f" [X] Error: {error}", flush=True)

    ch.basic_ack(delivery_tag=method.delivery_tag)

canal.basic_consume(queue=QUEUE_NAME, on_message_callback=recibir_mensaje)
canal.start_consuming()