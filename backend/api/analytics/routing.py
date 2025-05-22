"""
WebSocket routing configuration for analytics.
"""

from django.urls import path
from .consumers import MetricsConsumer, SystemEventsConsumer

websocket_urlpatterns = [
    path('ws/analytics/metrics/', MetricsConsumer.as_asgi()),
    path('ws/analytics/events/', SystemEventsConsumer.as_asgi()),
]