import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .services import KnowledgeGraphService

logger = logging.getLogger(__name__)


class KnowledgeGraphConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time knowledge graph updates"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.room_group_name = 'knowledge_graph'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial graph data
        await self.send_initial_data()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_graph':
                await self.send_graph_data(data.get('filters', {}))
            
            elif message_type == 'get_node_details':
                node_id = data.get('node_id')
                if node_id:
                    await self.send_node_details(node_id)
            
            elif message_type == 'request_clustering':
                await self.trigger_clustering()
            
            elif message_type == 'discover_connections':
                node_id = data.get('node_id')
                if node_id:
                    await self.discover_node_connections(node_id)
        
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON")
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            await self.send_error(str(e))
    
    async def graph_update(self, event):
        """Handle graph update events from channel layer"""
        # Send update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'update',
            'data': event['update']
        }))
    
    @database_sync_to_async
    def get_graph_data(self, filters):
        """Get graph data from service"""
        service = KnowledgeGraphService()
        return service.get_graph_data(
            node_types=filters.get('node_types'),
            edge_types=filters.get('edge_types'),
            cluster_id=filters.get('cluster_id')
        )
    
    @database_sync_to_async
    def get_node_details(self, node_id):
        """Get node details from service"""
        service = KnowledgeGraphService()
        return service.get_node_details(node_id)
    
    @database_sync_to_async
    def trigger_clustering_sync(self):
        """Trigger clustering synchronously"""
        service = KnowledgeGraphService()
        service.cluster_nodes()
    
    @database_sync_to_async
    def discover_connections_sync(self, node_id):
        """Discover connections for a node"""
        from .models import KnowledgeNode
        service = KnowledgeGraphService()
        
        try:
            node = KnowledgeNode.objects.get(node_id=node_id)
            service.discover_connections(node)
        except KnowledgeNode.DoesNotExist:
            pass
    
    async def send_initial_data(self):
        """Send initial graph data when client connects"""
        graph_data = await self.get_graph_data({})
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'data': graph_data
        }))
    
    async def send_graph_data(self, filters):
        """Send filtered graph data"""
        graph_data = await self.get_graph_data(filters)
        await self.send(text_data=json.dumps({
            'type': 'graph_data',
            'data': graph_data
        }))
    
    async def send_node_details(self, node_id):
        """Send node details"""
        details = await self.get_node_details(node_id)
        if details:
            await self.send(text_data=json.dumps({
                'type': 'node_details',
                'data': details
            }))
        else:
            await self.send_error(f"Node {node_id} not found")
    
    async def trigger_clustering(self):
        """Trigger graph clustering"""
        await self.trigger_clustering_sync()
        await self.send(text_data=json.dumps({
            'type': 'clustering_complete',
            'message': 'Graph clustering completed'
        }))
    
    async def discover_node_connections(self, node_id):
        """Discover connections for a specific node"""
        await self.discover_connections_sync(node_id)
        await self.send(text_data=json.dumps({
            'type': 'connections_discovered',
            'message': f'Connections discovered for node {node_id}'
        }))
    
    async def send_error(self, message):
        """Send error message"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))