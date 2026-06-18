from transformers import pipeline
from app.models.schemas import PayloadData, IntentData, SentimentData
from app.services.llm_service import llm_service

class NLPService:
    def __init__(self):
        print("[NLP] Cargando modelos optimizados para español...")
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment"
        )
        self.intents_labels = [
            "queja_cobro_duplicado",
            "problema_tarjeta_bancaria",
            "fallo_tecnico",
            "solicitud_reembolso",
            "consulta_estado_orden",
            "consulta_horario",
            "consulta_direccion",
            "saludo",
            "despedida",
            "informacion_general"
        ]
        self.intent_classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        print("[NLP] Modelos listos.")

    def analyze_text(self, raw_text: str, session_id: str) -> PayloadData:
        # 1. Sentimiento
        sent_result = self.sentiment_analyzer(raw_text)[0]
        stars = int(sent_result['label'][0])

        if stars <= 1:
            sentiment_label = "negative"
            emotion = "frustracion"
        elif stars == 2:
            if sent_result['score'] > 0.8:
                sentiment_label = "negative"
                emotion = "insatisfecho"
            else:
                sentiment_label = "neutral"
                emotion = "neutral"
        elif stars == 3:
            sentiment_label = "neutral"
            emotion = "neutral"
        else:
            sentiment_label = "positive"
            emotion = "satisfecho"

        # 2. Intención Zero-Shot
        intent_result = self.intent_classifier(raw_text, self.intents_labels)
        top_intent = intent_result['labels'][0]
        intent_confidence = round(intent_result['scores'][0], 4)

        # --- CORRECCIÓN: evitar que frases con "tarjeta/problema" sean "despedida" ---
        if ("tarjeta" in raw_text.lower() or "problema" in raw_text.lower()) and top_intent == "despedida":
            top_intent = "problema_tarjeta_bancaria"
            intent_confidence = 0.85

        # 3. Forzar neutral si es consulta informativa
        if top_intent in ["consulta_horario", "consulta_direccion", "informacion_general"]:
            sentiment_label = "neutral"
            emotion = "neutral"

        sentiment_data = SentimentData(
            label=sentiment_label,
            score=round(sent_result['score'], 4),
            emotion=emotion
        )

        intent_data = IntentData(
            label=top_intent,
            confidence=intent_confidence
        )

        # 4. Generar respuesta (híbrida)
        response = llm_service.generate_response(raw_text, top_intent, sentiment_label)

        return PayloadData(
            raw_text=raw_text,
            intent=intent_data,
            sentiment=sentiment_data,
            generated_response=response
        )

nlp_service = NLPService()