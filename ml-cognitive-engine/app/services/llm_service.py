from transformers import AutoTokenizer, AutoModelForCausalLM

class LLMService:
    def __init__(self):
        print("[LLM] Cargando modelo TinyLlama (Chat real)...")
        model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(model_id).to("cpu")
        print("[LLM] Modelo TinyLlama listo para chatear.")

    def generate_response(self, raw_text: str, intent: str, sentiment: str) -> str:
        # TinyLlama usa un formato de chat especial
        prompt = f"""<|user|>
Eres un agente amable de PluriOne. El cliente dijo: '{raw_text}'. 
Su intención es '{intent}' y su sentimiento es '{sentiment}'.
Responde en 1 sola frase en español.<|assistant| >
"""
        
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        # Generamos la respuesta
        outputs = self.model.generate(
            **inputs, 
            max_new_tokens=80, 
            temperature=0.7,      
            do_sample=True,       
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        # Cortamos el prompt de la respuesta final
        response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Limpiamos para quitar el eco del prompt y quedarnos solo con lo que respondió
        if "<|assistant| >" in response_text:
            response_text = response_text.split("<|assistant| >")[-1].strip()
            
        if not response_text:
            response_text = "Entiendo tu situación, estoy aquí para ayudarte."
            
        return response_text

# Instancia global
llm_service = LLMService()