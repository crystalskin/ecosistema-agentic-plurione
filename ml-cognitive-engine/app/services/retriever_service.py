import json
import numpy as np
from sentence_transformers import SentenceTransformer

class RetrieverService:
    def __init__(self):
        print("[RAG] Cargando modelo semántico multilingüe...")
        # Modelo ligero y excelente para español
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        with open('knowledge_base/plurione_faq.json', 'r', encoding='utf-8') as f:
            self.faqs = json.load(f)
            
        self.questions = [faq['q'] for faq in self.faqs]
        # Pre-calculamos los vectores de las preguntas para que la búsqueda sea instantánea
        self.db_embeddings = self.model.encode(self.questions)
        print("[RAG] Base de conocimiento cargada y vectorizada.")

    def search(self, query: str, threshold=0.45):
        # Convertimos la pregunta del usuario a vector
        query_embedding = self.model.encode([query])
        
        # Calculamos la similitud coseno
        scores = np.dot(self.db_embeddings, query_embedding.T).flatten()
        best_score = float(np.max(scores))
        
        # Si la similitud es mayor al umbral, devolvemos la respuesta
        if best_score >= threshold:
            best_index = int(np.argmax(scores))
            return self.faqs[best_index]['a'], best_score
            
        return None, best_score

# Instancia global
retriever_service = RetrieverService()