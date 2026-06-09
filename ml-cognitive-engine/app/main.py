from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="PluriOne - Cognitive Engine API",
    description="Microservicio de IA para clasificación de Intención y Sentimiento en tiempo real",
    version="1.0.0"
)

# Incluimos nuestras rutas
app.include_router(router)

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "ml-cognitive-engine"}