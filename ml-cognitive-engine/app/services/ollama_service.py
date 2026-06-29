"""
ollama_service.py — Cliente síncrono para Ollama local.

Requisitos previos (ejecutar una vez, fuera del venv):
  1. Instalar Ollama: https://ollama.com/download  (Windows installer)
  2. Descargar el modelo: ollama pull qwen2.5:7b
  3. Ollama queda como servicio en http://localhost:11434

Si Ollama no está corriendo, generar_respuesta_con_contexto() devuelve None
y llm_service cae automáticamente a su plantilla de respaldo.
"""

import requests
from pathlib import Path

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"
TIMEOUT_SEG  = 15      # timeout por respuesta
MAX_TOKENS   = 120     # respuestas concisas para chatbot

# System prompt: cargado desde persona_agente.md al importar el módulo (una vez).
# Fallback al texto anterior si el archivo no existe o falla la lectura.
_SYSTEM_PROMPT_FALLBACK = (
    "Eres un asistente de servicio al cliente de PluriOne, empresa mexicana. "
    "REGLAS ESTRICTAS: "
    "1. Responde ÚNICAMENTE usando la información del CONTEXTO provisto. "
    "2. Si el CONTEXTO no contiene la respuesta, di exactamente: "
    "\"No tengo esa información disponible. ¿Te puedo ayudar con algo más?\" "
    "3. NO inventes datos como horarios, precios, políticas ni nombres. "
    "4. Responde en español mexicano, máximo 3 oraciones, tono amigable y directo. "
    "5. No menciones que usas un contexto o base de conocimiento."
)
_PERSONA_PATH = Path(__file__).parent.parent / "knowledge_base" / "persona_agente.md"
try:
    _SYSTEM_PROMPT = _PERSONA_PATH.read_text(encoding="utf-8")
    print(f"[OllamaService] Persona cargada desde {_PERSONA_PATH.name}")
except Exception as _e:
    print(f"[OllamaService] WARN: no se pudo leer persona_agente.md ({_e}). Usando fallback.")
    _SYSTEM_PROMPT = _SYSTEM_PROMPT_FALLBACK


def verificar_conexion() -> bool:
    """Devuelve True si Ollama está corriendo y el modelo está disponible."""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        if not resp.ok:
            return False
        modelos = [m["name"] for m in resp.json().get("models", [])]
        disponible = any(OLLAMA_MODEL.split(":")[0] in m for m in modelos)
        if not disponible:
            print(f"[OllamaService] Modelo '{OLLAMA_MODEL}' no encontrado. "
                  f"Ejecuta: ollama pull {OLLAMA_MODEL}")
        return disponible
    except requests.exceptions.ConnectionError:
        return False


def generar_respuesta_con_contexto(
    pregunta: str, contexto_faq: str, historial: list | None = None
) -> str | None:
    """
    Genera una respuesta natural usando el FAQ como contexto.
    historial: lista de dicts {"user": str, "bot": str} con los turnos recientes.
    Devuelve None si Ollama no está disponible (llm_service usará la plantilla).
    """
    bloque_hist = ""
    if historial:
        lineas = []
        for turno in historial:
            lineas.append(f"Usuario: {turno['user']}")
            lineas.append(f"Asistente: {turno['bot']}")
        bloque_hist = "HISTORIAL DE CONVERSACIÓN:\n" + "\n".join(lineas) + "\n\n"

    prompt = (
        f"{bloque_hist}"
        f"CONTEXTO (información oficial):\n{contexto_faq}\n\n"
        f"PREGUNTA DEL CLIENTE:\n{pregunta}\n\n"
        f"RESPUESTA:"
    )

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model":  OLLAMA_MODEL,
                "prompt": prompt,
                "system": _SYSTEM_PROMPT,
                "stream": False,
                "options": {
                    "temperature": 0.3,   # poca creatividad → más fiel al FAQ
                    "num_predict": MAX_TOKENS,
                    "top_p": 0.9,
                },
            },
            timeout=TIMEOUT_SEG,
        )
        resp.raise_for_status()
        texto = resp.json().get("response", "").strip()
        return texto if texto else None

    except requests.exceptions.ConnectionError:
        # Ollama apagado — llm_service usará plantilla
        return None
    except requests.exceptions.Timeout:
        print(f"[OllamaService] Timeout ({TIMEOUT_SEG}s) generando respuesta.")
        return None
    except Exception as e:
        print(f"[OllamaService] Error inesperado: {e}")
        return None
