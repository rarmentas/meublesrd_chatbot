# MueblesRD Helper - Django Backend API

API REST para soporte de servicio al cliente de MueblesRD. Utiliza RAG (Retrieval-Augmented Generation) con LangChain, Pinecone y OpenAI para consultar politicas internas, analizar reclamaciones y evaluar el desempeno de agentes de tienda.

## Requisitos

- Python 3.10+
- Cuentas activas en: OpenAI, Pinecone, LangSmith

## Configuracion

### 1. Instalar dependencias

```bash
cd backend_django
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crear un archivo `.env` en la raiz del proyecto (`mueblesrd_helper/.env`):

```env
OPENAI_API_KEY=sk-proj-...
PINECONE_API_KEY=pcsk_...
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=Documentation Helper
LANGSMITH_TRACING=true
```

| Variable            | Descripcion                              |
| ------------------- | ---------------------------------------- |
| `OPENAI_API_KEY`    | API key de OpenAI (GPT-5.2 + embeddings) |
| `PINECONE_API_KEY`  | API key de Pinecone (vector store)       |
| `LANGSMITH_API_KEY` | API key de LangSmith (monitoreo LLM)     |
| `LANGSMITH_PROJECT` | Nombre del proyecto en LangSmith         |
| `LANGSMITH_TRACING` | Habilitar tracing (`true`/`false`)       |

### 3. Iniciar el servidor

```bash
cd backend_django
python manage.py runserver
```

El servidor arranca en `http://localhost:8000`. Para un puerto diferente:

```bash
python manage.py runserver 8080
```

---

## Arquitectura

```
backend_django/
├── manage.py
├── requirements.txt
├── feedback-agent.txt          # Especificacion de criterios de evaluacion
├── mueblesrd_api/              # Proyecto Django
│   ├── settings.py             # Config: CORS, REST Framework, sin BD
│   ├── urls.py                 # Router principal → /api/
│   ├── wsgi.py
│   └── asgi.py
└── chatbot/                    # App principal
    ├── urls.py                 # Rutas de endpoints
    ├── views.py                # Vistas (serializers + API views)
    └── rag_service.py          # Pipeline RAG (LangChain + Pinecone + OpenAI)
```

**Servicios externos:**

- **OpenAI** — GPT-5.2 (chat) + text-embedding-3-small (embeddings)
- **Pinecone** — Vector store (indice: `mueblesrd-index`)
- **LangSmith** — Tracing y monitoreo de llamadas LLM

**Caracteristicas:**

- API stateless (sin base de datos)
- CORS habilitado para cualquier origen
- Solo JSON (entrada y salida)
- Sin autenticacion (disenado para uso interno)

---

## Mapa de Endpoints

| Metodo | Ruta                        | Descripcion                                                     |
| ------ | --------------------------- | --------------------------------------------------------------- |
| `GET`  | `/api/health/`              | Health check                                                    |
| `POST` | `/api/chat/`                | Chat con RAG (consulta libre)                                   |
| `POST` | `/api/analyze-claim/`       | Analisis de reclamacion + tono                                  |
| `POST` | `/api/agent-feedback/`      | Evaluacion de agente optimizada (~4x mas rapido)                |
| `POST` | `/api/agent-feedback-deep/` | Evaluacion de agente exhaustiva (8 criterios, multi-step agent) |

---

## Detalle de Endpoints

### GET `/api/health/`

Health check del servidor.

**Respuesta:**

```json
{
  "status": "healthy"
}
```

---

### POST `/api/chat/`

Consulta libre al chatbot con RAG. Busca en las politicas de MueblesRD y responde con fuentes.

**Entrada:**

```json
{
  "query": "Como verifico el cumplimiento de la Ley 25?"
}
```

| Campo   | Tipo   | Requerido | Descripcion                  |
| ------- | ------ | --------- | ---------------------------- |
| `query` | string | Si        | Pregunta en lenguaje natural |

**Respuesta:**

```json
{
  "answer": "Para verificar el cumplimiento de la Ley 25, debes...",
  "sources": ["1. Verify Law 25 Compliance", "0.-Global Procedure"]
}
```

---

### POST `/api/analyze-claim/`

Analiza una reclamacion de cliente: busca politicas relevantes, analiza el tono del mensaje y devuelve recomendaciones.

**Entrada:**

```json
{
  "claim_type": "Defective, damaged product(s) or missing part(s)",
  "damage_type": "Mechanical or Structural",
  "delivery_date": "2025-12-15",
  "product_type": "Furniture",
  "manufacturer": "Ashley Furniture",
  "store_of_purchase": "MueblesRD Santo Domingo",
  "product_code": "ASH-TBL-4521",
  "description": "The dining table leg snapped off during normal use two weeks after delivery.",
  "has_attachments": true
}
```

