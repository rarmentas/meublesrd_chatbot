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

    claim_type = serializers.CharField()
    product_type = serializers.CharField()
    damage_type = serializers.CharField()
    days_since_delivery = serializers.IntegerField(allow_null=True)
    has_attachments = serializers.BooleanField(
        help_text="Si el cliente adjuntó fotos u otra evidencia."
    )


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
    ownership_framing = serializers.CharField(
        allow_blank=True,
        required=False,
        help_text="Frase de responsabilidad: 'We take responsibility for...'",
    )


class SolutionOptionSerializer(serializers.Serializer):
    """Una opción de solución para el cliente."""

    option_label = serializers.CharField(help_text="Ej: Option A: Replacement")
    description = serializers.CharField()
    timeline = serializers.CharField(allow_blank=True)
    trade_offs = serializers.CharField(allow_blank=True)


class CommunicationRecommendationsSerializer(serializers.Serializer):
    """Recomendaciones de comunicación para el agente."""

    approach = serializers.CharField(
        help_text="standard, empathetic, de-escalation o formal"
    )
    solution_options = serializers.ListField(
        child=SolutionOptionSerializer(),
        required=False,
        allow_empty=True,
        help_text="2-3 opciones de solución para ofrecer al cliente.",
    )
    tips = serializers.ListField(child=serializers.CharField())
    suggested_opening = serializers.CharField(allow_blank=True)


class AnticipationStepSerializer(serializers.Serializer):
    """Paso de anticipación (Principio GAC 3)."""

    potential_future_issue = serializers.CharField()
    preventive_action = serializers.CharField()
    follow_up_timeline = serializers.CharField(allow_blank=True)


class GacAssessmentSerializer(serializers.Serializer):
    """Evaluación GAC (principios de servicio al cliente)."""

    ownership_score = serializers.CharField(
        help_text="strong, moderate o weak"
    )
    ownership_evidence = serializers.CharField(allow_blank=True)
    options_score = serializers.CharField(help_text="strong, moderate o weak")
    options_evidence = serializers.CharField(allow_blank=True)
    anticipation_score = serializers.CharField(help_text="strong, moderate o weak")
    anticipation_evidence = serializers.CharField(allow_blank=True)


class AttachmentsVerificationSerializer(serializers.Serializer):
    """Verificación de adjuntos según política (respuesta de analyze-claim)."""

    result = serializers.BooleanField(
        help_text="True si los adjuntos cumplen con la política, False si faltan o son inadecuados."
    )
    recommendation = serializers.CharField(
        help_text="Explicación de si los adjuntos son adecuados o qué se requiere."
    )


class ClaimAnalysisResponseSerializer(serializers.Serializer):
    """Respuesta exitosa de POST /api/analyze-claim/."""

    claim_summary = ClaimSummarySerializer()
    tone_analysis = ToneAnalysisSerializer()
    policy_recommendations = serializers.ListField(
        child=PolicyRecommendationItemSerializer()
    )
    communication_recommendations = CommunicationRecommendationsSerializer()
    next_steps = serializers.ListField(child=serializers.CharField())
    anticipation_steps = serializers.ListField(
        child=AnticipationStepSerializer(),
        required=False,
        allow_empty=True,
        help_text="Pasos preventivos y seguimiento futuro (Principio GAC 3).",
    )
    attachments_verification = AttachmentsVerificationSerializer()
    gac_assessment = GacAssessmentSerializer(
        required=False,
        allow_null=True,
        help_text="Evaluación de los 3 principios GAC en las recomendaciones.",
    )
    sources = serializers.ListField(child=serializers.CharField())


# ---------------------------------------------------------------------------
# Agent Feedback (POST /api/agent-feedback/ y /api/agent-feedback-deep/)
# ---------------------------------------------------------------------------


class AgentClaimSummarySerializer(serializers.Serializer):
    """Resumen de reclamación en la respuesta de agent-feedback."""

    claim_type = serializers.CharField()
    product_type = serializers.CharField()
    damage_type = serializers.CharField()
    manufacturer = serializers.CharField(allow_blank=True)
    claim_date = serializers.CharField()
    days_since_delivery = serializers.IntegerField(allow_null=True)
    days_delivery_to_claim = serializers.IntegerField(allow_null=True)
    eligible_input = serializers.BooleanField()


class FinalRecommendationSerializer(serializers.Serializer):
    """Recomendación final para el agente (coaching)."""

    summary = serializers.CharField(help_text="Resumen general para el agente")
    ownership_coaching = serializers.CharField(
        help_text="Cómo demostrar mejor responsabilidad radical"
    )
    options_coaching = serializers.CharField(
        help_text="Cómo presentar múltiples opciones de solución"
    )
    anticipation_coaching = serializers.CharField(
        help_text="Qué problemas futuros abordar proactivamente"
    )


class GacPrincipleEvaluationSerializer(serializers.Serializer):
    """Evaluación de un principio GAC."""

    demonstrated = serializers.BooleanField()
    feedback = serializers.CharField()


class GacEvaluationSerializer(serializers.Serializer):
    """Evaluación GAC del manejo del agente."""

    ownership = GacPrincipleEvaluationSerializer()
    solution_options = GacPrincipleEvaluationSerializer()
    future_anticipation = GacPrincipleEvaluationSerializer()


class AgentFeedbackResponseSerializer(serializers.Serializer):
    """Respuesta exitosa de POST /api/agent-feedback/ y POST /api/agent-feedback-deep/."""

    claim_summary = AgentClaimSummarySerializer()
    criteria_evaluations = serializers.DictField(
        help_text="Evaluación por criterio (5): contract_verification "
                  "(result, explanation), delivery_date (result, recommendation), "
                  "damage_classification_validation, attachments_verification, "
                  "eligibility_decision (isDecisionCorrect, explanation)."
    )
    final_recommendation = FinalRecommendationSerializer()
    gac_evaluation = GacEvaluationSerializer(
        required=False,
        allow_null=True,
        help_text="Evaluación de los 3 principios GAC en el manejo del agente.",
    )
    final_eligibility = serializers.DictField(
        help_text="Objeto con isEligible (bool) y justification (string)."
    )
    sources = serializers.ListField(child=serializers.CharField())
