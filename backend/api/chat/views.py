"""
Chat views for conversational interface.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
import uuid
from django.utils import timezone

from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from api.search.real_rag import perform_rag_query


class ChatSessionView(APIView):
    """Manage chat sessions."""
    permission_classes = [AllowAny]
    
    def get(self, request, session_id=None):
        """Get chat session(s)."""
        if session_id:
            # Get specific session with messages
            session = get_object_or_404(ChatSession, id=session_id)
            messages = session.messages.all()
            
            return Response({
                'session': ChatSessionSerializer(session).data,
                'messages': ChatMessageSerializer(messages, many=True).data
            })
        else:
            # List all sessions
            sessions = ChatSession.objects.filter(is_active=True)
            if request.user.is_authenticated:
                sessions = sessions.filter(user=request.user)
            else:
                # For anonymous users, only show sessions from the last 24 hours
                last_24h = timezone.now() - timezone.timedelta(hours=24)
                sessions = sessions.filter(created_at__gte=last_24h, user__isnull=True)
            
            return Response({
                'sessions': ChatSessionSerializer(sessions, many=True).data
            })
    
    def post(self, request):
        """Create a new chat session."""
        session = ChatSession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            title=request.data.get('title', 'New Chat')
        )
        
        # Add initial system message
        ChatMessage.objects.create(
            session=session,
            role='system',
            content='Welcome to RNA Lab Navigator! I can help you explore research papers, protocols, and theses from Dr. Chakraborty\'s lab. Ask me anything!'
        )
        
        return Response({
            'session': ChatSessionSerializer(session).data
        }, status=status.HTTP_201_CREATED)
    
    def patch(self, request, session_id):
        """Update session title."""
        session = get_object_or_404(ChatSession, id=session_id)
        
        if 'title' in request.data:
            session.title = request.data['title']
            session.save()
        
        return Response({
            'session': ChatSessionSerializer(session).data
        })
    
    def delete(self, request, session_id):
        """Archive a session."""
        session = get_object_or_404(ChatSession, id=session_id)
        session.is_active = False
        session.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChatMessageView(APIView):
    """Handle chat messages and RAG queries."""
    permission_classes = [AllowAny]
    
    def post(self, request, session_id):
        """Send a message and get AI response."""
        session = get_object_or_404(ChatSession, id=session_id)
        
        # Validate message
        content = request.data.get('content', '').strip()
        if not content:
            return Response(
                {'error': 'Message content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user message
        user_message = ChatMessage.objects.create(
            session=session,
            role='user',
            content=content
        )
        
        # Get conversation context (last 5 messages)
        recent_messages = session.messages.filter(
            role__in=['user', 'assistant']
        ).order_by('-created_at')[:5][::-1]
        
        # Build context for RAG
        context = self._build_context(recent_messages, content)
        
        try:
            # Perform RAG query with context
            rag_result = perform_rag_query(
                context['query'],
                doc_type=request.data.get('doc_type', 'all')
            )
            
            # Create assistant response
            assistant_message = ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=rag_result['answer'],
                metadata={
                    'sources': rag_result.get('sources', []),
                    'confidence_score': rag_result.get('confidence_score', 0),
                    'search_results': rag_result.get('search_results', [])[:3],  # Top 3
                    'processing_time': rag_result.get('processing_time', 0)
                }
            )
            
            # Update session
            session.updated_at = timezone.now()
            if session.title == 'New Chat' and len(content.split()) > 3:
                # Auto-generate title from first message
                session.title = ' '.join(content.split()[:6]) + '...'
            session.save()
            
            return Response({
                'user_message': ChatMessageSerializer(user_message).data,
                'assistant_message': ChatMessageSerializer(assistant_message).data,
                'session': ChatSessionSerializer(session).data
            })
            
        except Exception as e:
            # Create error response
            error_message = ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=f"I apologize, but I encountered an error while processing your question. Please try again.",
                metadata={'error': str(e)}
            )
            
            return Response({
                'user_message': ChatMessageSerializer(user_message).data,
                'assistant_message': ChatMessageSerializer(error_message).data,
                'error': True
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _build_context(self, recent_messages, current_query):
        """Build context from conversation history."""
        # If this is the first message, just use it
        if not recent_messages:
            return {'query': current_query, 'context': ''}
        
        # Build conversation context
        context_parts = []
        for msg in recent_messages:
            if msg.role == 'user':
                context_parts.append(f"User: {msg.content}")
            else:
                # Include brief summary of previous answers
                context_parts.append(f"Assistant: {msg.content[:200]}...")
        
        # Create contextual query
        context_text = '\n'.join(context_parts[-4:])  # Last 2 exchanges
        
        # Check if current query references previous context
        reference_words = ['it', 'this', 'that', 'those', 'these', 'the same', 
                          'also', 'more', 'additionally', 'furthermore']
        
        needs_context = any(word in current_query.lower() for word in reference_words)
        
        if needs_context and context_parts:
            # Enhance query with context
            contextual_query = f"Based on our previous discussion about: {context_parts[-1].split(': ', 1)[1][:100]}... {current_query}"
        else:
            contextual_query = current_query
        
        return {
            'query': contextual_query,
            'context': context_text
        }