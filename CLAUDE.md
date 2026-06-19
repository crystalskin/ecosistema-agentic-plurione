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

## Próximos módulos (pendientes)

| Módulo | Estado | Notas |
| --- | --- | --- |
| M3 — Resolución automática de incidencias | 🚧 Parcial | 3 árboles funcionales; pendiente: prioridad M5 vs M3 y afinar clasificador |
| M4 — Integración con sistemas empresariales | ❌ No iniciado | — |
| M6 — Decisiones empresariales automatizadas | ❌ No iniciado | — |
| M7 — Aprendizaje continuo | 🚧 Parcial | `consumidor.py` guarda eventos; scripts de reentrenamiento existen pero el pipeline de reentrenamiento automático con MLflow no está conectado |
| M9 — Alta disponibilidad | ❌ No iniciado | — |

---

## Historial: bug resuelto — RabbitMQ exchange/binding (M1)
**Resuelto. El chat funciona end-to-end. Se deja como referencia.**

- **Causa raíz (histórica)**: `broker_service.py` publicaba en un *topic exchange* llamado
  `agentic_exchange` con routing key `cognicion.evaluada`, pero el `consumidor.py` original
  **nunca declaraba el exchange ni hacía bind de la cola** → RabbitMQ descartaba el mensaje
  en silencio (sin lanzar error).
- **Fix aplicado**: en el consumidor, se añadieron `exchange_declare()`, `queue_declare()` y
  `queue_bind()` con binding key `cognicion.#`.

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
- **M2 — Dashboard de métricas**: ✅ Completado.
  Endpoint `GET /api/cognitive/metrics` operativo. `MetricsPage.jsx` (Recharts)
  con KPI cards, PieChart (sentimientos), BarChart (intenciones) y tabla de últimas interacciones.
  Datos de prueba con `seed_datos_demo.py` (42 filas, flag `--reset`). Estados de error y vacío
  manejados con `<EmptyChart />`.
  *Archivos*: `metrics.service.ts`, `MetricsPage.jsx`, `seed_datos_demo.py`.
- **M3 — Resolución automática de incidencias**: 🚧 Parcial (Fases 1–3).
  Flujo guiado interactivo funcional: estado en memoria (`Map<session_id, FlujoState>`) en
  `IncidenciasService`, `arboles.ts` con 3 árboles (`tarjeta_bancaria`, `fallo_tecnico`,
  `cobro_duplicado`), eventos `respuesta_guiada` / `opciones_guiadas`, botones de opciones
  en `ChatPage.jsx`. Salidas `resolver` / `escalar` (reutiliza M5) / `abandonar` verificadas
  end-to-end (escalar y abandonar probadas vía árbol de tarjeta).
  **⚠️ No quitar el override de tarjeta en `analyze_text` sin reemplazo verificado** — sostiene
  el disparo del árbol de tarjeta.
  **Pendiente 1 — clasificador**: el clasificador zero-shot BART a veces no detecta el intent
  correcto (ej. "la app no me deja pagar" → `despedida` en vez de `fallo_tecnico`). El árbol
  de tarjeta es el único confiable gracias al override hardcodeado. Afinar sin romper lo que
  ya funciona queda pendiente (intento previo con frases en inglés rompió "perdí mi tarjeta",
  se revirtió).
  **Pendiente 2 — prioridad M5 vs M3**: para mensajes con sentimiento negativo, el escalamiento
  M5 (`escalate_human`) se dispara antes que el árbol M3, aunque el intent sea correcto (ej.
  "me cobraron dos veces" → `queja_cobro_duplicado` correcto, pero M5 lo tapa). El orden de
  prioridad entre M5 y M3 queda por definir (en `chat.gateway.ts`, bloque `handleUserMessage`).
  *Archivos*: `nlp_service.py` (override en `analyze_text`), `arboles.ts`,
  `incidencias.service/module.ts`, `chat.gateway.ts` (handlers `user_message` + `respuesta_guiada`),
  `ChatPage.jsx` (flujoGuiado state + botones).
- **M4 — Integración con sistemas empresariales**: ❌ No iniciado.
- **M5 — Escalamiento inteligente a humanos**: ✅ Completado (Fases 1–3).
  Disparador: `sentiment.label === 'negative'` && (`emotion === 'frustracion'` || `score > 0.8`).
  Flujo verificado: `chat.gateway.ts` emite `escalate_human` → `ChatPage.jsx` muestra botón
  "Hablar con un agente" + opción "Continuar con el bot" → al pulsar emite `request_human` →
  gateway guarda en BD (`solicitudes_escalamiento`, estado `pendiente`) y publica en RabbitMQ
  (`agentic_exchange`, routing key `escalamiento.solicitado`, cola durable `escalamiento_cola`).
  El bot se detiene para esa sesión. El shortcircuit RAG nunca dispara escalamiento (retorna `neutral`).
  *Archivos*: `chat.gateway.ts`, `ChatPage.jsx`, `escalamiento.entity/service/module.ts`,
  `broker_service.py`, `routes.py` (`/api/v1/escalate`).
- **M6 — Decisiones empresariales automatizadas**: ❌ No iniciado.
- **M7 — Aprendizaje continuo**: ✅ El consumidor recibe eventos y guarda en
  `logs_interacciones`. Scripts de reentrenamiento existen pero no automatizados en el pipeline.
- **M8 — Análisis de sentimiento en tiempo real**: ✅ Integrado en `nlp_service.py`.
- **M9 — Alta disponibilidad**: ❌ No iniciado.
- **M10 — Clasificación de tickets**: ✅ Completado (Fases 1–2).
  Clasificador zero-shot BART reutilizado de `nlp_service.py` con etiquetas descriptivas en inglés.
  Prioridad derivada de la categoría (determinista, sin BERT). Techo de precisión ~80% con zero-shot sin entrenar.
  Categorías: `facturacion`, `soporte_tecnico`, `cuenta_acceso`, `tarjeta_bancaria`, `estado_pedido`,
  `queja_general`, `informacion_general`, `otros`. Prioridades: alta / media / baja.
  Respuesta: `{ categoria, confianza, prioridad }`.
  BD: tabla `tickets_clasificados` (TypeORM, `@CreateDateColumn`, sin timestamptz).
  *Archivos*: `nlp_service.py` (método `clasificar_ticket`), `routes.py` (`POST /api/v1/clasificar-ticket`),
  `tickets/ticket.entity/service/module/controller.ts`, `app.module.ts`.

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