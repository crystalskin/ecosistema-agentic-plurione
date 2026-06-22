import time
import uuid as uuid_lib
from datetime import datetime, timezone
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
        t_inicio = time.perf_counter()

        # 1. La IA piensa
        payload = nlp_service.analyze_text(text, session_id)
        t_nlp = time.perf_counter()

        # 2. Armamos el evento final
        evento = CognizeEvent(
            session_id=session_id,
            payload=payload,
            metadata=MetadataData(
                model_intent_version="zero-shot-bart",
                model_sentiment_version="distilbert-sst2"
            )
        )
        t_evento = time.perf_counter()

        # 3. Publicamos de forma asíncrona en RabbitMQ (para que el Módulo 7 lo lea después)
        broker_service.publish_cognize_event(evento)
        t_broker = time.perf_counter()

        print(
            f"[TIMING /cognize] "
            f"pipeline_nlp={t_nlp-t_inicio:.3f}s | "
            f"armar_evento={t_evento-t_nlp:.3f}s | "
            f"broker_rabbitmq={t_broker-t_evento:.3f}s | "
            f"TOTAL={t_broker-t_inicio:.3f}s"
        )

        # 4. Devolvemos la respuesta inmediatamente al cliente (NestJS/Frontend)
        return evento

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el motor de IA: {str(e)}")


@router.post("/escalate")
def publicar_escalamiento(body: dict):
    try:
        payload = {
            "event_id": str(uuid_lib.uuid4()),
            "event_type": "escalamiento_solicitado",
            "session_id": body.get("session_id"),
            "raw_text": body.get("raw_text"),
            "emotion": body.get("emotion"),
            "sentiment_score": body.get("sentiment_score"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        broker_service.publish_escalamiento_event(payload)
        return {"status": "publicado", "routing_key": "escalamiento.solicitado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al publicar escalamiento: {str(e)}")


@router.delete("/session/{session_id}")
def limpiar_sesion(session_id: str):
    nlp_service.limpiar_sesion(session_id)
    return {"status": "ok"}


@router.post("/clasificar-ticket")
def clasificar_ticket(body: dict):
    texto = (body.get("texto") or "").strip()
    if not texto:
        raise HTTPException(status_code=422, detail="El campo 'texto' es obligatorio.")
    try:
        resultado = nlp_service.clasificar_ticket(texto)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al clasificar ticket: {str(e)}")