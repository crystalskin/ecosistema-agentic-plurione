# Contrato de Integración - Módulo 7 (Sistema de Aprendizaje Continuo)

## Mecanismo de Comunicación
* **Tecnología:** RabbitMQ (Asíncrono)
* **Nombre de la Cola:** `atencion_cliente_logs`

## Estructura del Mensaje (JSON)
Cada vez que un módulo finalice una interacción o detecte un fallo, deberá publicar un mensaje en la cola con la siguiente estructura exacta:

```json
{
  "id_interaccion": "string (UUID)",
  "modulo_origen": "string (chatbot | resolutor | sentimiento)",
  "timestamp": "string (ISO 8601)",
  "resultado": "string (EXITOSO | FALLIDO)",
  "paso_fallido": "string o null",
  "sentimiento_final": "string (POSITIVO | NEUTRAL | NEGATIVO)"
}