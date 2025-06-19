import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
import asyncio
from datetime import datetime

class SearchConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time search updates."""
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        self.session_group_name = f'search_{self.session_id}'
        
        # Join session group
        await self.channel_layer.group_add(
            self.session_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial connection confirmation
        await self.send_json({
            'type': 'connection_established',
            'session_id': self.session_id,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def disconnect(self, close_code):
        # Leave session group
        await self.channel_layer.group_discard(
            self.session_group_name,
            self.channel_name
        )
    
    async def receive_json(self, content):
        """Handle incoming WebSocket messages."""
        message_type = content.get('type')
        
        if message_type == 'search_progress':
            # Broadcast search progress to group
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'search_progress',
                    'message': content.get('message'),
                    'progress': content.get('progress', 0),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        
        elif message_type == 'search_complete':
            # Notify completion
            await self.channel_layer.group_send(
                self.session_group_name,
                {
                    'type': 'search_complete',
                    'results_count': content.get('results_count', 0),
                    'query_id': content.get('query_id'),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
    
    async def search_progress(self, event):
        """Send search progress to WebSocket."""
        await self.send_json({
            'type': 'search_progress',
            'message': event['message'],
            'progress': event['progress'],
            'timestamp': event['timestamp']
        })
    
    async def search_complete(self, event):
        """Send search completion to WebSocket."""
        await self.send_json({
            'type': 'search_complete',
            'results_count': event['results_count'],
            'query_id': event['query_id'],
            'timestamp': event['timestamp']
        })
    
    async def new_result(self, event):
        """Send new search result to WebSocket."""
        await self.send_json({
            'type': 'new_result',
            'result': event['result'],
            'timestamp': event['timestamp']
        })


class CollaborationConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for document collaboration."""
    
    async def connect(self):
        self.document_id = self.scope['url_route']['kwargs'].get('document_id')
        self.document_group_name = f'doc_{self.document_id}'
        self.user = self.scope['user']
        
        # Join document group
        await self.channel_layer.group_add(
            self.document_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.document_group_name,
            {
                'type': 'user_joined',
                'user_id': str(self.user.id) if self.user.is_authenticated else 'anonymous',
                'username': self.user.username if self.user.is_authenticated else 'Anonymous',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    async def disconnect(self, close_code):
        # Notify others that user left
        await self.channel_layer.group_send(
            self.document_group_name,
            {
                'type': 'user_left',
                'user_id': str(self.user.id) if self.user.is_authenticated else 'anonymous',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Leave document group
        await self.channel_layer.group_discard(
            self.document_group_name,
            self.channel_name
        )
    
    async def receive_json(self, content):
        """Handle incoming collaboration messages."""
        message_type = content.get('type')
        
        if message_type == 'cursor_position':
            # Broadcast cursor position
            await self.channel_layer.group_send(
                self.document_group_name,
                {
                    'type': 'cursor_update',
                    'user_id': str(self.user.id) if self.user.is_authenticated else 'anonymous',
                    'position': content.get('position'),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        
        elif message_type == 'selection':
            # Broadcast text selection
            await self.channel_layer.group_send(
                self.document_group_name,
                {
                    'type': 'selection_update',
                    'user_id': str(self.user.id) if self.user.is_authenticated else 'anonymous',
                    'selection': content.get('selection'),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
    
    async def user_joined(self, event):
        """Send user joined notification."""
        if event['user_id'] != str(self.user.id if self.user.is_authenticated else 'anonymous'):
            await self.send_json({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'username': event['username'],
                'timestamp': event['timestamp']
            })
    
    async def user_left(self, event):
        """Send user left notification."""
        if event['user_id'] != str(self.user.id if self.user.is_authenticated else 'anonymous'):
            await self.send_json({
                'type': 'user_left',
                'user_id': event['user_id'],
                'timestamp': event['timestamp']
            })
    
    async def cursor_update(self, event):
        """Send cursor position update."""
        if event['user_id'] != str(self.user.id if self.user.is_authenticated else 'anonymous'):
            await self.send_json({
                'type': 'cursor_update',
                'user_id': event['user_id'],
                'position': event['position'],
                'timestamp': event['timestamp']
            })
    
    async def selection_update(self, event):
        """Send selection update."""
        if event['user_id'] != str(self.user.id if self.user.is_authenticated else 'anonymous'):
            await self.send_json({
                'type': 'selection_update',
                'user_id': event['user_id'],
                'selection': event['selection'],
                'timestamp': event['timestamp']
            })


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time notifications."""
    
    async def connect(self):
        self.user = self.scope['user']
        
        if self.user.is_authenticated:
            self.user_group_name = f'notifications_{self.user.id}'
            
            # Join user-specific notification group
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            # Join global notification group
            await self.channel_layer.group_add(
                'notifications_global',
                self.channel_name
            )
            
            await self.accept()
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            # Leave groups
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            await self.channel_layer.group_discard(
                'notifications_global',
                self.channel_name
            )
    
    async def notification(self, event):
        """Send notification to WebSocket."""
        await self.send_json({
            'type': 'notification',
            'title': event['title'],
            'message': event['message'],
            'level': event.get('level', 'info'),
            'timestamp': event['timestamp']
        })
    
    async def system_update(self, event):
        """Send system update notification."""
        await self.send_json({
            'type': 'system_update',
            'message': event['message'],
            'timestamp': event['timestamp']
        })