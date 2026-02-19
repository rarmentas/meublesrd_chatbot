"""
API views for MueblesRD chatbot.
"""

import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema

from .rag_service import run_llm, analyze_claim, evaluate_agent_feedback, evaluate_agent_feedback_optimized
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from .serializers import (
    ChatRequestSerializer,
    ChatResponseSerializer,
    ChatErrorSerializer,
    HealthResponseSerializer,
    TokenRequestSerializer,
    TokenResponseSerializer,
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


class ObtainTokenView(APIView):
    """Devuelve un token para el usuario si username/password son correctos."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Obtener token",
        description="Envía usuario y contraseña. Devuelve un token para usar en "
                    "el header: Authorization: Token &lt;token&gt;. Usa los mismos usuarios que Django Admin.",
        request=TokenRequestSerializer,
        responses={
            200: TokenResponseSerializer,
            400: ChatErrorSerializer,
        },
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response(
                {"error": "username y password son obligatorios"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"error": "Credenciales inválidas"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})


class HealthCheckView(APIView):
    """Health check endpoint (público, sin autenticación)."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Health check",
        description="Comprueba que el servicio esté en marcha. No requiere autenticación.",
        responses={200: HealthResponseSerializer},
    )
    def get(self, request):
        return Response({"status": "healthy"})


class ChatView(APIView):
    """Chat endpoint for processing queries (requiere autenticación por token)."""

    permission_classes = [IsAuthenticated]

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


# ============================================================
# Claim Analysis Endpoint
# ============================================================


class ClaimAnalysisInputSerializer(serializers.Serializer):
    """Serializer for claim analysis input validation."""

    CLAIM_TYPE_CHOICES = [
        ("Defective, damaged product(s) or missing part(s)",
         "Defective, damaged product(s) or missing part(s)"),
        ("Error or Missing Product", "Error or Missing Product"),
        ("Home Damage or Delivery Complaint", "Home Damage or Delivery Complaint"),
        ("ComfoRD Warranty - Mattresses", "ComfoRD Warranty - Mattresses"),
    ]
    DAMAGE_TYPE_CHOICES = [
        ("Aesthetics", "Aesthetics"),
        ("Mechanical or Structural", "Mechanical or Structural"),
        ("Missing Part(s)", "Missing Part(s)"),
    ]
    PRODUCT_TYPE_CHOICES = [
        ("Appliances", "Appliances"),
        ("Barbecue", "Barbecue"),
        ("Electronics", "Electronics"),
        ("Mattresses", "Mattresses"),
        ("Furniture", "Furniture"),
    ]

    claim_type = serializers.ChoiceField(choices=CLAIM_TYPE_CHOICES)
    damage_type = serializers.ChoiceField(choices=DAMAGE_TYPE_CHOICES)
    delivery_date = serializers.DateField()
    product_type = serializers.ChoiceField(choices=PRODUCT_TYPE_CHOICES)
    manufacturer = serializers.CharField(max_length=100)
    store_of_purchase = serializers.CharField(max_length=100)
    product_code = serializers.CharField(max_length=50)
    description = serializers.CharField(min_length=10, max_length=5000)
    has_attachments = serializers.BooleanField()


class ClaimAnalysisView(APIView):
    """POST /api/analyze-claim/ - Analyze customer claim with RAG and tone analysis."""

    def post(self, request):
        """Analyze a customer claim and return policy recommendations and tone analysis."""
        serializer = ClaimAnalysisInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid input", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            claim_data = serializer.validated_data.copy()
            # Convert date to ISO string for the analyze_claim function
            claim_data["delivery_date"] = claim_data["delivery_date"].isoformat()
            result = analyze_claim(claim_data)
            return Response(result)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================
# Agent Feedback Endpoint
# ============================================================


class AgentFeedbackInputSerializer(ClaimAnalysisInputSerializer):
    """Serializer for agent feedback evaluation. Extends claim analysis with verification fields."""

    contract_number = serializers.CharField(max_length=100)
    claim_date = serializers.DateField()
    eligible = serializers.BooleanField()


class AgentFeedbackView(APIView):
    """POST /api/agent-feedback-deep/ - Evaluate agent's claim handling across 7 criteria (exhaustive, multi-step agent)."""

    def post(self, request):
        """Evaluate a store agent's claim handling and return structured feedback."""
        serializer = AgentFeedbackInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid input", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            feedback_data = serializer.validated_data.copy()
            # Convert date fields to ISO strings
            feedback_data["delivery_date"] = feedback_data["delivery_date"].isoformat()
            feedback_data["claim_date"] = feedback_data["claim_date"].isoformat()
            result = evaluate_agent_feedback(feedback_data)
            return Response(result)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AgentFeedbackOptimizedView(APIView):
    """POST /api/agent-feedback/ - Optimized: pre-fetched policies + single LLM call."""

    def post(self, request):
        serializer = AgentFeedbackInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid input", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            feedback_data = serializer.validated_data.copy()
            feedback_data["delivery_date"] = feedback_data["delivery_date"].isoformat()
            feedback_data["claim_date"] = feedback_data["claim_date"].isoformat()
            result = evaluate_agent_feedback_optimized(feedback_data)
            return Response(result)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )