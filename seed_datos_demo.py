#!/usr/bin/env python3
"""
seed_datos_demo.py — Inserta ~42 interacciones sintéticas en cognize_events.

Uso:
  python seed_datos_demo.py          Inserta los datos demo
  python seed_datos_demo.py --reset  Borra SOLO filas demo (session_id LIKE 'demo-%')
                                     NO toca interacciones reales (session-react-01, etc.)

Para identificar cuáles son demo, todas usan session_id con prefijo "demo-".
"""

import argparse
import uuid
import sys
import psycopg2
from datetime import datetime, timedelta

DB = dict(
    host="localhost",
    port=5432,
    dbname="aprendizaje_db",
    user="usuario_learning",
    password="password_secreto",
)

# Columnas: (raw_text, intent, confidence, sentiment, sentiment_score, emotion, generated_response, days_ago)
INTERACCIONES = [
    # --- SALUDOS (4, neutral) ---
    ("Hola, buenos días", "saludo", 0.9821, "neutral", 0.4213, "neutral",
     "¡Hola! Soy el asistente virtual de PluriOne. ¿En qué puedo ayudarte hoy?", 0),
    ("Buenas tardes, necesito ayuda", "saludo", 0.8743, "neutral", 0.3812, "neutral",
     "¡Hola! Soy el asistente virtual de PluriOne. ¿En qué puedo ayudarte hoy?", 1),
    ("Hola! ¿Cómo están?", "saludo", 0.9156, "neutral", 0.4501, "neutral",
     "¡Hola! Soy el asistente virtual de PluriOne. ¿En qué puedo ayudarte hoy?", 2),
    ("Buenas noches", "saludo", 0.9044, "neutral", 0.3924, "neutral",
     "¡Hola! Soy el asistente virtual de PluriOne. ¿En qué puedo ayudarte hoy?", 3),

    # --- DESPEDIDAS (3, neutral + positive) ---
    ("Gracias por la ayuda, hasta luego", "despedida", 0.8912, "positive", 0.7234, "satisfecho",
     "¡Gracias por contactarnos! Estamos a tu disposición cuando lo necesites. ¡Que tengas excelente día!", 0),
    ("Hasta pronto", "despedida", 0.9234, "neutral", 0.4123, "neutral",
     "¡Gracias por contactarnos! Estamos a tu disposición cuando lo necesites. ¡Que tengas excelente día!", 1),
    ("Muchas gracias, adiós", "despedida", 0.8765, "neutral", 0.4567, "neutral",
     "¡Gracias por contactarnos! Estamos a tu disposición cuando lo necesites. ¡Que tengas excelente día!", 4),

    # --- CONSULTA HORARIO (6, neutral + rag_directo) ---
    ("A qué hora abren?", "rag_directo", 0.9945, "neutral", 0.9945, "neutral",
     "¡Claro! Nuestro horario de atención al cliente es de lunes a viernes de 9:00 a.m. a 6:00 p.m. (hora de la Ciudad de México). ¿Puedo ayudarte en algo más?", 0),
    ("Cuál es el horario de atención?", "rag_directo", 0.9123, "neutral", 0.9123, "neutral",
     "¡Claro! Nuestro horario de atención al cliente es de lunes a viernes de 9:00 a.m. a 6:00 p.m. (hora de la Ciudad de México). ¿Puedo ayudarte en algo más?", 2),
    ("Qué días tienen servicio?", "consulta_horario", 0.4123, "neutral", 0.3567, "neutral",
     "Permíteme revisar esa información. ¿Podrías ser un poco más específico? Así te doy la respuesta exacta que necesitas.", 1),
    ("Atienden los sábados?", "consulta_horario", 0.3891, "neutral", 0.3234, "neutral",
     "Permíteme revisar esa información. ¿Podrías ser un poco más específico? Así te doy la respuesta exacta que necesitas.", 3),
    ("Horarios de atención por favor", "consulta_horario", 0.5234, "neutral", 0.4012, "neutral",
     "Permíteme revisar esa información. ¿Podrías ser un poco más específico? Así te doy la respuesta exacta que necesitas.", 5),
    ("Necesito saber el horario de cierre", "consulta_horario", 0.4567, "neutral", 0.3891, "neutral",
     "Permíteme revisar esa información. ¿Podrías ser un poco más específico? Así te doy la respuesta exacta que necesitas.", 6),

    # --- CONSULTA DIRECCION (4, neutral) ---
    ("Dónde están ubicados?", "consulta_direccion", 0.6823, "neutral", 0.4234, "neutral",
     "¡Claro! Estamos ubicados en Puebla 46, Colonia Roma Norte, Alcaldía Cuauhtémoc, C.P. 06700, CDMX. ¿Te puedo ayudar en algo más?", 0),
    ("Cuál es la dirección?", "consulta_direccion", 0.7234, "neutral", 0.4567, "neutral",
     "¡Claro! Estamos ubicados en Puebla 46, Colonia Roma Norte, Alcaldía Cuauhtémoc, C.P. 06700, CDMX. ¿Te puedo ayudar en algo más?", 2),
    ("En qué ciudad tienen oficinas?", "consulta_direccion", 0.5678, "neutral", 0.3901, "neutral",
     "¡Claro! Estamos ubicados en Puebla 46, Colonia Roma Norte, Alcaldía Cuauhtémoc, C.P. 06700, CDMX. ¿Te puedo ayudar en algo más?", 4),
    ("Cómo llego a sus instalaciones?", "consulta_direccion", 0.6012, "neutral", 0.4123, "neutral",
     "¡Claro! Estamos ubicados en Puebla 46, Colonia Roma Norte, Alcaldía Cuauhtémoc, C.P. 06700, CDMX. ¿Te puedo ayudar en algo más?", 5),

    # --- INFORMACION GENERAL (5, neutral) ---
    ("Qué servicios ofrecen?", "informacion_general", 0.7234, "neutral", 0.4345, "neutral",
     "Permíteme revisar esa información. ¿Podrías ser un poco más específico? Así te doy la respuesta exacta que necesitas.", 1),
    ("Información sobre sus productos", "informacion_general", 0.6891, "neutral", 0.4012, "neutral",
     "Permíteme revisar esa información. ¿Podrías ser un poco más específico? Así te doy la respuesta exacta que necesitas.", 2),
    ("Tienen planes empresariales?", "informacion_general", 0.6345, "neutral", 0.3901, "neutral",
     "Permíteme revisar esa información. ¿Podrías ser un poco más específico? Así te doy la respuesta exacta que necesitas.", 3),
    ("Cómo puedo contratar sus servicios?", "informacion_general", 0.5901, "neutral", 0.4234, "neutral",
     "Permíteme revisar esa información. ¿Podrías ser un poco más específico? Así te doy la respuesta exacta que necesitas.", 4),
    ("Quiero saber más sobre PluriOne", "informacion_general", 0.6789, "neutral", 0.4456, "neutral",
     "Permíteme revisar esa información. ¿Podrías ser un poco más específico? Así te doy la respuesta exacta que necesitas.", 6),

    # --- CONSULTA ESTADO ORDEN (4, neutral + negative) ---
    ("En qué estado está mi pedido?", "consulta_estado_orden", 0.7891, "neutral", 0.4234, "neutral",
     "Permíteme revisar esa información. ¿Podrías ser un poco más específico? Así te doy la respuesta exacta que necesitas.", 1),
    ("Cuándo llega mi paquete?", "consulta_estado_orden", 0.8123, "neutral", 0.4567, "neutral",
     "Permíteme revisar esa información. ¿Podrías ser un poco más específico? Así te doy la respuesta exacta que necesitas.", 3),
    ("Llevan 5 días y no llega mi orden", "consulta_estado_orden", 0.7234, "negative", 0.5891, "frustracion",
     "Lamento muchísimo el inconveniente. Entiendo tu molestia y quiero ayudarte a resolverlo cuanto antes. ¿Podrías darme más detalles de lo sucedido? Si prefieres, te comunico de inmediato con un agente humano.", 2),
    ("Mi pedido no aparece en el sistema", "consulta_estado_orden", 0.6891, "negative", 0.5234, "insatisfecho",
     "Siento que estés pasando por esto. Cuéntame un poco más para entender mejor tu situación y encontrar una solución. Si lo deseas, puedo transferirte con un agente humano.", 5),

    # --- PROBLEMA TARJETA BANCARIA (5, negative + neutral) ---
    ("Perdí mi tarjeta, qué hago", "problema_tarjeta_bancaria", 0.8500, "negative", 0.5243, "frustracion",
     "Lamento muchísimo el inconveniente. Entiendo tu molestia y quiero ayudarte a resolverlo cuanto antes. ¿Podrías darme más detalles de lo sucedido? Si prefieres, te comunico de inmediato con un agente humano.", 0),
    ("Me robaron la tarjeta", "problema_tarjeta_bancaria", 0.8900, "negative", 0.7012, "frustracion",
     "Lamento muchísimo el inconveniente. Entiendo tu molestia y quiero ayudarte a resolverlo cuanto antes. ¿Podrías darme más detalles de lo sucedido? Si prefieres, te comunico de inmediato con un agente humano.", 1),
    ("Mi tarjeta no funciona para pagar", "problema_tarjeta_bancaria", 0.8234, "negative", 0.5678, "insatisfecho",
     "Entiendo que tienes una dificultad. ¿Podrías darme más detalles sobre lo que sucede? Así puedo orientarte mejor o, si lo prefieres, comunicarte con un agente humano.", 3),
    ("Bloquearon mi tarjeta sin avisarme", "problema_tarjeta_bancaria", 0.7891, "negative", 0.6234, "frustracion",
     "Lamento muchísimo el inconveniente. Entiendo tu molestia y quiero ayudarte a resolverlo cuanto antes. ¿Podrías darme más detalles de lo sucedido? Si prefieres, te comunico de inmediato con un agente humano.", 4),
    ("Cómo solicito una tarjeta nueva?", "problema_tarjeta_bancaria", 0.7234, "neutral", 0.4123, "neutral",
     "Entiendo que tienes una dificultad. ¿Podrías darme más detalles sobre lo que sucede? Así puedo orientarte mejor o, si lo prefieres, comunicarte con un agente humano.", 6),

    # --- QUEJA COBRO DUPLICADO (4, negative) ---
    ("Me cobraron dos veces el mismo mes", "queja_cobro_duplicado", 0.8901, "negative", 0.7123, "frustracion",
     "Lamento muchísimo el inconveniente. Entiendo tu molestia y quiero ayudarte a resolverlo cuanto antes. ¿Podrías darme más detalles de lo sucedido? Si prefieres, te comunico de inmediato con un agente humano.", 1),
    ("Hay un cobro que no reconozco", "queja_cobro_duplicado", 0.8234, "negative", 0.6234, "insatisfecho",
     "Siento que estés pasando por esto. Cuéntame un poco más para entender mejor tu situación y encontrar una solución. Si lo deseas, puedo transferirte con un agente humano.", 2),
    ("Cobro duplicado en mi cuenta este mes", "queja_cobro_duplicado", 0.9012, "negative", 0.7456, "frustracion",
     "Lamento muchísimo el inconveniente. Entiendo tu molestia y quiero ayudarte a resolverlo cuanto antes. ¿Podrías darme más detalles de lo sucedido? Si prefieres, te comunico de inmediato con un agente humano.", 4),
    ("Me descontaron de más esta semana", "queja_cobro_duplicado", 0.8567, "negative", 0.6789, "insatisfecho",
     "Siento que estés pasando por esto. Cuéntame un poco más para entender mejor tu situación y encontrar una solución. Si lo deseas, puedo transferirte con un agente humano.", 5),

    # --- FALLO TECNICO (4, negative + neutral) ---
    ("La app no carga", "fallo_tecnico", 0.7891, "negative", 0.5234, "insatisfecho",
     "Entiendo que tienes una dificultad. ¿Podrías darme más detalles sobre lo que sucede? Así puedo orientarte mejor o, si lo prefieres, comunicarte con un agente humano.", 0),
    ("Error al intentar pagar en línea", "fallo_tecnico", 0.8234, "negative", 0.5891, "frustracion",
     "Lamento muchísimo el inconveniente. Entiendo tu molestia y quiero ayudarte a resolverlo cuanto antes. ¿Podrías darme más detalles de lo sucedido? Si prefieres, te comunico de inmediato con un agente humano.", 2),
    ("El sistema está caído?", "fallo_tecnico", 0.7012, "neutral", 0.4234, "neutral",
     "Entiendo que tienes una dificultad. ¿Podrías darme más detalles sobre lo que sucede? Así puedo orientarte mejor o, si lo prefieres, comunicarte con un agente humano.", 3),
    ("No puedo acceder a mi cuenta", "fallo_tecnico", 0.8567, "negative", 0.6123, "frustracion",
     "Lamento muchísimo el inconveniente. Entiendo tu molestia y quiero ayudarte a resolverlo cuanto antes. ¿Podrías darme más detalles de lo sucedido? Si prefieres, te comunico de inmediato con un agente humano.", 6),

    # --- SOLICITUD REEMBOLSO (3, negative + positive) ---
    ("Quiero que me devuelvan mi dinero", "solicitud_reembolso", 0.8901, "negative", 0.7234, "frustracion",
     "Lamento muchísimo el inconveniente. Entiendo tu molestia y quiero ayudarte a resolverlo cuanto antes. ¿Podrías darme más detalles de lo sucedido? Si prefieres, te comunico de inmediato con un agente humano.", 1),
    ("Necesito reembolso por cargo incorrecto", "solicitud_reembolso", 0.8456, "negative", 0.6567, "insatisfecho",
     "Siento que estés pasando por esto. Cuéntame un poco más para entender mejor tu situación y encontrar una solución. Si lo deseas, puedo transferirte con un agente humano.", 3),
    ("Ya me hicieron el reembolso, gracias", "solicitud_reembolso", 0.7234, "positive", 0.6789, "satisfecho",
     "¡Gracias por contactarnos! Estamos a tu disposición cuando lo necesites. ¡Que tengas excelente día!", 5),
]


