from transformers import AutoTokenizer, AutoModelForCausalLM
from app.services.retriever_service import retriever_service

class LLMService:
    def __init__(self):
        print("[LLM] Cargando modelo TinyLlama (Chat real)...")
        model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(model_id).to("cpu")
        print("[LLM] Modelo TinyLlama listo para chatear.")

    def generate_response(self, raw_text: str, intent: str, sentiment: str) -> str:
        # 1. BUSCAR EN MEMORIA (RAG)
        faq_answer, score = retriever_service.search(raw_text)
        if faq_answer:
            return faq_answer

        # 2. RESPUESTA EMPÁTICA (Si hay problemas)
        if sentiment == 'negative' or intent in ['queja_cobro_duplicado', 'solicitud_reembolso']:
            return f"Lamento mucho la inconveniencia. Entiendo tu frustración. Un agente especializado revisará tu caso de {intent} inmediatamente para ayudarte."

        # 3. LLM CREATIVO (Si es saludo o algo general)
        prompt = f"User: {raw_text}\nAgent:"
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs, max_new_tokens=50, temperature=0.7, do_sample=True, pad_token_id=self.tokenizer.eos_token_id)
        
        response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        if "Agent:" in response_text:
            response_text = response_text.split("Agent:")[-1].strip()
            
        if not response_text or len(response_text) < 3:
            response_text = "Hola, estoy aquí para ayudarte. ¿En qué te puedo servir?"
            
        return response_text

llm_service = LLMService()