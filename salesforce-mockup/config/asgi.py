"""
ASGI config for Meubles RD Salesforce mockup.
Permite servir la app con uvicorn en producción.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_asgi_application()
