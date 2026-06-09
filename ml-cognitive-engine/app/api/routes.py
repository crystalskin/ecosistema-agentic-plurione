from fastapi import APIRouter, HTTPException
from app.models.schemas import CognizeEvent, MetadataData
from app.services.nlp_service import nlp_service
from app.services.broker_service import broker_service

router = APIRouter(prefix="/api/v1", tags=["Cognitive Engine"])

# NOTA DE ARQUITECTURA: Usamos `def` en lugar de `async def` porque la inferencia
# de modelos de ML (PyTorch) bloquea el hilo. FastAPI es lo suficientemente inteligente
# para ejecutar funciones `def` normales en un hilo separado (Threadpool), 
# evitando que se bloquee todo el servidor mientras piensa la IA.
@router.post("/cognize", response_model=CognizeEvent)
def process_cognize_event(text: str, session_id: str):
    try:
        # 1. La IA piensa
        payload = nlp_service.analyze_text(text, session_id)
        
        # 2. Armamos el evento final
        evento = CognizeEvent(
            session_id=session_id,
            payload=payload,
            metadata=MetadataData(
                model_intent_version="zero-shot-bart",
                model_sentiment_version="distilbert-sst2"
            )
        )
        
        # 3. Publicamos de forma asíncrona en RabbitMQ (para que el Módulo 7 lo lea después)
        broker_service.publish_cognize_event(evento)
        
        # 4. Devolvemos la respuesta inmediatamente al cliente (NestJS/Frontend)
        return evento

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el motor de IA: {str(e)}")