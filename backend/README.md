# MueblesRD Helper - Django Backend API

API REST para soporte de servicio al cliente de MueblesRD. Utiliza RAG (Retrieval-Augmented Generation) con LangChain, Pinecone y OpenAI para consultar politicas internas, analizar reclamaciones y evaluar el desempeno de agentes de tienda.

Todas las recomendaciones generadas por los endpoints de analisis y feedback incorporan los **3 Principios de Servicio GAC**:

1. **Radical Ownership** — Responsabilidad total; lenguaje de propiedad ("Nos comprometemos a...", "Nuestro equipo se responsabiliza de...")
2. **Solution through Options** — Siempre ofrecer 2-3 opciones de resolucion alternativas al cliente
3. **Value Creation through Future Anticipation** — Identificar proactivamente riesgos futuros y acciones preventivas

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
├── feedback-agent.txt          # Especificacion de criterios de evaluacion + principios GAC
├── mueblesrd_api/              # Proyecto Django
│   ├── settings.py             # Config: CORS, REST Framework, sin BD
│   ├── urls.py                 # Router principal → /api/
│   ├── wsgi.py
│   └── asgi.py
└── chatbot/                    # App principal
    ├── urls.py                 # Rutas de endpoints
    ├── views.py                # Vistas (serializers + API views)
    ├── rag_service.py          # Pipeline RAG (LangChain + Pinecone + OpenAI)
    └── claim_type_validator.py # Validacion semantica de claim_type via LLM
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

| Metodo | Ruta                        | Descripcion                                                              |
| ------ | --------------------------- | ------------------------------------------------------------------------ |
| `GET`  | `/api/health/`              | Health check                                                             |
| `POST` | `/api/chat/`                | Chat con RAG (consulta libre)                                            |
| `POST` | `/api/analyze-claim/`       | Analisis de reclamacion + tono + principios GAC                          |
| `POST` | `/api/agent-feedback/`      | Evaluacion de agente optimizada + coaching GAC (~4x mas rapido)          |
| `POST` | `/api/agent-feedback-deep/` | Evaluacion de agente exhaustiva + coaching GAC (5 criterios + multi-step agent) |

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
  "claim_type": "Defective product - broken leg",
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

| Campo               | Tipo    | Requerido | Valores permitidos                                                                                                                                                                           |
| ------------------- | ------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `claim_type`        | string  | Si        | Texto libre (max 200 chars). Validacion semantica: acepta reclamos por productos defectuosos, dañados o partes faltantes; rechaza quejas de entrega, daños al hogar y garantias de colchones |
| `damage_type`       | string  | Si        | `"Aesthetics"`, `"Mechanical or Structural"`, `"Missing Part(s)"`                                                                                                                            |
| `delivery_date`     | string  | Si        | Formato `YYYY-MM-DD`                                                                                                                                                                         |
| `product_type`      | string  | Si        | `"Furniture"`, `"Appliances"`, `"Barbecue"`, `"Electronics"`, `"Mattresses"`                                                                                                                 |
| `manufacturer`      | string  | Si        | Texto libre (max 100 chars)                                                                                                                                                                  |
| `store_of_purchase` | string  | Si        | Texto libre (max 100 chars)                                                                                                                                                                  |
| `product_code`      | string  | Si        | Texto libre (max 50 chars)                                                                                                                                                                   |
| `description`       | string  | Si        | Descripcion del problema (10-5000 chars)                                                                                                                                                     |
| `has_attachments`   | boolean | Si        | `true` / `false`                                                                                                                                                                             |

**Respuesta:**

```json
{
  "claim_summary": {
    "claim_type": "Defective product - broken leg",
    "product_type": "Furniture",
    "damage_type": "Mechanical or Structural",
    "days_since_delivery": 45,
    "has_attachments": true
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
      "priority": "high",
      "ownership_framing": "We take responsibility for processing this claim within the warranty period and will ensure a resolution is provided promptly."
    }
  ],
  "communication_recommendations": {
    "approach": "standard",
    "solution_options": [
      {
        "option_label": "Option A: Full replacement",
        "description": "Replace the defective table with a new unit of the same model.",
        "timeline": "5-7 business days",
        "trade_offs": "Subject to stock availability"
      },
      {
        "option_label": "Option B: Repair service",
        "description": "Send a technician to repair the broken leg on-site.",
        "timeline": "3-5 business days",
        "trade_offs": "Repair may not match original finish"
      }
    ],
    "tips": ["Acknowledge the issue", "Reference the policy"],
    "suggested_opening": "Thank you for reaching out..."
  },
  "next_steps": [
    "Verify contract number in Salesforce",
    "Request photos of the damage"
  ],
  "anticipation_steps": [
    {
      "potential_future_issue": "Customer may experience similar issues with other furniture pieces from the same batch.",
      "preventive_action": "Check if other products from the same order have known quality issues and proactively offer inspection.",
      "follow_up_timeline": "14 days after resolution"
    }
  ],
  "attachments_verification": {
    "result": true,
    "recommendation": "Photos have been provided as required by policy for mechanical damage claims."
  },
  "gac_assessment": {
    "ownership_score": "strong",
    "ownership_evidence": "Recommendations use 'We will...' language and take full responsibility.",
    "options_score": "strong",
    "options_evidence": "Two resolution options provided with timelines and trade-offs.",
    "anticipation_score": "moderate",
    "anticipation_evidence": "Follow-up scheduled but could include more preventive measures."
  },
  "sources": ["4. Respecting Deadlines", "5.1 Validation of Damage Type"]
}
```

**Campos GAC nuevos en la respuesta:**

| Campo                                                  | Descripcion                                                        |
| ------------------------------------------------------ | ------------------------------------------------------------------ |
| `policy_recommendations[].ownership_framing`           | Lenguaje de responsabilidad (Principio 1: Radical Ownership)       |
| `communication_recommendations.solution_options`       | 2-3 opciones de resolucion con timeline y trade-offs (Principio 2) |
| `anticipation_steps`                                   | Riesgos futuros y acciones preventivas (Principio 3)               |
| `gac_assessment`                                       | Evaluacion de cumplimiento de los 3 principios GAC                 |

---

### POST `/api/agent-feedback/`

Evalua el manejo de una reclamacion por parte de un agente de tienda. Version optimizada: usa queries batch al vectorstore y una sola llamada LLM (~4-5 segundos).

**Entrada:**

Incluye todos los campos de `analyze-claim` mas 3 campos adicionales de verificacion:

```json
{
  "claim_type": "Defective product - broken leg",
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
    "claim_type": "Defective product - broken leg",
    "product_type": "Furniture",
    "damage_type": "Mechanical or Structural",
    "manufacturer": "Ashley Furniture",
    "claim_date": "2025-12-30",
    "days_since_delivery": 45,
    "days_delivery_to_claim": 15,
    "eligible_input": true
  },
  "criteria_evaluations": {
    "contract_verification": {
      "result": "Correct",
      "explanation": "Contract number is provided (CN-2025-34567). IMPORTANT: Please compare the name of the person that made the ticket or claim against the data in the contract to ensure they match."
    },
    "delivery_date": { "result": "In Warranty", "recommendation": "..." },
    "damage_classification_validation": {
      "result": true,
      "recommendation": "..."
    },
    "attachments_verification": { "result": true, "recommendation": "..." },
    "eligibility_decision": { "isDecisionCorrect": true, "explanation": "..." }
  },
  "final_recommendation": {
    "summary": "The agent handled this claim correctly...",
    "ownership_coaching": "Use language like 'We will ensure...' instead of 'You need to...' when communicating with the customer.",
    "options_coaching": "Present at least 2 resolution paths (e.g., replacement vs. repair) with timelines.",
    "anticipation_coaching": "Proactively check if other products from the same order may have similar issues and schedule a follow-up."
  },
  "gac_evaluation": {
    "ownership": { "demonstrated": true, "feedback": "Agent took responsibility for the resolution process." },
    "solution_options": { "demonstrated": false, "feedback": "Only one resolution path was offered. Suggest adding repair as an alternative." },
    "future_anticipation": { "demonstrated": false, "feedback": "No follow-up or preventive measures were proposed." }
  },
  "final_eligibility": { "isEligible": true, "justification": "..." },
  "sources": ["4. Respecting Deadlines", "5.1 Validation of Damage Type"]
}
```

