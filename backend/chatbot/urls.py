"""
URL configuration for chatbot app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
]
