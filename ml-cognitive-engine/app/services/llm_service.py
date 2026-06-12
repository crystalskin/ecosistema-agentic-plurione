from transformers import AutoTokenizer, AutoModelForCausalLM

class LLMService:
    def __init__(self):
        print("[LLM] Cargando modelo TinyLlama (Chat real)...")
        model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(model_id).to("cpu")
        print("[LLM] Modelo TinyLlama listo para chatear.")

    def generate_response(self, raw_text: str, intent: str, sentiment: str) -> str:
        # TinyLlama se confunde con instrucciones largas. 
        # Le hablamos directo y al grano como si fuera un WhatsApp.
        
        if sentiment == 'negative' or intent in ['queja_cobro_duplicado', 'solicitud_reembolso']:
            prompt = f"User: {raw_text}\nAgent: Lamento mucho la inconveniencia. Entiendo tu frustración. Un agente especializado revisará tu caso de {intent} inmediatamente para ayudarte."
            # Si es negativo, respondemos empáticamente sin dejar que la IA alucine
            return prompt.split("Agent: ")[1]
        else:
            # Si es positivo o neutro, dejamos que la IA sea creativa pero con prompt corto
            prompt = f"User: {raw_text}\nAgent:"
            
            inputs = self.tokenizer(prompt, return_tensors="pt")
            outputs = self.model.generate(
                **inputs, 
                max_new_tokens=50, 
                temperature=0.7,
                do_sample=True, 
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            if "Agent:" in response_text:
                response_text = response_text.split("Agent:")[-1].strip()
                
            if not response_text or len(response_text) < 3:
                response_text = "Hola, estoy aquí para ayudarte. ¿En qué te puedo servir?"
                
            return response_text

# Instancia global
llm_service = LLMService()