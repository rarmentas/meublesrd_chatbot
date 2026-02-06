# MueblesRD Customer Service Chatbot API

A Django REST Framework backend implementing a RAG (Retrieval-Augmented Generation) pipeline for MueblesRD's internal customer service operations. This API helps store employees find answers to customer service questions by retrieving relevant company policies and procedures from a vector database.

## Features

- RAG-powered chatbot using LangChain and OpenAI GPT
- Vector search with Pinecone for company policy retrieval
- Source attribution for generated responses
- Stateless API design (no database required)
- CORS-enabled for frontend integration

## Project Structure

```
backend_django/
├── manage.py                 # Django management utility
├── requirements.txt          # Python dependencies
├── mueblesrd_api/            # Main project configuration
│   ├── settings.py           # Django settings
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py               # WSGI entry point
│   └── asgi.py               # ASGI entry point
└── chatbot/                  # Chatbot application
    ├── urls.py               # App URL routes
    ├── views.py              # API views
    └── rag_service.py        # RAG pipeline logic
```

## Requirements

- Python 3.10+
- OpenAI API key
- Pinecone API key with `mueblesrd-index` configured

## Installation

1. **Clone the repository and navigate to the project directory:**

```bash
cd backend_django
```

2. **Create and activate a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Create a `.env` file in the project root:**

```env
DJANGO_SECRET_KEY=your-secure-secret-key
DEBUG=False
OPENAI_API_KEY=your-openai-api-key
PINECONE_API_KEY=your-pinecone-api-key
```

5. **Run the development server:**

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DJANGO_SECRET_KEY` | Django secret key for cryptographic signing | Yes (production) |
| `DEBUG` | Enable debug mode (`True`/`False`) | No (defaults to `True`) |
| `OPENAI_API_KEY` | OpenAI API key for embeddings and LLM | Yes |
| `PINECONE_API_KEY` | Pinecone API key for vector store | Yes |

## API Reference

### Health Check

Check if the API is running.

```
GET /api/health/
```

**Response:**

```json
{
  "status": "healthy"
}
```

**Status Codes:**
- `200 OK` - Service is healthy

---

### Chat

Send a query to the chatbot and receive a response with relevant sources.

```
POST /api/chat/
```

**Request Headers:**

```
Content-Type: application/json
```

**Request Body:**

```json
{
  "query": "How do I process a customer return request?"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | The customer service question |

**Response:**

```json
{
  "answer": "To process a customer return request, follow these steps: 1. Verify the customer's purchase in Salesforce...",
  "sources": [
    "5.1 Return Procedures",
    "3. Customer Verification"
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Generated response based on company policies |
| `sources` | array | List of policy sections referenced in the answer |

**Status Codes:**
- `200 OK` - Query processed successfully
- `400 Bad Request` - Missing or invalid query parameter
- `500 Internal Server Error` - Processing error

**Error Response Example:**

```json
{
  "error": "Query is required"
}
```

## Usage Examples

### cURL

```bash
# Health check
curl http://localhost:8000/api/health/

# Chat query
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the procedure for Law 25 compliance verification?"}'
```

### Python (requests)

```python
import requests

# Chat query
response = requests.post(
    "http://localhost:8000/api/chat/",
    json={"query": "How do I handle a duplicate customer request?"}
)

data = response.json()
print(f"Answer: {data['answer']}")
print(f"Sources: {data['sources']}")
```

### JavaScript (fetch)

```javascript
const response = await fetch('http://localhost:8000/api/chat/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'How do I check delivery deadlines?'
  }),
});

const data = await response.json();
console.log('Answer:', data.answer);
console.log('Sources:', data.sources);
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Client    │────▶│  Django API  │────▶│  LangChain      │
│  (Frontend) │     │  /api/chat/  │     │  Agent          │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    │                             ▼                             │
                    │    ┌─────────────────┐     ┌─────────────────┐           │
                    │    │    Pinecone     │◀────│   Retrieval     │           │
                    │    │  Vector Store   │     │     Tool        │           │
                    │    └─────────────────┘     └─────────────────┘           │
                    │                                     │                     │
                    │                                     ▼                     │
                    │                            ┌─────────────────┐           │
                    │                            │   OpenAI GPT    │           │
                    │                            │   (Response)    │           │
                    │                            └─────────────────┘           │
                    └───────────────────────────────────────────────────────────┘
```

## Supported Use Cases

The chatbot is designed to assist store employees with:

- Processing customer requests following standard procedures
- Verifying Law 25 compliance (data protection)
- Validating contracts in Salesforce and Meublex systems
- Checking deadlines and delivery dates
- Determining request admissibility
- Handling duplicate customer requests
- Following up on After-Sales Service (ADS) requests
- Assessing product damage (aesthetic vs. mechanical)

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in environment variables
2. Configure a proper `DJANGO_SECRET_KEY`
3. Set up appropriate `ALLOWED_HOSTS` in settings
4. Configure CORS settings to restrict allowed origins
5. Deploy behind a reverse proxy (nginx, etc.)
6. Consider adding authentication if exposing publicly

## Dependencies

| Package | Purpose |
|---------|---------|
| Django | Web framework |
| djangorestframework | REST API framework |
| django-cors-headers | CORS support |
| python-dotenv | Environment variable loading |
| langchain | AI orchestration framework |
| langchain-openai | OpenAI integration |
| langchain-pinecone | Pinecone vector store |
| langsmith | LangChain tracing/monitoring |
