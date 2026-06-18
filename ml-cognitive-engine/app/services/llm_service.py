import time
from app.services.retriever_service import retriever_service

class LLMService:
    """
    Servicio híbrido: usa el RAG como fuente de verdad y plantillas
    empáticas cuando no hay información en la base de conocimiento.
    """

    def __init__(self):
        print("[HybridAgent] Modo híbrido activado (RAG + plantillas).")

    def generate_response(self, raw_text: str, intent: str, sentiment: str) -> str:
        # 1. Buscar en el FAQ con umbral más bajo (0.3)
        t_rag0 = time.perf_counter()
        faq_answer, score = retriever_service.search(raw_text, threshold=0.3)
        t_rag1 = time.perf_counter()
        print(f"[TIMING RAG] busqueda_rag={t_rag1-t_rag0:.3f}s | score={score:.3f} | encontrado={faq_answer is not None}")

        # 2. Definir intenciones que pueden usar FAQ
        intenciones_informativas = [
            "consulta_horario", "consulta_direccion", "informacion_general",
            "consulta_estado_orden"
        ]

        # 3. Solo usar FAQ si la intención es informativa Y el score es decente
        if intent in intenciones_informativas and faq_answer and score >= 0.3:
            if "horario" in intent or "hora" in faq_answer.lower():
                return f"¡Claro! {faq_answer} ¿Te puedo ayudar en algo más?"
            elif "dirección" in intent or "direccion" in intent or "ubicado" in faq_answer.lower():
                return f"Nuestra ubicación: {faq_answer} ¿Necesitas algo más?"
            else:
                return f"{faq_answer} ¿Necesitas algo más?"

        # 4. Plantillas por sentimiento e intención
        if sentiment == "negative":
            if "queja" in intent or "problema" in intent or "fallo" in intent:
                return ("Lamento muchísimo el inconveniente. Entiendo tu molestia y quiero ayudarte a resolverlo cuanto antes. "
                        "¿Podrías darme más detalles de lo sucedido? Si prefieres, te comunico de inmediato con un agente humano.")
            else:
                return ("Siento que estés pasando por esto. Cuéntame un poco más para entender mejor tu situación "
                        "y encontrar una solución. Si lo deseas, puedo transferirte con un agente humano.")

        # 5. Intenciones que requieren soporte técnico o asistencia (sentimiento neutro)
        if intent in ["problema_tarjeta_bancaria", "fallo_tecnico", "solicitud_reembolso"]:
            return ("Entiendo que tienes una dificultad. ¿Podrías darme más detalles sobre lo que sucede? "
                    "Así puedo orientarte mejor o, si lo prefieres, comunicarte con un agente humano.")

        # 6. Consultas sin FAQ
        if intent in ["consulta_horario", "consulta_direccion", "informacion_general"]:
            return ("Permíteme revisar esa información. ¿Podrías ser un poco más específico? "
                    "Así te doy la respuesta exacta que necesitas.")

        # 7. Saludo / Despedida
        if intent == "saludo":
            return "¡Hola! Soy el asistente virtual de PluriOne. ¿En qué puedo ayudarte hoy?"

        if intent == "despedida":
            return "¡Gracias por contactarnos! Estamos a tu disposición cuando lo necesites. ¡Que tengas excelente día!"

        # 8. Fallback genérico
        return "Gracias por tu mensaje. ¿Podrías darme más detalles para entender mejor cómo ayudarte?"

llm_service = LLMService()