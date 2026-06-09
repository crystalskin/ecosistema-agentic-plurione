import time
from app.models.schemas import CognizeEvent, MetadataData
from app.services.nlp_service import nlp_service
from app.services.broker_service import broker_service

def main():
    print("--- INICIO DE PRUEBA DINÁMICA CON IA ---")
    
    # Simulamos lo que un usuario le diría al chatbot
    texto_de_prueba = "Me cobraron dos veces por el mismo producto y estoy muy enojado, quiero mi dinero ya."
    session_id = "session-dinamica-001"
    
    print(f"\n[1] Texto recibido: '{texto_de_prueba}'")
    print("[2] Pasando texto por los modelos neuronales de HuggingFace...")
    print("    (Cargando modelos a memoria, espera unos segundos...)")
    
    start_time = time.time()
    
    # LA MAGIA: El modelo analiza el texto y devuelve el objeto Payload
    payload = nlp_service.analyze_text(texto_de_prueba, session_id)
    
    elapsed_time = round(time.time() - start_time, 2)
    
    print(f"\n    -> Análisis completado en {elapsed_time} segundos")
    print(f"    -> Intención detectada por IA: {payload.intent.label} (Confianza: {payload.intent.confidence})")
    print(f"    -> Sentimiento detectado por IA: {payload.sentiment.label} (Score: {payload.sentiment.score})")
    
    # 3. Armamos el evento final con los metadatos
    evento = CognizeEvent(
        session_id=session_id,
        payload=payload,
        metadata=MetadataData(
            model_intent_version="zero-shot-bart",
            model_sentiment_version="distilbert-sst2"
        )
    )
    
    print("\n[3] Publicando evento generado por IA en RabbitMQ...")
    try:
        broker_service.publish_cognize_event(evento)
        print("    -> ¡BOOM! El evento con predicciones reales de IA está en RabbitMQ.")
    except Exception as e:
        print(f"    -> ERROR al publicar: {e}")
    finally:
        broker_service.close()

    print("\n--- FIN DE PRUEBA ---")

if __name__ == "__main__":
    main()