import json
import numpy as np
from sentence_transformers import SentenceTransformer

class RetrieverService:
    def __init__(self):
        print("[RAG] Cargando modelo semántico multilingüe...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        with open('knowledge_base/plurione_faq.json', 'r', encoding='utf-8') as f:
            self.faqs = json.load(f)
            
        self.questions = [faq['q'] for faq in self.faqs]
        self.db_embeddings = self.model.encode(self.questions)
        # Normalizar los embeddings para similitud coseno real
        self.db_embeddings = self.db_embeddings / np.linalg.norm(self.db_embeddings, axis=1, keepdims=True)
        print("[RAG] Base de conocimiento cargada y vectorizada.")

    def search(self, query: str, threshold=0.4):
        query_embedding = self.model.encode([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        scores = np.dot(self.db_embeddings, query_embedding.T).flatten()
        best_score = float(np.max(scores))
        
        if best_score >= threshold:
            best_index = int(np.argmax(scores))
            return self.faqs[best_index]['a'], best_score
        return None, best_score

    def search_topn(self, query: str, n: int = 3, threshold: float = 0.3) -> list[tuple[str, float]]:
        """Devuelve hasta n fragmentos FAQ con score ≥ threshold, ordenados por score desc."""
        query_embedding = self.model.encode([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        scores = np.dot(self.db_embeddings, query_embedding.T).flatten()

        resultados = []
        for idx in np.argsort(scores)[::-1]:
            if float(scores[idx]) < threshold:
                break
            resultados.append((self.faqs[idx]['a'], float(scores[idx])))
            if len(resultados) >= n:
                break
        return resultados

retriever_service = RetrieverService()