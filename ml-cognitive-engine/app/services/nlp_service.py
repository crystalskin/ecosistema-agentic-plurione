from transformers import pipeline
from app.models.schemas import PayloadData, IntentData, SentimentData

class NLPService:
    def __init__(self):
        print("[NLP] Cargando modelos de HuggingFace (Puede tardar unos segundos la primera vez)...")
        
        # Modelo para análisis de sentimiento (liviano y rápido)
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis", 
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        
        # Modelo Zero-Shot para detectar intenciones sin estar entrenado específicamente
        # Le definimos las posibles intenciones de nuestro negocio
        self.intents_labels = [
            "queja_cobro_duplicado",
            "consulta_estado_orden",
            "solicitud_reembolso",
            "saludo",
            "despedida",
            "informacion_general"
        ]
        self.intent_classifier = pipeline(
            "zero-shot-classification", 
            model="facebook/bart-large-mnli"
        )
        print("[NLP] Modelos cargados y listos.")

    def analyze_text(self, raw_text: str, session_id: str) -> PayloadData:
        """Analiza el texto y devuelve el objeto Payload estructurado"""
        
        # 1. Analizar Sentimiento
        sent_result = self.sentiment_analyzer(raw_text)[0]
        sentiment_label = "positive" if sent_result['label'] == 'POSITIVE' else "negative"
        
        sentiment_data = SentimentData(
            label=sentiment_label,
            score=round(sent_result['score'], 4),
            emotion="frustracion" if sentiment_label == "negative" else "neutral" # Lógica simple por ahora
        )

        # 2. Analizar Intención (Zero-Shot)
        intent_result = self.intent_classifier(raw_text, self.intents_labels)
        top_intent = intent_result['labels'][0]
        intent_confidence = round(intent_result['scores'][0], 4)

        intent_data = IntentData(
            label=top_intent,
            confidence=intent_confidence
        )

        # 3. Construir y devolver el Payload
        payload = PayloadData(
            raw_text=raw_text,
            intent=intent_data,
            sentiment=sentiment_data
        )
        
        return payload

# Instancia global
nlp_service = NLPService()