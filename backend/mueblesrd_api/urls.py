"""
URL configuration for mueblesrd_api project.
"""

from django.urls import path, include

urlpatterns = [
    path('api/', include('chatbot.urls')),
]
