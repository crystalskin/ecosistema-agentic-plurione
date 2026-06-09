import json
import pika
import os
from app.models.schemas import CognizeEvent

# Configuración de RabbitMQ (por defecto usa las de tu docker-compose)
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
EXCHANGE_NAME = "agentic_exchange"
ROUTING_KEY = "cognicion.evaluada"

class BrokerService:
    def __init__(self):
        self.connection = None
        self.channel = None

    def connect(self):
        """Establece la conexión con RabbitMQ"""
        credentials = pika.PlainCredentials('invitado', 'invitado_pass')
        parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # Declaramos el exchange (tipo 'topic' permite routing keys flexibles)
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)
        print(f"[*] Conectado a RabbitMQ en {RABBITMQ_HOST}")

    def publish_cognize_event(self, event: CognizeEvent):
        """Publica el evento de cognición en RabbitMQ"""
        if not self.connection or self.connection.is_closed:
            self.connect()

        # Convertimos el modelo de Pydantic a JSON string perfecto
        message_body = event.model_dump_json()

        self.channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=message_body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Hace el mensaje persistente (sobrevive si RabbitMQ se reinicia)
                content_type='application/json'
            )
        )
        print(f"[x] Evento publicado -> {ROUTING_KEY} | Event ID: {event.event_id}")

    def close(self):
        """Cierra la conexión de forma segura"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

# Instancia global para reutilizarla
broker_service = BrokerService()