| Campo              | Tipo    | Requerido | Valores permitidos                                                                                                                                           |
| ------------------ | ------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `claim_type`       | string  | Si        | `"Defective, damaged product(s) or missing part(s)"`, `"Error or Missing Product"`, `"Home Damage or Delivery Complaint"`, `"ComfoRD Warranty - Mattresses"` |
| `damage_type`      | string  | Si        | `"Aesthetics"`, `"Mechanical or Structural"`, `"Missing Part(s)"`                                                                                            |
| `delivery_date`    | string  | Si        | Formato `YYYY-MM-DD`                                                                                                                                         |
| `product_type`     | string  | Si        | `"Furniture"`, `"Appliances"`, `"Barbecue"`, `"Electronics"`, `"Mattresses"`                                                                                 |
| `manufacturer`     | string  | Si        | Texto libre (max 100 chars)                                                                                                                                  |
| `store_of_purchase` | string | Si        | Texto libre (max 100 chars)                                                                                                                                  |
| `product_code`     | string  | Si        | Texto libre (max 50 chars)                                                                                                                                   |
| `description`      | string  | Si        | Descripcion del problema (10-5000 chars)                                                                                                                     |
| `has_attachments`  | boolean | Si        | `true` / `false`                                                                                                                                             |

**Respuesta:**

```json
{
  "claim_summary": {
    "claim_type": "Defective, damaged product(s) or missing part(s)",
    "product_type": "Furniture",
    "damage_type": "Mechanical or Structural",
    "days_since_delivery": 45
  },
  "tone_analysis": {
    "tone": "neutral",
    "confidence": 0.85,
    "indicators": ["factual description", "no emotional language"]
  },
  "policy_recommendations": [
    {
      "policy_reference": "Section 4: Respecting Deadlines",
      "recommendation": "Claim is within the 90-day window.",
      "priority": "high"
    }
  ],
  "communication_recommendations": {
    "approach": "standard",
    "tips": ["Acknowledge the issue", "Reference the policy"],
    "suggested_opening": "Thank you for reaching out..."
  },
  "next_steps": [
    "Verify contract number in Salesforce",
    "Request photos of the damage"
  ],
  "sources": ["4. Respecting Deadlines", "5.1 Validation of Damage Type"]
}
```

---

### POST `/api/agent-feedback/`

Evalua el manejo de una reclamacion por parte de un agente de tienda. Version optimizada: usa queries batch al vectorstore y una sola llamada LLM (~4-5 segundos).

**Entrada:**

Incluye todos los campos de `analyze-claim` mas 3 campos adicionales de verificacion:

```json
{
  "claim_type": "Defective, damaged product(s) or missing part(s)",
  "damage_type": "Mechanical or Structural",
  "delivery_date": "2025-12-15",
  "product_type": "Furniture",
  "manufacturer": "Ashley Furniture",
  "store_of_purchase": "MueblesRD Santo Domingo",
  "product_code": "ASH-TBL-4521",
  "description": "The dining table leg snapped off during normal use two weeks after delivery.",
  "has_attachments": true,
  "contract_number": "CN-2025-34567",
  "claim_date": "2025-12-30",
  "eligible": true
}
```

**Campos adicionales:**

| Campo             | Tipo    | Requerido | Descripcion                                            |
| ----------------- | ------- | --------- | ------------------------------------------------------ |
| `contract_number` | string  | Si        | Numero de contrato (max 100 chars)                     |
| `claim_date`      | string  | Si        | Fecha en que se presento la reclamacion (`YYYY-MM-DD`) |
| `eligible`        | boolean | Si        | Decision de elegibilidad del agente                    |

**Respuesta:**

```json
{
  "claim_summary": {
    "claim_type": "Defective, damaged product(s) or missing part(s)",
    "product_type": "Furniture",
    "damage_type": "Mechanical or Structural",
    "manufacturer": "Ashley Furniture",
    "claim_date": "2025-12-30",
    "days_since_delivery": 45,
    "days_delivery_to_claim": 15,
    "eligible_input": true
  },
  "criteria_evaluations": {
    "contract_verification": { "result": "Correct", "explanation": "Contract number is provided (CN-2025-34567). IMPORTANT: Please compare the name of the person that made the ticket or claim against the data in the contract to ensure they match." },
    "delivery_date": { "result": "In Warranty", "recommendation": "..." },
    "damage_classification_validation": {
      "result": true,
      "recommendation": "..."
    },
    "attachments_verification": { "result": true, "recommendation": "..." },
    "eligibility_decision": { "isDecisionCorrect": true, "explanation": "..." }
  },
  "final_recommendation": "The agent handled this claim correctly...",
  "final_eligibility": { "isEligible": true, "justification": "..." },
  "sources": ["4. Respecting Deadlines", "5.1 Validation of Damage Type"]
}
```

> **Nota:** El criterio 1 devuelve `{"result": "Correct"/"Incorrect", "explanation": "..."}` de forma deterministica (presencia de contract_number), siempre incluye un recordatorio para que el agente compare el nombre del solicitante contra los datos del contrato.

