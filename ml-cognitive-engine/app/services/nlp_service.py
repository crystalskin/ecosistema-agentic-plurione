import time
from transformers import pipeline
from app.models.schemas import PayloadData, IntentData, SentimentData
from app.services.llm_service import llm_service
from app.services.retriever_service import retriever_service

RAG_SHORTCIRCUIT_THRESHOLD = 0.90

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
        t0 = time.perf_counter()

        # CORTOCIRCUITO: si el FAQ responde con alta confianza, omite BERT + BART
        faq_rapido, rag_score = retriever_service.search(raw_text, threshold=RAG_SHORTCIRCUIT_THRESHOLD)
        if faq_rapido is not None:
            print(f"[SHORTCIRCUIT] score={rag_score:.3f} → BERT+BART omitidos | total={time.perf_counter()-t0:.3f}s")
            return PayloadData(
                raw_text=raw_text,
                intent=IntentData(label="rag_directo", confidence=round(rag_score, 4)),
                sentiment=SentimentData(label="neutral", score=round(rag_score, 4), emotion="neutral"),
                generated_response=f"¡Claro! {faq_rapido} ¿Puedo ayudarte en algo más?",
            )

        # 1. Sentimiento
        t_bert0 = time.perf_counter()
        sent_result = self.sentiment_analyzer(raw_text)[0]
        t_bert1 = time.perf_counter()
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
        t_bart0 = time.perf_counter()
        intent_result = self.intent_classifier(raw_text, self.intents_labels)
        t_bart1 = time.perf_counter()
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
        t_llm0 = time.perf_counter()
        response = llm_service.generate_response(raw_text, top_intent, sentiment_label)
        t_llm1 = time.perf_counter()

        print(
            f"[TIMING NLP] "
            f"bert_sentiment={t_bert1-t_bert0:.3f}s | "
            f"bart_intent={t_bart1-t_bart0:.3f}s | "
            f"llm_rag={t_llm1-t_llm0:.3f}s | "
            f"total_nlp={t_llm1-t0:.3f}s"
        )

        return PayloadData(
            raw_text=raw_text,
            intent=intent_data,
            sentiment=sentiment_data,
            generated_response=response
        )

    def clasificar_ticket(self, texto: str) -> dict:
        """Categoría via BART (frases descriptivas en inglés) + prioridad por categoría."""

        # Frases descriptivas en inglés → mejor precisión en BART (modelo inglés)
        # El texto de entrada puede ser español — el NLI mapea semánticamente igual
        MAPA_ETIQUETAS = {
            "charged twice, double charge, billing error, wrong amount billed, invoice issue, or refund request": "facturacion",
            "technical issue, app not working, system failure, or payment error":  "soporte_tecnico",
            "login problem, password reset, blocked account, or access issue":     "cuenta_acceso",
            "lost, stolen, or blocked card, or request for a new card":            "tarjeta_bancaria",
            "order tracking, delivery status, or shipment inquiry":                "estado_pedido",
            "complaint about poor service or negative customer experience":        "queja_general",
            "asking about business hours, opening times, schedules, branch location, or address": "informacion_general",
            "other request not classified above":                                  "otros",
        }

        # Prioridad determinista por categoría — más fiable que BERT en texto de soporte
        PRIORIDAD_CATEGORIA = {
            "facturacion":         "alta",
            "tarjeta_bancaria":    "alta",
            "queja_general":       "alta",
            "soporte_tecnico":     "media",
            "cuenta_acceso":       "media",
            "estado_pedido":       "media",
            "informacion_general": "baja",
            "otros":               "baja",
        }

        etiquetas = list(MAPA_ETIQUETAS.keys())
        resultado = self.intent_classifier(texto, etiquetas)
        etiqueta_ganadora = resultado['labels'][0]
        categoria = MAPA_ETIQUETAS[etiqueta_ganadora]
        confianza = round(resultado['scores'][0], 4)
        prioridad = PRIORIDAD_CATEGORIA[categoria]

        return {
            "categoria": categoria,
            "confianza": confianza,
            "prioridad": prioridad,
        }

nlp_service = NLPService()