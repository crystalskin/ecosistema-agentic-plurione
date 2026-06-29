import time
from app.services.retriever_service import retriever_service
from app.services import ollama_service

USAR_LLM_FIRST = True   # False → vuelve al comportamiento anterior (top-1 FAQ)

class LLMService:
    """
    Servicio híbrido: genera respuestas con Qwen2.5-7B (Ollama) cuando hay
    contexto RAG verificado, y usa plantillas para quejas/escalamiento/casos
    sin FAQ — así se evitan alucinaciones en respuestas críticas.
    """

    def __init__(self):
        ollama_ok = ollama_service.verificar_conexion()
        if ollama_ok:
            print(f"[HybridAgent] Ollama activo → generativo para intents informativos ({ollama_service.OLLAMA_MODEL}).")
        else:
            print("[HybridAgent] Ollama no disponible → modo plantillas (fallback completo).")

    def generate_response(self, raw_text: str, intent: str, sentiment: str,
                          history: list | None = None) -> str:
        history = history or []
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

        # 3. Intent informativo + FAQ encontrado → generativo anclado al FAQ
        if intent in intenciones_informativas and faq_answer and score >= 0.3:
            if USAR_LLM_FIRST:
                fragmentos = retriever_service.search_topn(raw_text, n=3)
                contexto = (
                    "\n".join(f"DATO {i+1}: {r}" for i, (r, _) in enumerate(fragmentos))
                    if fragmentos else faq_answer
                )
                t_llm0 = time.perf_counter()
                respuesta = ollama_service.generar_respuesta_con_contexto(raw_text, contexto, history)
                t_llm1 = time.perf_counter()
                if respuesta:
                    print(f"[TIMING LLM] ollama_gen={t_llm1-t_llm0:.3f}s | llm_first=True | n={len(fragmentos)}")
                    return respuesta
                print("[LLMService] LLM-first sin respuesta → plantilla de respaldo.")
            else:
                t_llm0 = time.perf_counter()
                respuesta = ollama_service.generar_respuesta_con_contexto(raw_text, faq_answer, history)
                t_llm1 = time.perf_counter()
                if respuesta:
                    print(f"[TIMING LLM] ollama_gen={t_llm1-t_llm0:.3f}s")
                    return respuesta
                print("[LLMService] Ollama sin respuesta → plantilla de respaldo.")
            # Fallback compartido — Ollama no disponible en cualquier rama
            if "horario" in intent or "hora" in faq_answer.lower():
                return f"¡Con gusto! {faq_answer} ¿Le puedo ayudar en algo más?"
            elif "dirección" in intent or "direccion" in intent or "ubicado" in faq_answer.lower():
                return f"Nuestra ubicación: {faq_answer} ¿Le puedo ayudar en algo más?"
            else:
                return f"{faq_answer} ¿Le puedo ayudar en algo más?"

        # 4. Plantillas por sentimiento e intención
        if sentiment == "negative":
            if "queja" in intent or "problema" in intent or "fallo" in intent:
                return ("Lamento muchísimo el inconveniente. Entiendo su molestia y quiero ayudarle a resolverlo cuanto antes. "
                        "¿Podría darme más detalles de lo sucedido? Si lo prefiere, le comunico de inmediato con un agente humano.")
            else:
                return ("Siento que esté pasando por esto. Cuénteme un poco más para entender mejor su situación "
                        "y encontrar una solución. Si lo desea, puedo transferirle con un agente humano.")

        # 5. Intenciones que requieren soporte técnico o asistencia (sentimiento neutro)
        if intent in ["problema_tarjeta_bancaria", "fallo_tecnico", "solicitud_reembolso"]:
            return ("Entiendo que tiene una dificultad. ¿Podría darme más detalles sobre lo que sucede? "
                    "Así puedo orientarle mejor o, si lo prefiere, comunicarle con un agente humano.")

        # 6. Consultas sin FAQ
        if intent in ["consulta_horario", "consulta_direccion", "informacion_general"]:
            return ("Permítame revisar esa información. ¿Podría ser un poco más específico? "
                    "Así le doy la respuesta exacta que necesita.")

        # 7. Saludo / Despedida
        if intent == "saludo":
            return "¡Hola! Soy el asistente virtual de PluriOne. ¿En qué puedo ayudarle hoy?"

        if intent == "despedida":
            return "¡Gracias por contactarnos! Estamos a su disposición cuando lo necesite. ¡Que tenga excelente día!"

        # 8. Fallback genérico
        return "Gracias por su mensaje. ¿Podría darme más detalles para entender mejor cómo ayudarle?"

llm_service = LLMService()