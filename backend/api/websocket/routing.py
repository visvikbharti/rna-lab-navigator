from django.urls import re_path
from . import consumers
from api.intelligence.knowledge_graph import KnowledgeGraphConsumer

websocket_urlpatterns = [
    re_path(r'ws/search/(?P<session_id>\w+)/$', consumers.SearchConsumer.as_asgi()),
    re_path(r'ws/collaborate/(?P<document_id>\w+)/$', consumers.CollaborationConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/knowledge-graph/$', KnowledgeGraphConsumer.as_asgi()),
]