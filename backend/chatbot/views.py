"""
API views for MueblesRD chatbot.
"""

import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .rag_service import run_llm
from .serializers import (
    ChatRequestSerializer,
    ChatResponseSerializer,
    ChatErrorSerializer,
    HealthResponseSerializer,
)


# Section patterns to extract from content if metadata doesn't have section title
SECTION_PATTERNS = [
    r"(\d+\.?\d*\.-[A-Za-z\s]+)",  # Matches "0.-Global Procedure", "5.1 Validation"
    r"(\d+\.\s*[A-Z][A-Za-z\s]+(?:of|and|the|in|to|for|with)?[A-Za-z\s]*)",  # Matches "1. Verify Law 25"
]


def extract_section_from_content(content: str) -> str:
    """Extract section title from document content."""
    for pattern in SECTION_PATTERNS:
        match = re.search(pattern, content)
        if match:
            title = match.group(1).strip()
            title = re.sub(r'\s+', ' ', title)
            if len(title) > 10:
                return title[:80]

    # Fallback: use first line if it looks like a header
    first_line = content.split('\n')[0].strip()
    if first_line and len(first_line) < 100 and not first_line.endswith('.'):
        return first_line[:80]

    return None


class HealthCheckView(APIView):
    """Health check endpoint."""

    @extend_schema(
        summary="Health check",
        description="Comprueba que el servicio esté en marcha.",
        responses={200: HealthResponseSerializer},
    )
    def get(self, request):
        return Response({"status": "healthy"})


class ChatView(APIView):
    """Chat endpoint for processing queries."""

    @extend_schema(
        summary="Enviar mensaje al chatbot",
        description="Envía una pregunta al chatbot RAG y devuelve la respuesta con las fuentes usadas.",
        request=ChatRequestSerializer,
        responses={
            200: ChatResponseSerializer,
            400: ChatErrorSerializer,
            500: ChatErrorSerializer,
        },
    )
    def post(self, request):
        """Process a chat query and return the response with sources."""
        query = request.data.get('query')

        if not query:
            return Response(
                {"error": "Query is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = run_llm(query)

            # Extract sources from context documents
            sources = []
            seen = set()

            for doc in result.get("context", []):
                source = None

                if hasattr(doc, "metadata"):
                    meta_source = doc.metadata.get("source", "")

                    # Skip if source is a PDF filename or empty
                    if meta_source and not meta_source.lower().endswith('.pdf'):
                        source = meta_source

                # If no valid source in metadata, extract from content
                if not source and hasattr(doc, "page_content"):
                    source = extract_section_from_content(doc.page_content)

                # Add to sources if valid and not duplicate
                if source and source not in seen:
                    seen.add(source)
                    sources.append(source)

            return Response({
                "answer": result.get("answer", "No answer available."),
                "sources": sources
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
