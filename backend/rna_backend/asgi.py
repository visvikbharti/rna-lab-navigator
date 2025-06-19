"""
ASGI config for rna_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rna_backend.settings")

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from api.analytics.routing import websocket_urlpatterns as analytics_ws
from api.ingestion.routing import websocket_urlpatterns as ingestion_ws

# Combine all WebSocket patterns
websocket_urlpatterns = []
try:
    websocket_urlpatterns.extend(analytics_ws)
except:
    pass
try:
    websocket_urlpatterns.extend(ingestion_ws)
except:
    pass

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})