"""
URL configuration for chatbot app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('auth/token/', views.ObtainTokenView.as_view(), name='api-token'),
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
]