def main():
    parser = argparse.ArgumentParser(
        description="Seed de datos demo para cognize_events."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Borra SOLO las filas demo (session_id LIKE 'demo-%%'). NO toca interacciones reales.",
    )
    args = parser.parse_args()

    try:
        conn = psycopg2.connect(**DB)
    except psycopg2.OperationalError as e:
        print(f"ERROR: No se pudo conectar a PostgreSQL. ¿Está corriendo Docker?\n{e}", file=sys.stderr)
        sys.exit(1)

    cur = conn.cursor()

    if args.reset:
        cur.execute("DELETE FROM cognize_events WHERE session_id LIKE 'demo-%'")
        deleted = cur.rowcount
        conn.commit()
        conn.close()
        print(f"Eliminadas {deleted} filas demo. Las interacciones reales no fueron tocadas.")
        return

    now = datetime.utcnow()
    inserted = 0

    for i, (raw, intent, conf, sent, sscore, emo, resp, days_ago) in enumerate(INTERACCIONES):
        ts = now - timedelta(days=days_ago, hours=i % 8, minutes=(i * 7) % 60)
        cur.execute(
            """
            INSERT INTO cognize_events
              (event_id, session_id, timestamp, raw_text, intent, intent_confidence,
               sentiment, sentiment_score, emotion, generated_response)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                str(uuid.uuid4()),
                f"demo-{i // 6:02d}",
                ts,
                raw,
                intent,
                conf,
                sent,
                sscore,
                emo,
                resp,
            ),
        )
        inserted += cur.rowcount

    conn.commit()
    conn.close()
    print(f"Insertadas {inserted} filas demo en cognize_events.")
    print(f"Para borrarlas después: python seed_datos_demo.py --reset")


if __name__ == "__main__":
    main()