---

### POST `/api/agent-feedback-deep/`

Version exhaustiva de la evaluacion de agente. Usa un agente LangChain con multiples llamadas a herramientas de RAG para un analisis mas profundo de cada criterio (5 criterios con explicaciones detalladas).

> **Nota:** Este endpoint es mas exhaustivo pero tarda ~15-20 segundos por las multiples llamadas LLM + vector search. Para la version rapida, usar `/api/agent-feedback/`.

**Entrada:** Identica a `/api/agent-feedback/`

**Diferencias con `/api/agent-feedback/`:**

| Aspecto              | `agent-feedback`                          | `agent-feedback-deep`           |
| -------------------- | ----------------------------------------- | ------------------------------- |
| Busqueda de politicas | 2 queries batch al vectorstore           | 4-5 tool calls del agente       |
| Criterio 1           | Deterministico (`Correct`/`Incorrect` + explicacion) | LLM evalua con detalle |
| Llamadas LLM         | 1 sola llamada `model.invoke()`           | ~6-8 (agent loop)               |
| Tiempo estimado      | ~4-5s                                     | ~15-20s                         |

**Respuesta:**

```json
{
  "claim_summary": {
    "claim_type": "Defective, damaged product(s) or missing part(s)",
    "product_type": "Furniture",
    "damage_type": "Mechanical or Structural",
    "manufacturer": "Ashley Furniture",
    "claim_date": "2025-12-30",
    "days_since_delivery": 45,
    "days_delivery_to_claim": 15,
    "eligible_input": true
  },
  "criteria_evaluations": {
    "contract_verification": { "result": "Correct", "explanation": "..." },
    "delivery_date": { "result": "In Warranty", "recommendation": "..." },
    "damage_classification_validation": {
      "result": true,
      "recommendation": "..."
    },
    "attachments_verification": { "result": true, "recommendation": "..." },
    "eligibility_decision": { "isDecisionCorrect": true, "explanation": "..." }
  },
  "final_recommendation": "The agent handled this claim correctly...",
  "final_eligibility": { "isEligible": true, "justification": "..." },
  "sources": ["4. Respecting Deadlines", "5.1 Validation of Damage Type"]
}
```

**Criterios de evaluacion (5):**

| #   | Criterio                         | Metodo                                  | Usa RAG? |
| --- | -------------------------------- | --------------------------------------- | -------- |
| 1   | Verificacion de contrato         | Verificacion de `contract_number`       | No       |
| 2   | Fecha de entrega                 | Fechas + RAG (politicas de plazos)      | Si       |
| 3   | Clasificacion del dano           | LLM compara descripcion vs tipo con RAG | Si       |
| 4   | Verificacion de adjuntos         | Boolean + RAG (requisitos de adjuntos)  | Si       |
| 5   | Decision de elegibilidad final   | LLM sintetiza los 4 criterios + RAG     | Si       |

---

## Respuestas de Error

**400 - Validacion fallida:**

```json
{
  "error": "Invalid input",
  "details": {
    "claim_type": ["\"invalid\" is not a valid choice."],
    "delivery_date": ["Date has wrong format. Use YYYY-MM-DD."]
  }
}
```

**400 - Campo faltante (chat):**

```json
{
  "error": "Query is required"
}
```

**500 - Error interno:**

```json
{
  "error": "Connection to Pinecone timed out"
}
```

---

## Ejemplos con curl

### Chat

```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I verify Law 25 compliance?"}'
```

### Analisis de reclamacion

```bash
curl -X POST http://localhost:8000/api/analyze-claim/ \
  -H "Content-Type: application/json" \
  -d '{
    "claim_type": "Defective, damaged product(s) or missing part(s)",
    "damage_type": "Mechanical or Structural",
    "delivery_date": "2025-12-15",
    "product_type": "Furniture",
    "manufacturer": "Ashley Furniture",
    "store_of_purchase": "MueblesRD Santo Domingo",
    "product_code": "ASH-TBL-4521",
    "description": "The dining table leg snapped off during normal use two weeks after delivery.",
    "has_attachments": true
  }'
```

### Feedback de agente

```bash
curl -X POST http://localhost:8000/api/agent-feedback/ \
  -H "Content-Type: application/json" \
  -d '{
    "claim_type": "Defective, damaged product(s) or missing part(s)",
    "damage_type": "Mechanical or Structural",
    "delivery_date": "2025-12-15",
    "product_type": "Furniture",
    "manufacturer": "Ashley Furniture",
    "store_of_purchase": "MueblesRD Santo Domingo",
    "product_code": "ASH-TBL-4521",
    "description": "The dining table leg snapped off during normal use two weeks after delivery.",
    "has_attachments": true,
    "contract_number": "CN-2025-34567",
    "claim_date": "2025-12-30",
    "eligible": true
  }'
```
