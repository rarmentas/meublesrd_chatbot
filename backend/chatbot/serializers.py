"""
Serializers para documentación OpenAPI (drf-spectacular).
No se usan para validación en las vistas; solo definen el esquema en Swagger.
"""

from rest_framework import serializers


# ---------------------------------------------------------------------------
# Errores (400 con detalles de validación, 500 genérico)
# ---------------------------------------------------------------------------


class InvalidInputErrorSerializer(serializers.Serializer):
    """Respuesta 400 cuando la validación del body falla (p. ej. analyze-claim, agent-feedback)."""

    error = serializers.CharField(help_text="Mensaje de error, p. ej. 'Invalid input'.")
    details = serializers.DictField(
        allow_null=True,
        required=False,
        help_text="Detalle por campo: lista de mensajes de validación.",
    )


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------


class ChatRequestSerializer(serializers.Serializer):
    """Cuerpo esperado para POST /api/chat/."""

    query = serializers.CharField(help_text="Pregunta o mensaje del usuario para el chatbot.")


class ChatResponseSerializer(serializers.Serializer):
    """Respuesta exitosa de POST /api/chat/."""

    answer = serializers.CharField(help_text="Respuesta generada por el modelo.")
    sources = serializers.ListField(
        child=serializers.CharField(),
        help_text="Lista de fuentes o secciones usadas para la respuesta.",
    )


class ChatErrorSerializer(serializers.Serializer):
    """Respuesta de error (400 o 500)."""

    error = serializers.CharField(help_text="Mensaje de error.")


class HealthResponseSerializer(serializers.Serializer):
    """Respuesta de GET /api/health/."""

    status = serializers.CharField(help_text="Estado del servicio, p. ej. 'healthy'.")


class TokenRequestSerializer(serializers.Serializer):
    """Cuerpo para POST /api/auth/token/ (obtener token)."""

    username = serializers.CharField(help_text="Nombre de usuario Django.")
    password = serializers.CharField(style={'input_type': 'password'}, help_text="Contraseña.")


class TokenResponseSerializer(serializers.Serializer):
    """Respuesta de POST /api/auth/token/."""

    token = serializers.CharField(help_text="Token para usar en header: Authorization: Token <token>.")


# ---------------------------------------------------------------------------
# Analyze Claim (POST /api/analyze-claim/)
# ---------------------------------------------------------------------------


class ClaimSummarySerializer(serializers.Serializer):
    """Resumen de la reclamación en la respuesta de analyze-claim."""

    request_type = serializers.CharField()
    claim_type = serializers.CharField()
    product_type = serializers.CharField()
    damage_type = serializers.CharField()
    days_since_delivery = serializers.IntegerField(allow_null=True)


class ToneAnalysisSerializer(serializers.Serializer):
    """Análisis de tono del mensaje del cliente."""

    tone = serializers.CharField(help_text="Ej: neutral, frustrated, polite")
    confidence = serializers.FloatField()
    indicators = serializers.ListField(child=serializers.CharField())


class PolicyRecommendationItemSerializer(serializers.Serializer):
    """Una recomendación de política."""

    policy_reference = serializers.CharField()
    recommendation = serializers.CharField()
    priority = serializers.CharField(help_text="Ej: high, medium, low")


class CommunicationRecommendationsSerializer(serializers.Serializer):
    """Recomendaciones de comunicación para el agente."""

    approach = serializers.CharField()
    tips = serializers.ListField(child=serializers.CharField())
    suggested_opening = serializers.CharField(allow_blank=True)


class ClaimAnalysisResponseSerializer(serializers.Serializer):
    """Respuesta exitosa de POST /api/analyze-claim/."""

    claim_summary = ClaimSummarySerializer()
    tone_analysis = ToneAnalysisSerializer()
    policy_recommendations = serializers.ListField(
        child=PolicyRecommendationItemSerializer()
    )
    communication_recommendations = CommunicationRecommendationsSerializer()
    next_steps = serializers.ListField(child=serializers.CharField())
    sources = serializers.ListField(child=serializers.CharField())


# ---------------------------------------------------------------------------
# Agent Feedback (POST /api/agent-feedback/ y /api/agent-feedback-deep/)
# ---------------------------------------------------------------------------


class AgentClaimSummarySerializer(serializers.Serializer):
    """Resumen de reclamación en la respuesta de agent-feedback."""

    request_type = serializers.CharField()
    claim_type = serializers.CharField()
    product_type = serializers.CharField()
    damage_type = serializers.CharField()
    manufacturer = serializers.CharField(allow_blank=True)
    claim_date = serializers.CharField()
    days_since_delivery = serializers.IntegerField(allow_null=True)
    days_delivery_to_claim = serializers.IntegerField(allow_null=True)
    eligible_input = serializers.BooleanField()


class AgentFeedbackResponseSerializer(serializers.Serializer):
    """Respuesta exitosa de POST /api/agent-feedback/ y POST /api/agent-feedback-deep/."""

    claim_summary = AgentClaimSummarySerializer()
    criteria_evaluations = serializers.DictField(
        help_text="Evaluación por criterio: personal_information_consistency, "
                  "contract_ownership_verification, client_number_validation, "
                  "delivery_date_consistency, damage_classification_validation, "
                  "attachments_verification, warranty_eligibility_by_claim_date, "
                  "eligibility_decision. Cada uno tiene result y/o recommendation/explanation."
    )
    final_recommendation = serializers.CharField()
    final_eligibility = serializers.DictField(
        help_text="Objeto con isEligible (bool) y justification (string)."
    )
    sources = serializers.ListField(child=serializers.CharField())
