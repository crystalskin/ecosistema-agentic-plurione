# CLAUDE.md — Ecosistema Agentic de Servicio al Cliente (PluriOne)

> Claude Code lee este archivo al inicio de cada sesión. Mantiene el contexto, las
> convenciones y el estado del proyecto. Amplíalo conforme avances.

---

## Entorno de trabajo
- **SO**: Windows + **PowerShell** (no CMD ni bash). Usa sintaxis de PowerShell: separa
  comandos con `;`, **no** con `&&`.
- **Raíz del proyecto**: `C:\Users\Ale\Downloads\VisualStudio\Proyecto_Agentics\Modulo 7`
- Todos los comandos se ejecutan **desde la raíz** salvo que se indique lo contrario.
- **Git**: repo `ecosistema-agentic-plurione` (usuario `crystalskin`). NO subir
  `Proyecto_Agentics` completo, solo la carpeta `Modulo 7`.
- **Idioma**: responde y comenta el código en español.

---

## Visión general
Chat en tiempo real que atiende usuarios, detecta su enojo, entiende su intención,
busca respuestas en una base de conocimiento (FAQ), responde con IA y aprende de sus
propios errores. Arquitectura **Event-Driven + Microservicios**. Cubre los Módulos 1–10
(varios todavía en desarrollo).

---

## Stack tecnológico
- **Contenedores (Docker Desktop)**: PostgreSQL 15, RabbitMQ 3, MLflow v2.
- **IA — Python 3.14**: FastAPI, Uvicorn, PyTorch, HuggingFace Transformers,
  Sentence-Transformers, pika.
- **Gateway — Node.js 24**: NestJS, TypeORM, Socket.io, Axios.
- **Frontend**: React 18, Vite, Socket.io-client, React-Router-DOM, Recharts.
- **Base de datos**: PostgreSQL. Tablas: `logs_interacciones`, `cognize_events`.
  BD de aprendizaje: `aprendizaje_db`.

---

## Flujo de datos
1. El usuario escribe en **React (5174)**.
2. Mensaje → **WebSockets** → **NestJS (3000)**.
3. NestJS → **HTTP POST** → **FastAPI (8000)**.
4. Python ejecuta 4 pasos en cadena:
   - **RAG** (`retriever_service`): busca en el FAQ por similitud coseno (Sentence Transformers).
   - **NLP** (`nlp_service`): clasifica intención (Zero-Shot con BART) y sentimiento (modelo multilingüe de 5 estrellas).
     **Optimización activa (shortcircuit RAG)**: si `retriever_service` devuelve score >= 0.90,
     se omiten `bert_sentiment` y `bart_intent` y se responde directo con el FAQ. El campo
     `intent` se marca como `"rag_directo"` (no null). Reduce consultas FAQ de ~1.3 s a
     ~0.065 s. Para scores < 0.90 se ejecuta el pipeline NLP completo.
   - **LLM** (`llm_service`): híbrido. Si el RAG encuentra respuesta y la intención es informativa → paráfrasis con plantillas; si no → plantillas empáticas según sentimiento/intención. **Sin modelos generativos, para evitar alucinaciones.**
   - **Broker** (`broker_service`): publica el evento en **RabbitMQ (5672)**.
5. NestJS recibe la respuesta de Python, la guarda en **PostgreSQL** (si el servicio de métricas está activo) y la devuelve a React.
6. `consumidor.py` escucha RabbitMQ, guarda las interacciones en `aprendizaje_db` y alimenta el aprendizaje continuo (Módulo 7). Reentrenamiento planeado con **MLflow (5000)**.

---

## Puertos
| Servicio | Puerto |
| --- | --- |
| React (Vite) | 5174 |
| NestJS | 3000 |
| FastAPI | 8000 |
| RabbitMQ | 5672 (panel 15672) |
| PostgreSQL | 5432 |
| MLflow | 5000 |

---

## Estructura de carpetas (raíz `Modulo 7/`)
```
Modulo 7/
├── docker-compose.yml
├── consumidor.py
├── generador_dataset.py
├── entrenamiento_ac06.py
├── validacion_rollback_ac08.py
├── .gitignore
├── CLAUDE.md
│
├── ml-cognitive-engine/          # Motor cognitivo (Python)
│   ├── knowledge_base/plurione_faq.json
│   ├── .venv/
│   └── app/
│       ├── main.py
│       ├── api/routes.py
│       ├── models/schemas.py     # ← modelo Pydantic CognizeEvent
│       └── services/
│           ├── nlp_service.py
│           ├── retriever_service.py
│           ├── llm_service.py
│           └── broker_service.py
│
├── backend-nestjs/               # Gateway principal (Node.js)
│   ├── src/
│   │   ├── main.ts
│   │   ├── app.module.ts
│   │   ├── cognitive/
│   │   │   ├── cognitive.module.ts
│   │   │   ├── cognitive.controller.ts
│   │   │   ├── cognitive.service.ts
│   │   │   ├── metrics.service.ts
│   │   │   └── cognize-event.entity.ts
│   │   └── chat/chat.gateway.ts
│   └── package.json
│
├── frontend-chat/                # Interfaz React
│   ├── src/
│   │   ├── App.jsx
│   │   └── pages/
│   │       ├── ChatPage.jsx
│   │       └── MetricsPage.jsx
│   └── package.json
│
└── datasets/                     # Datos de entrenamiento
```

---

## Comandos de arranque (PowerShell, desde la raíz)
1. **Docker**: `docker-compose up -d`  → verificar con `docker ps`
2. **FastAPI**: `cd ml-cognitive-engine; .\.venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --reload --port 8000`
3. **NestJS**: `cd backend-nestjs; npm run start:dev`
4. **React**: `cd frontend-chat; npm run dev`
5. **Consumidor** (opcional, con `.venv` activo): `python consumidor.py`

---

## Reglas de reinicio
- Cambios en `nlp_service`, `llm_service` o `retriever_service` → **reiniciar FastAPI**.
- Cambios en controladores/servicios de NestJS → **reiniciar `backend-nestjs`**.
- React se recarga solo (HMR de Vite).
- El `WebSocketGateway` de NestJS tiene `cors: true`.

---

## ⚠️ TAREA ACTIVA (máxima prioridad)
**Conectar `broker_service.py` → `consumidor.py` vía RabbitMQ.**

- **Causa raíz diagnosticada**: `broker_service.py` publica en un *topic exchange* llamado
  `agentic_exchange` con routing key `cognicion.evaluada`, pero el `consumidor.py` original
  **nunca declaraba el exchange ni hacía bind de la cola** → RabbitMQ descarta el mensaje
  en silencio (sin lanzar error).
- **Fix**: en el consumidor, añadir `exchange_declare()`, `queue_declare()` y `queue_bind()`
  con binding key `cognicion.#`.
- **Verificar SIN FALLA antes de probar**: posible desajuste de nombre de campo.
  `broker_service.py` referencia `event.event_id`, mientras que `consumidor.py` inserta el
  PRIMARY KEY usando `datos.get('id_interaccion')`. Si no coinciden, la inserción mete un
  **NULL silencioso**. Confirmar contra el modelo Pydantic `CognizeEvent` en
  `ml-cognitive-engine/app/models/schemas.py`.
- **Pendiente**: prueba end-to-end una vez que Docker esté corriendo.

### Principios aprendidos (event-driven)
- Los *topic exchanges* de RabbitMQ requieren `exchange_declare()` + `queue_declare()` +
  `queue_bind()` del lado del consumidor. Omitir cualquiera = pérdida silenciosa de mensajes,
  sin error.
- Los desajustes de nombre de campo entre publisher y consumer fallan en silencio →
  verificar el schema antes de cualquier prueba de integración.
- Los comandos `docker-compose` deben correrse desde la carpeta que contiene
  `docker-compose.yml` (la raíz); desde un directorio padre da *file not found*.

---

## Estado de los módulos
- **M1 — Agente conversacional**: ✅ Completado y verificado end-to-end.
  Flujo operativo: React → WebSocket (`chat.gateway.ts`) → NestJS → FastAPI → RabbitMQ → `consumidor.py`.
  Sistema híbrido RAG + plantillas con shortcircuit (FAQ ~0.065 s, NLP completo ~1.2 s). Sin alucinaciones.
- **M2 — Dashboard de métricas**: 🚧 En progreso. Endpoint `GET /api/cognitive/metrics` y
  `MetricsPage.jsx` (Recharts) creados, pero `MetricsService` aún no probado con datos reales.
  *Pendiente*: verificar `MetricsService` contra la entidad `CognizeEventEntity`; ajustar
  nombres de columnas (`sentiment`, `intent`, `intent_confidence`); probar el endpoint en
  `http://localhost:3000/api/cognitive/metrics`; revisar logs de NestJS si da error 500.
- **M3 — Resolución automática de incidencias**: ❌ No iniciado.
- **M4 — Integración con sistemas empresariales**: ❌ No iniciado.
- **M5 — Escalamiento inteligente a humanos**: ❌ Diseñado, no programado.
  *Flujo*: en `chat.gateway.ts`, tras la respuesta de FastAPI, si
  `sentiment.label === 'negative'` y (`emotion === 'frustracion'` o `score > 0.8`) →
  emitir `escalate_human` al frontend → `ChatPage.jsx` muestra botón "Hablar con un agente"
  → al pulsar emite `request_human` (publica en RabbitMQ / detiene la conversación automática
  / opcional: notifica a tickets o correo).
  *Archivos*: `backend-nestjs/src/chat/chat.gateway.ts`, `frontend-chat/src/pages/ChatPage.jsx`.
- **M6 — Decisiones empresariales automatizadas**: ❌ No iniciado.
- **M7 — Aprendizaje continuo**: ✅ El consumidor recibe eventos y guarda en
  `logs_interacciones`. Scripts de reentrenamiento existen pero no automatizados en el pipeline.
- **M8 — Análisis de sentimiento en tiempo real**: ✅ Integrado en `nlp_service.py`.
- **M9 — Alta disponibilidad**: ❌ No iniciado.
- **M10 — Clasificación de tickets**: ❌ No iniciado.

---

## Convenciones
- Verifica nombres de campo/columna contra `schemas.py` y `cognize-event.entity.ts` antes de
  tocar cualquier flujo event-driven.
- Al ampliar este archivo, usa bloques de código y listas claras.

## Objetivo de calidad
Este proyecto es mi entrega de estadías y quiero que quede COMPLETO y PULIDO,
no solo funcional. En cada cambio de frontend (frontend-chat):
- Diseño limpio y profesional: jerarquía visual clara, espaciado consistente,
  paleta coherente con el verde de PluriOne.
- Gráficos (Recharts) legibles y bien etiquetados, con estados de carga y de "sin datos".
- Estados de error y vacío manejados con elegancia (nada de pantallas en blanco).
- Responsivo y sin elementos rotos o desalineados.
Prioriza que se vea terminado. Si ves algo a medias o descuidado, proponme mejorarlo.