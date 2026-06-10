from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

# --- Sub-modelos (Anidados) ---

class IntentData(BaseModel):
    label: str = Field(..., description="Ej: queja_cobro_duplicado, consulta_estado, saludo")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Probabilidad de 0 a 1")

class SentimentData(BaseModel):
    label: str = Field(..., description="Ej: positive, negative, neutral")
    score: float = Field(..., ge=0.0, le=1.0, description="Intensidad del sentimiento")
    emotion: Optional[str] = Field(None, description="Ej: frustracion, alegría, enojo")

class PayloadData(BaseModel):
    raw_text: str = Field(..., min_length=1, description="Texto original del usuario")
    intent: IntentData
    sentiment: SentimentData
    generated_response: Optional[str] = Field(None, description="Respuesta generada por el LLM")

class MetadataData(BaseModel):
    model_intent_version: str = Field(..., description="Ej: intent-v1")
    model_sentiment_version: str = Field(..., description="Ej: sentiment-v1")

# --- Modelo Principal (El evento completo) ---

class CognizeEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4, description="ID único autogenerado")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Fecha ISO 8601")
    session_id: str = Field(..., description="Identificador de la conversación")
    payload: PayloadData
    metadata: MetadataData

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "timestamp": "2024-05-20T14:32:00Z",
                "session_id": "session-123",
                "payload": {
                    "raw_text": "¡Me cobraron dos veces!",
                    "intent": {"label": "queja_cobro_duplicado", "confidence": 0.94},
                    "sentiment": {"label": "negative", "score": 0.89, "emotion": "frustracion"}
                },
                "metadata": {
                    "model_intent_version": "intent-v1",
                    "model_sentiment_version": "sentiment-v1"
                }
            }
        }