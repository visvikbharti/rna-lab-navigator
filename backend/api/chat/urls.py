"""
URL patterns for chat API.
"""

from django.urls import path
from .views import ChatSessionView, ChatMessageView

urlpatterns = [
    # Chat sessions
    path('sessions/', ChatSessionView.as_view(), name='chat-sessions'),
    path('sessions/<uuid:session_id>/', ChatSessionView.as_view(), name='chat-session-detail'),
    
    # Chat messages
    path('sessions/<uuid:session_id>/messages/', ChatMessageView.as_view(), name='chat-messages'),
]