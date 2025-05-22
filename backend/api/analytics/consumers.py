"""
Django Channels WebSocket consumers for real-time analytics.
Provides real-time metrics and system status updates.
"""

import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

from .models import SystemMetric, SystemStatusLog
from .monitor import SystemMonitor

logger = logging.getLogger(__name__)


class MetricsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for streaming real-time metrics.
    Provides system performance and component health status.
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        # Check permission (admin users only)
        user = self.scope['user']
        if isinstance(user, AnonymousUser) or not user.is_staff:
            await self.close(code=4003)  # Permission denied
            return
        
        # Add to metrics group
        await self.channel_layer.group_add(
            'system_metrics',
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        await self.send_initial_data()
        
        # Start sending periodic updates
        self.update_task = asyncio.create_task(self.send_periodic_updates())
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Remove from metrics group
        await self.channel_layer.group_discard(
            'system_metrics',
            self.channel_name
        )
        
        # Cancel update task if running
        if hasattr(self, 'update_task') and not self.update_task.done():
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'get_health':
                # Get and send system health
                await self.send_system_health()
            elif action == 'get_metrics':
                # Get and send system metrics
                metric_type = data.get('metric_type')
                await self.send_metrics(metric_type)
            elif action == 'set_update_interval':
                # Update the interval for periodic updates
                interval = data.get('interval', 10)
                if hasattr(self, 'update_interval'):
                    self.update_interval = max(1, min(60, interval))  # 1-60 seconds
            else:
                logger.warning(f"Unknown action: {action}")
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def system_metrics(self, event):
        """Handle system metrics message from channel layer"""
        # Send metrics to WebSocket
        await self.send(text_data=json.dumps(event))
    
    async def system_health(self, event):
        """Handle system health message from channel layer"""
        # Send health status to WebSocket
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def get_latest_metrics(self, metric_type=None, limit=20):
        """Get latest metrics from database"""
        query = SystemMetric.objects.all().order_by('-timestamp')
        
        if metric_type:
            query = query.filter(metric_type=metric_type)
        
        metrics = list(query[:limit])
        
        return [
            {
                'metric_type': metric.metric_type,
                'value': metric.value,
                'unit': metric.unit,
                'timestamp': metric.timestamp.isoformat(),
            }
            for metric in metrics
        ]
    
    @database_sync_to_async
    def get_system_health(self):
        """Get system health summary"""
        return SystemMonitor.get_system_health_summary()
    
    async def send_initial_data(self):
        """Send initial data to client upon connection"""
        # Send system health
        await self.send_system_health()
        
        # Send latest metrics for important metric types
        for metric_type in ['cpu_usage', 'memory_usage', 'response_time']:
            await self.send_metrics(metric_type, limit=10)
    
    async def send_system_health(self):
        """Send system health status to client"""
        health = await self.get_system_health()
        
        # Convert datetime objects to ISO format strings for JSON serialization
        for component, status in health['component_status'].items():
            if 'last_updated' in status and status['last_updated']:
                status['last_updated'] = status['last_updated'].isoformat()
        
        for metric_name, metric_data in health['system_metrics'].items():
            if isinstance(metric_data, dict) and 'last_updated' in metric_data and metric_data['last_updated']:
                metric_data['last_updated'] = metric_data['last_updated'].isoformat()
        
        health['timestamp'] = health['timestamp'].isoformat()
        
        await self.send(text_data=json.dumps({
            'type': 'system_health',
            'data': health
        }))
    
    async def send_metrics(self, metric_type=None, limit=20):
        """Send metrics to client"""
        metrics = await self.get_latest_metrics(metric_type, limit)
        
        await self.send(text_data=json.dumps({
            'type': 'system_metrics',
            'metric_type': metric_type,
            'data': metrics
        }))
    
    async def send_periodic_updates(self):
        """Send periodic metrics updates to client"""
        self.update_interval = 10  # Default: 10 seconds
        
        try:
            while True:
                # Send system health every other update
                if (int(timezone.now().timestamp()) // self.update_interval) % 2 == 0:
                    await self.send_system_health()
                
                # Send latest metrics for important metric types
                metric_types = ['cpu_usage', 'memory_usage', 'response_time']
                for metric_type in metric_types:
                    await self.send_metrics(metric_type, limit=1)
                
                await asyncio.sleep(self.update_interval)
        except asyncio.CancelledError:
            # Task was cancelled - this is normal during disconnect
            pass
        except Exception as e:
            logger.error(f"Error in periodic update task: {e}")


class SystemEventsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for streaming system events.
    Provides real-time notification of significant system events.
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        # Check permission (admin users only)
        user = self.scope['user']
        if isinstance(user, AnonymousUser) or not user.is_staff:
            await self.close(code=4003)  # Permission denied
            return
        
        # Add to system events group
        await self.channel_layer.group_add(
            'system_events',
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial events list
        await self.send_recent_events()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Remove from system events group
        await self.channel_layer.group_discard(
            'system_events',
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'get_events':
                # Get and send recent events
                event_type = data.get('event_type')
                limit = data.get('limit', 20)
                await self.send_recent_events(event_type, limit)
            else:
                logger.warning(f"Unknown action: {action}")
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def system_event(self, event):
        """Handle system event message from channel layer"""
        # Send event to WebSocket
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def get_recent_events(self, event_type=None, limit=20):
        """Get recent system events from database"""
        from .models import SecurityEvent, AuditEvent
        
        # Combine security and audit events
        events = []
        
        # Get security events
        security_query = SecurityEvent.objects.all().order_by('-timestamp')
        if event_type:
            security_query = security_query.filter(event_type=event_type)
        
        security_events = list(security_query[:limit])
        for event in security_events:
            events.append({
                'id': f"security_{event.id}",
                'type': 'security',
                'event_type': event.event_type,
                'description': event.description,
                'timestamp': event.timestamp.isoformat(),
                'severity': event.severity,
                'is_resolved': event.is_resolved,
                'user': event.user.username if event.user else None,
            })
        
        # Get audit events
        audit_query = AuditEvent.objects.all().order_by('-timestamp')
        if event_type:
            audit_query = audit_query.filter(event_type=event_type)
        
        audit_events = list(audit_query[:limit])
        for event in audit_events:
            events.append({
                'id': f"audit_{event.id}",
                'type': 'audit',
                'event_type': event.event_type,
                'description': event.description,
                'timestamp': event.timestamp.isoformat(),
                'severity': event.severity,
                'user': event.user.username if event.user else None,
            })
        
        # Sort combined events by timestamp (newest first)
        events.sort(key=lambda e: e['timestamp'], reverse=True)
        
        return events[:limit]
    
    async def send_recent_events(self, event_type=None, limit=20):
        """Send recent events to client"""
        events = await self.get_recent_events(event_type, limit)
        
        await self.send(text_data=json.dumps({
            'type': 'system_events',
            'data': events
        }))