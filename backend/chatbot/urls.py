"""
URL configuration for chatbot app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
    path('analyze-claim/', views.ClaimAnalysisView.as_view(), name='analyze-claim'),
    path('agent-feedback/', views.AgentFeedbackOptimizedView.as_view(), name='agent-feedback'),
    path('agent-feedback-deep/', views.AgentFeedbackView.as_view(), name='agent-feedback-deep'),
]
