import json
import pika
import os

# --- CONFIGURACIÓN ---
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
# ⚠️ PON AQUÍ LAS CREDENCIALES QUE USASTE AYER EN broker_service.py
RABBITMQ_USER = "invitado" 
RABBITMQ_PASS = "invitado_pass" 

EXCHANGE_NAME = "agentic_exchange"
ROUTING_KEY = "cognicion.evaluada"

def callback_cognicion(ch, method, properties, body):
    """Se ejecuta automáticamente cuando llega un evento del motor de IA"""
    print("\n" + "="*60)
    print("🔔 [MÓDULO 7] ¡EVENTO RECIBIDO DEL MOTOR COGNITIVO!")
    print("="*60)
    
    # Decodificamos el JSON que envió FastAPI
    event = json.loads(body)
    
    # Extraemos los datos que le interesan al Módulo 7
    texto = event.get('payload', {}).get('raw_text', 'No text')
    intencion = event.get('payload', {}).get('intent', {}).get('label', 'Desconocida')
    sentimiento = event.get('payload', {}).get('sentiment', {}).get('label', 'Desconocido')
    score = event.get('payload', {}).get('sentiment', {}).get('score', 0.0)
    
    # Simulamos lo que haría el Módulo 7 con esta información
    print(f"💬 Texto del usuario: '{texto}'")
    print(f"🧠 Intención detectada: {intencion}")
    print(f"❤️  Sentimiento: {sentimiento} (Score: {score})")
    print(f"📋 Si el sentimiento es 'negative', el Módulo 7 lo guardaría para re-entrenar.")
    print("="*60 + "\n")
    
    # Le decimos a RabbitMQ que ya procesamos el mensaje
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    print("🚀 Iniciando puente de cognición hacia el Módulo 7...")
    
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
    channel = connection.channel()

    # 1. Nos conectamos al MISMO exchange que creó tu motor de IA ayer
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)

    # 2. Creamos una cola temporal para este puente
    result = channel.queue_declare(queue='modulo7_puente_cognicion', durable=True)
    queue_name = result.method.queue

    # 3. Ligamos esa cola al routing key 'cognicion.evaluada'
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=ROUTING_KEY)

    print(f"[*] Escuchando eventos de IA en: {ROUTING_KEY}")
    print(f"[*] Esperando... (Presiona CTRL+C para detener)\n")

    channel.basic_consume(queue=queue_name, on_message_callback=callback_cognicion)
    channel.start_consuming()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Puente detenido manualmente.")