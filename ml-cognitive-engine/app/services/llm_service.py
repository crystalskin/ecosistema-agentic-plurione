from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class LLMService:
    def __init__(self):
        print("[LLM] Cargando modelo generativo FLAN-T5 (Método Manual)...")
        model_name = "google/flan-t5-base"
        
        # Cargamos el "traductor" (Tokenizer) y el "cerebro" (Model) por separado
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        print("[LLM] Modelo generativo listo.")

    def generate_response(self, raw_text: str, intent: str, sentiment: str) -> str:
        # Le damos la instrucción
        prompt = f"""
        You are a helpful customer service agent for PluriOne.
        The user said: '{raw_text}'
        You know their intent is '{intent}' and their sentiment is '{sentiment}'.
        Provide a short, polite, and helpful response in Spanish.
        """
        
        # 1. Convertimos el texto a números que la IA entiende
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        # 2. La IA piensa y genera los números de la respuesta
        outputs = self.model.generate(**inputs, max_new_tokens=100)
        
        # 3. Convertimos los números de vuelta a texto
        response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 4. Si la IA se quedó en blanco, usamos un mensaje de respaldo
        if not response_text or len(response_text) < 5:
            response_text = "Entiendo tu situación. Un agente se comunicará contigo pronto."
            
        return response_text

# Instancia global
llm_service = LLMService()