"""
Serializers para documentación OpenAPI (drf-spectacular).
No se usan para validación en las vistas; solo definen el esquema en Swagger.
"""

from rest_framework import serializers


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