> **Nota:** El criterio 1 devuelve `{"result": "Correct"/"Incorrect", "explanation": "..."}` de forma deterministica (presencia de contract_number), siempre incluye un recordatorio para que el agente compare el nombre del solicitante contra los datos del contrato.

**Campos GAC nuevos en la respuesta:**

| Campo                  | Descripcion                                                                             |
| ---------------------- | --------------------------------------------------------------------------------------- |
| `final_recommendation` | Ahora es un objeto estructurado con `summary` + coaching por cada principio GAC         |
| `gac_evaluation`       | Evaluacion de si el agente demostro cada principio GAC (`demonstrated` bool + feedback) |

---

### POST `/api/agent-feedback-deep/`

Version exhaustiva de la evaluacion de agente. Usa un agente LangChain con multiples llamadas a herramientas de RAG para un analisis mas profundo de cada criterio (5 criterios con explicaciones detalladas).

> **Nota:** Este endpoint es mas exhaustivo pero tarda ~15-20 segundos por las multiples llamadas LLM + vector search. Para la version rapida, usar `/api/agent-feedback/`.

**Entrada:** Identica a `/api/agent-feedback/`

**Diferencias con `/api/agent-feedback/`:**

| Aspecto               | `agent-feedback`                                     | `agent-feedback-deep`     |
| --------------------- | ---------------------------------------------------- | ------------------------- |
| Busqueda de politicas | 2 queries batch al vectorstore                       | 4-5 tool calls del agente |
| Criterio 1            | Deterministico (`Correct`/`Incorrect` + explicacion) | LLM evalua con detalle    |
| Llamadas LLM          | 1 sola llamada `model.invoke()`                      | ~6-8 (agent loop)         |
| Tiempo estimado       | ~4-5s                                                | ~15-20s                   |

**Respuesta:**

```json
{
  "claim_summary": {
    "claim_type": "Defective product - broken leg",
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
  "final_recommendation": {
    "summary": "The agent handled this claim correctly...",
    "ownership_coaching": "Use language like 'We will ensure...' instead of 'You need to...'.",
    "options_coaching": "Present at least 2 resolution paths with timelines.",
    "anticipation_coaching": "Schedule a follow-up and check for batch-related issues."
  },
  "gac_evaluation": {
    "ownership": { "demonstrated": true, "feedback": "Agent took responsibility for the resolution." },
    "solution_options": { "demonstrated": false, "feedback": "Only one resolution was offered." },
    "future_anticipation": { "demonstrated": false, "feedback": "No preventive measures proposed." }
  },
  "final_eligibility": { "isEligible": true, "justification": "..." },
  "sources": ["4. Respecting Deadlines", "5.1 Validation of Damage Type"]
}
```

> **Nota:** La estructura de `final_recommendation` y `gac_evaluation` es identica a `/api/agent-feedback/`. Este endpoint ademas evalua los principios GAC usando el prompt extendido de `feedback-agent.txt`.

**Criterios de evaluacion (5 + GAC):**

| #   | Criterio                       | Metodo                                  | Usa RAG? |
| --- | ------------------------------ | --------------------------------------- | -------- |
| 1   | Verificacion de contrato       | Verificacion de `contract_number`       | No       |
| 2   | Fecha de entrega               | Fechas + RAG (politicas de plazos)      | Si       |
| 3   | Clasificacion del dano         | LLM compara descripcion vs tipo con RAG | Si       |
| 4   | Verificacion de adjuntos       | Boolean + RAG (requisitos de adjuntos)  | Si       |
| 5   | Decision de elegibilidad final | LLM sintetiza los 4 criterios + RAG     | Si       |
| GAC | Principios de Servicio GAC     | LLM evalua ownership, opciones y anticipacion | Si |

---

## Respuestas de Error

**400 - Validacion fallida:**

```json
{
  "error": "Invalid input",
  "details": {
    "delivery_date": ["Date has wrong format. Use YYYY-MM-DD."],
    "description": ["This field is required."]
  }
}
```

**400 - Validacion semantica de claim_type:**

```json
{
  "error": "Invalid input",
  "details": {
    "claim_type": [
      "Claim type not accepted: this appears to be a delivery complaint. Only claims for defective, damaged, or missing products/parts are accepted."
    ]
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
    "claim_type": "Defective product - broken leg",
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
    "claim_type": "Defective product - broken leg",
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
