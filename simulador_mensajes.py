"""
simulador_mensajes.py — Inyecta datos de prueba realistas con texto

Úsalo para llenar tu base de datos con interacciones que tengan
texto_usuario y respuesta_agente, necesarios para el dataset AC-05.

Corre con: python simulador_mensajes.py
"""

import pika
import json
import uuid
from datetime import datetime, timezone

# ── Datos de prueba realistas ────────────────────────────────────
MENSAJES_PRUEBA = [
    # Interacciones EXITOSAS (ejemplos positivos para el dataset)
    {
        "modulo_origen": "chatbot",
        "resultado": "EXITOSO",
        "paso_fallido": None,
        "sentimiento_final": "POSITIVO",
        "texto_usuario": "Hola, quiero saber el saldo de mi cuenta",
        "respuesta_agente": "Claro, tu saldo actual es de $1,250.00 MXN. ¿Necesitas algo más?"
    },
    {
        "modulo_origen": "chatbot",
        "resultado": "EXITOSO",
        "paso_fallido": None,
        "sentimiento_final": "POSITIVO",
        "texto_usuario": "¿Cuál es el horario de atención?",
        "respuesta_agente": "Nuestro horario es de lunes a viernes de 9:00 a 18:00 horas."
    },
    {
        "modulo_origen": "resolutor",
        "resultado": "EXITOSO",
        "paso_fallido": None,
        "sentimiento_final": "NEUTRAL",
        "texto_usuario": "Necesito cancelar mi suscripción del plan básico",
        "respuesta_agente": "Tu suscripción al plan básico ha sido cancelada exitosamente. Recibirás un correo de confirmación."
    },
    {
        "modulo_origen": "chatbot",
        "resultado": "EXITOSO",
        "paso_fallido": None,
        "sentimiento_final": "POSITIVO",
        "texto_usuario": "¿Cómo puedo cambiar mi contraseña?",
        "respuesta_agente": "Puedes cambiar tu contraseña en Configuración > Seguridad > Cambiar contraseña. ¿Te ayudo con algo más?"
    },
    {
        "modulo_origen": "resolutor",
        "resultado": "EXITOSO",
        "paso_fallido": None,
        "sentimiento_final": "POSITIVO",
        "texto_usuario": "Quiero actualizar mi dirección de envío",
        "respuesta_agente": "Tu dirección de envío ha sido actualizada. Los cambios aplican a partir de tu próximo pedido."
    },
    # Interacciones FALLIDAS (para clasificar y corregir en el dataset)
    {
        "modulo_origen": "chatbot",
        "resultado": "FALLIDO",
        "paso_fallido": "intencion_no_reconocida",
        "sentimiento_final": "NEUTRAL",
        "texto_usuario": "Oye quiero hacer lo del trámite ese que me dijeron",
        "respuesta_agente": "Lo siento, no entendí tu solicitud. ¿Podrías ser más específico?"
    },
    {
        "modulo_origen": "chatbot",
        "resultado": "FALLIDO",
        "paso_fallido": "intencion_no_reconocida",
        "sentimiento_final": "NEGATIVO",
        "texto_usuario": "Ya te dije que quiero hablar con alguien de verdad no con un robot",
        "respuesta_agente": "Disculpa, no entendí tu solicitud. Por favor intenta de nuevo."
    },
    {
        "modulo_origen": "resolutor",
        "resultado": "FALLIDO",
        "paso_fallido": "verificacion_pago_crm",
        "sentimiento_final": "NEUTRAL",
        "texto_usuario": "¿Ya se aplicó mi pago de ayer?",
        "respuesta_agente": "Error al consultar el sistema de pagos. Por favor intenta más tarde."
    },
    {
        "modulo_origen": "resolutor",
        "resultado": "FALLIDO",
        "paso_fallido": "timeout_api",
        "sentimiento_final": "NEGATIVO",
        "texto_usuario": "Quiero ver mi historial de compras del último mes",
        "respuesta_agente": "No se pudo conectar con el servidor. Intenta de nuevo en unos minutos."
    },
    {
        "modulo_origen": "chatbot",
        "resultado": "FALLIDO",
        "paso_fallido": "transferencia_a_humano",
        "sentimiento_final": "NEGATIVO",
        "texto_usuario": "Esto es un desastre, llevan 3 días sin resolver mi problema y nadie me hace caso",
        "respuesta_agente": "Entiendo tu frustración, te transfiero con un agente humano."
    },
]

def publicar_mensajes():
    credenciales = pika.PlainCredentials('invitado', 'invitado_pass')
    conexion     = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost', port=5672, credentials=credenciales)
    )
    canal = conexion.channel()
    canal.queue_declare(queue='atencion_cliente_logs', durable=True)

    print(f"📤 Publicando {len(MENSAJES_PRUEBA)} mensajes de prueba...\n")

    for i, base in enumerate(MENSAJES_PRUEBA, 1):
        mensaje = {
            "id_interaccion": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **base
        }

        canal.basic_publish(
            exchange='',
            routing_key='atencion_cliente_logs',
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(delivery_mode=2)  # persistente
        )

        tipo  = "✅ EXITOSO" if base["resultado"] == "EXITOSO" else "❌ FALLIDO"
        texto = base["texto_usuario"][:50]
        print(f"  [{i:02d}] {tipo} | {base['modulo_origen']:10s} | {texto}...")

    conexion.close()
    print(f"\n✅ {len(MENSAJES_PRUEBA)} mensajes enviados a RabbitMQ.")
    print("   Asegúrate de que consumidor_v2.py esté corriendo para procesarlos.")

if __name__ == "__main__":
    publicar_mensajes()