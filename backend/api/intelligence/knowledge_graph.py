"""
Real-time Knowledge Graph System
Maintains and updates a living graph of research connections
"""
import json
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio

import networkx as nx
import numpy as np
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q, Count
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

from api.models import Document, QueryHistory
from api.intelligence.cross_paper_insights import CrossPaperInsightGenerator
from api.intelligence.knowledge_gaps import KnowledgeGapAnalyzer
from api.search.services import SearchService

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Manages the real-time knowledge graph"""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.insight_generator = CrossPaperInsightGenerator()
        self.gap_analyzer = KnowledgeGapAnalyzer()
        self.search_service = SearchService()
        self._initialize_graph()
        
    def _initialize_graph(self):
        """Initialize graph from existing documents"""
        cache_key = "knowledge_graph:initialized"
        if cache.get(cache_key):
            self._load_from_cache()
            return
            
        # Load all documents
        documents = Document.objects.all()
        for doc in documents:
            self.add_document_node(doc)
            
        # Generate initial connections
        self._generate_all_connections()
        
        # Cache the graph
        self._save_to_cache()
        cache.set(cache_key, True, 3600)
        
    def add_document_node(self, document: Document) -> str:
        """Add a document as a node in the graph"""
        node_id = f"doc_{document.id}"
        
        # Extract key attributes
        node_attrs = {
            'id': document.id,
            'type': 'document',
            'doc_type': document.doc_type,
            'title': document.title,
            'author': document.author,
            'year': document.year,
            'created_at': document.created_at.isoformat(),
            'keywords': self._extract_keywords(document),
            'entities': self._extract_entities(document),
            'methods': self._extract_methods(document)
        }
        
        self.graph.add_node(node_id, **node_attrs)
        return node_id
        
    def add_connection(self, node1: str, node2: str, 
                      connection_type: str, metadata: Dict) -> None:
        """Add or update a connection between nodes"""
        if self.graph.has_edge(node1, node2):
            # Update existing edge
            edge_data = self.graph[node1][node2]
            if 'connections' not in edge_data:
                edge_data['connections'] = []
            edge_data['connections'].append({
                'type': connection_type,
                'metadata': metadata,
                'created_at': datetime.now().isoformat()
            })
            edge_data['weight'] = len(edge_data['connections'])
        else:
            # Create new edge
            self.graph.add_edge(node1, node2, 
                              connections=[{
                                  'type': connection_type,
                                  'metadata': metadata,
                                  'created_at': datetime.now().isoformat()
                              }],
                              weight=1)
                              
    def get_node_connections(self, node_id: str, 
                           connection_types: Optional[List[str]] = None) -> List[Dict]:
        """Get all connections for a node"""
        connections = []
        
        if node_id not in self.graph:
            return connections
            
        for neighbor in self.graph.neighbors(node_id):
            edge_data = self.graph[node_id][neighbor]
            for conn in edge_data.get('connections', []):
                if not connection_types or conn['type'] in connection_types:
                    connections.append({
                        'target': neighbor,
                        'type': conn['type'],
                        'metadata': conn['metadata'],
                        'created_at': conn['created_at']
                    })
                    
        return connections
        
    def find_shortest_path(self, node1: str, node2: str) -> Optional[List[str]]:
        """Find shortest path between two nodes"""
        try:
            return nx.shortest_path(self.graph, node1, node2)
        except nx.NetworkXNoPath:
            return None
            
    def get_node_clusters(self, min_size: int = 3) -> List[Set[str]]:
        """Get clusters of highly connected nodes"""
        # Use Louvain community detection
        import community as community_louvain
        
        # Convert to undirected for community detection
        G_undirected = self.graph.to_undirected()
        partition = community_louvain.best_partition(G_undirected)
        
        # Group nodes by community
        communities = defaultdict(set)
        for node, comm_id in partition.items():
            communities[comm_id].add(node)
            
        # Filter by minimum size
        return [nodes for nodes in communities.values() if len(nodes) >= min_size]
        
    def get_important_nodes(self, metric: str = 'betweenness', top_n: int = 10) -> List[Tuple[str, float]]:
        """Get most important nodes by various metrics"""
        if metric == 'betweenness':
            centrality = nx.betweenness_centrality(self.graph)
        elif metric == 'closeness':
            centrality = nx.closeness_centrality(self.graph)
        elif metric == 'degree':
            centrality = nx.degree_centrality(self.graph)
        elif metric == 'eigenvector':
            centrality = nx.eigenvector_centrality(self.graph, max_iter=1000)
        else:
            centrality = nx.degree_centrality(self.graph)
            
        # Sort by centrality score
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_n]
        
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get overall graph statistics"""
        stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'is_connected': nx.is_connected(self.graph),
            'number_of_components': nx.number_connected_components(self.graph),
            'average_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0,
            'average_clustering': nx.average_clustering(self.graph),
        }
        
        # Node type distribution
        node_types = defaultdict(int)
        for node, attrs in self.graph.nodes(data=True):
            node_types[attrs.get('doc_type', 'unknown')] += 1
        stats['node_type_distribution'] = dict(node_types)
        
        # Connection type distribution
        connection_types = defaultdict(int)
        for u, v, data in self.graph.edges(data=True):
            for conn in data.get('connections', []):
                connection_types[conn['type']] += 1
        stats['connection_type_distribution'] = dict(connection_types)
        
        return stats
        
    def get_subgraph(self, center_node: str, depth: int = 2) -> nx.Graph:
        """Get subgraph around a specific node"""
        nodes = {center_node}
        
        # BFS to find nodes within depth
        queue = deque([(center_node, 0)])
        visited = {center_node}
        
        while queue:
            node, d = queue.popleft()
            if d < depth:
                for neighbor in self.graph.neighbors(node):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        nodes.add(neighbor)
                        queue.append((neighbor, d + 1))
                        
        return self.graph.subgraph(nodes)
        
    def search_nodes(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for nodes matching query"""
        results = []
        query_lower = query.lower()
        
        for node, attrs in self.graph.nodes(data=True):
            score = 0
            
            # Check title
            if query_lower in attrs.get('title', '').lower():
                score += 10
                
            # Check keywords
            keywords = attrs.get('keywords', [])
            for keyword in keywords:
                if query_lower in keyword.lower():
                    score += 5
                    
            # Check entities
            entities = attrs.get('entities', [])
            for entity in entities:
                if query_lower in entity.lower():
                    score += 3
                    
            if score > 0:
                results.append({
                    'node_id': node,
                    'title': attrs.get('title', ''),
                    'type': attrs.get('doc_type', ''),
                    'score': score,
                    'year': attrs.get('year', ''),
                    'degree': self.graph.degree(node)
                })
                
        # Sort by score and limit
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
        
    def detect_research_trends(self, time_window_days: int = 365) -> Dict[str, Any]:
        """Detect trending topics and connections"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_window_days)
        
        # Get recent nodes
        recent_nodes = []
        for node, attrs in self.graph.nodes(data=True):
            created_at = datetime.fromisoformat(attrs.get('created_at', ''))
            if start_date <= created_at <= end_date:
                recent_nodes.append((node, attrs))
                
        # Analyze keywords and entities
        keyword_counts = defaultdict(int)
        entity_counts = defaultdict(int)
        
        for node, attrs in recent_nodes:
            for keyword in attrs.get('keywords', []):
                keyword_counts[keyword] += 1
            for entity in attrs.get('entities', []):
                entity_counts[entity] += 1
                
        # Find trending connections
        recent_connections = defaultdict(int)
        for u, v, data in self.graph.edges(data=True):
            for conn in data.get('connections', []):
                conn_date = datetime.fromisoformat(conn['created_at'])
                if start_date <= conn_date <= end_date:
                    recent_connections[conn['type']] += 1
                    
        return {
            'trending_keywords': sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'trending_entities': sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'trending_connections': sorted(recent_connections.items(), key=lambda x: x[1], reverse=True)[:5],
            'new_nodes_count': len(recent_nodes),
            'time_window': time_window_days
        }
        
    def suggest_connections(self, node_id: str, limit: int = 5) -> List[Dict]:
        """Suggest potential connections for a node"""
        if node_id not in self.graph:
            return []
            
        node_attrs = self.graph.nodes[node_id]
        suggestions = []
        
        # Get node's keywords and entities
        node_keywords = set(node_attrs.get('keywords', []))
        node_entities = set(node_attrs.get('entities', []))
        node_methods = set(node_attrs.get('methods', []))
        
        # Find nodes with similar attributes but no direct connection
        for other_node, other_attrs in self.graph.nodes(data=True):
            if other_node == node_id or self.graph.has_edge(node_id, other_node):
                continue
                
            # Calculate similarity
            other_keywords = set(other_attrs.get('keywords', []))
            other_entities = set(other_attrs.get('entities', []))
            other_methods = set(other_attrs.get('methods', []))
            
            keyword_overlap = len(node_keywords & other_keywords)
            entity_overlap = len(node_entities & other_entities)
            method_overlap = len(node_methods & other_methods)
            
            similarity_score = keyword_overlap * 2 + entity_overlap * 3 + method_overlap * 2
            
            if similarity_score > 0:
                suggestions.append({
                    'node_id': other_node,
                    'title': other_attrs.get('title', ''),
                    'similarity_score': similarity_score,
                    'shared_keywords': list(node_keywords & other_keywords),
                    'shared_entities': list(node_entities & other_entities),
                    'shared_methods': list(node_methods & other_methods),
                    'potential_connection_types': self._infer_connection_types(
                        node_attrs, other_attrs
                    )
                })
                
        # Sort by similarity score
        suggestions.sort(key=lambda x: x['similarity_score'], reverse=True)
        return suggestions[:limit]
        
    def export_for_visualization(self) -> Dict[str, Any]:
        """Export graph data for frontend visualization"""
        nodes = []
        edges = []
        
        # Export nodes
        for node_id, attrs in self.graph.nodes(data=True):
            nodes.append({
                'id': node_id,
                'label': attrs.get('title', '')[:50] + '...' if len(attrs.get('title', '')) > 50 else attrs.get('title', ''),
                'type': attrs.get('doc_type', 'unknown'),
                'year': attrs.get('year', ''),
                'degree': self.graph.degree(node_id),
                'attributes': {
                    'keywords': attrs.get('keywords', [])[:5],
                    'entities': attrs.get('entities', [])[:5]
                }
            })
            
        # Export edges
        for u, v, data in self.graph.edges(data=True):
            connections = data.get('connections', [])
            primary_type = connections[0]['type'] if connections else 'related'
            
            edges.append({
                'source': u,
                'target': v,
                'type': primary_type,
                'weight': data.get('weight', 1),
                'connection_count': len(connections),
                'connection_types': list(set(c['type'] for c in connections))
            })
            
        # Add layout positions using force-directed layout
        pos = nx.spring_layout(self.graph, k=2, iterations=50)
        for node in nodes:
            if node['id'] in pos:
                node['x'] = float(pos[node['id']][0])
                node['y'] = float(pos[node['id']][1])
                
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': self.get_graph_stats()
        }
        
    # Helper methods
    def _extract_keywords(self, document: Document) -> List[str]:
        """Extract keywords from document"""
        # Use cached result if available
        cache_key = f"doc_keywords:{document.id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
            
        # Simple keyword extraction (can be enhanced with NLP)
        text = f"{document.title} {document.abstract}"
        keywords = []
        
        # Extract based on frequency and importance
        # This is a simplified version - could use TF-IDF or other methods
        import re
        from collections import Counter
        
        words = re.findall(r'\b\w+\b', text.lower())
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = [w for w in words if w not in stopwords and len(w) > 3]
        
        word_counts = Counter(words)
        keywords = [word for word, _ in word_counts.most_common(10)]
        
        cache.set(cache_key, keywords, 86400)
        return keywords
        
    def _extract_entities(self, document: Document) -> List[str]:
        """Extract named entities from document"""
        cache_key = f"doc_entities:{document.id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
            
        # Simplified entity extraction
        entities = []
        text = f"{document.title} {document.abstract}"
        
        # Look for common patterns (genes, proteins, diseases)
        gene_pattern = r'\b[A-Z][A-Z0-9]{2,}\b'
        genes = re.findall(gene_pattern, text)
        entities.extend(genes[:5])
        
        cache.set(cache_key, entities, 86400)
        return entities
        
    def _extract_methods(self, document: Document) -> List[str]:
        """Extract methods from document"""
        cache_key = f"doc_methods:{document.id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
            
        # Common method keywords
        method_keywords = [
            'PCR', 'Western blot', 'CRISPR', 'RNA-seq', 'ChIP-seq',
            'immunofluorescence', 'flow cytometry', 'mass spectrometry',
            'crystallography', 'microscopy'
        ]
        
        methods = []
        text = document.content[:2000] if document.content else document.abstract
        text_lower = text.lower()
        
        for method in method_keywords:
            if method.lower() in text_lower:
                methods.append(method)
                
        cache.set(cache_key, methods, 86400)
        return methods
        
    def _generate_all_connections(self):
        """Generate connections between all documents"""
        documents = list(self.graph.nodes())
        
        for i, doc1 in enumerate(documents):
            for doc2 in documents[i+1:]:
                self._generate_connection(doc1, doc2)
                
    def _generate_connection(self, node1: str, node2: str):
        """Generate connection between two nodes if relevant"""
        attrs1 = self.graph.nodes[node1]
        attrs2 = self.graph.nodes[node2]
        
        # Check for shared elements
        shared_keywords = set(attrs1.get('keywords', [])) & set(attrs2.get('keywords', []))
        shared_entities = set(attrs1.get('entities', [])) & set(attrs2.get('entities', []))
        shared_methods = set(attrs1.get('methods', [])) & set(attrs2.get('methods', []))
        
        if shared_keywords or shared_entities or shared_methods:
            connection_type = self._determine_connection_type(
                shared_keywords, shared_entities, shared_methods
            )
            
            self.add_connection(node1, node2, connection_type, {
                'shared_keywords': list(shared_keywords),
                'shared_entities': list(shared_entities),
                'shared_methods': list(shared_methods)
            })
            
    def _determine_connection_type(self, keywords, entities, methods) -> str:
        """Determine the type of connection based on shared elements"""
        if methods:
            return 'methodological'
        elif entities:
            return 'entity_based'
        elif keywords:
            return 'topic_related'
        else:
            return 'related'
            
    def _infer_connection_types(self, attrs1: Dict, attrs2: Dict) -> List[str]:
        """Infer potential connection types between nodes"""
        types = []
        
        if attrs1.get('doc_type') == 'paper' and attrs2.get('doc_type') == 'paper':
            types.extend(['citation', 'complementary', 'contradictory'])
            
        if attrs1.get('doc_type') == 'protocol' or attrs2.get('doc_type') == 'protocol':
            types.append('implementation')
            
        if set(attrs1.get('methods', [])) & set(attrs2.get('methods', [])):
            types.append('methodological')
            
        return types or ['related']
        
    def _save_to_cache(self):
        """Save graph to cache"""
        # Convert graph to serializable format
        graph_data = {
            'nodes': list(self.graph.nodes(data=True)),
            'edges': list(self.graph.edges(data=True))
        }
        cache.set('knowledge_graph:data', graph_data, 3600)
        
    def _load_from_cache(self):
        """Load graph from cache"""
        graph_data = cache.get('knowledge_graph:data')
        if graph_data:
            self.graph.clear()
            self.graph.add_nodes_from(graph_data['nodes'])
            self.graph.add_edges_from(graph_data['edges'])


class KnowledgeGraphConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time graph updates"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.graph_service = KnowledgeGraphService()
        self.room_group_name = 'knowledge_graph_updates'
        
    async def connect(self):
        """Handle WebSocket connection"""
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # Send initial graph data
        graph_data = await sync_to_async(self.graph_service.export_for_visualization)()
        await self.send_json({
            'type': 'graph_init',
            'data': graph_data
        })
        
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
    async def receive_json(self, content):
        """Handle incoming WebSocket messages"""
        message_type = content.get('type')
        
        if message_type == 'get_subgraph':
            node_id = content.get('node_id')
            depth = content.get('depth', 2)
            
            subgraph = await sync_to_async(self.graph_service.get_subgraph)(node_id, depth)
            subgraph_data = await sync_to_async(self._subgraph_to_dict)(subgraph)
            
            await self.send_json({
                'type': 'subgraph_data',
                'data': subgraph_data
            })
            
        elif message_type == 'search_nodes':
            query = content.get('query', '')
            results = await sync_to_async(self.graph_service.search_nodes)(query)
            
            await self.send_json({
                'type': 'search_results',
                'data': results
            })
            
        elif message_type == 'get_suggestions':
            node_id = content.get('node_id')
            suggestions = await sync_to_async(self.graph_service.suggest_connections)(node_id)
            
            await self.send_json({
                'type': 'connection_suggestions',
                'data': suggestions
            })
            
        elif message_type == 'get_trends':
            trends = await sync_to_async(self.graph_service.detect_research_trends)()
            
            await self.send_json({
                'type': 'trend_data',
                'data': trends
            })
            
    async def graph_update(self, event):
        """Handle graph update events"""
        await self.send_json({
            'type': 'graph_update',
            'data': event['data']
        })
        
    async def new_connection(self, event):
        """Handle new connection events"""
        await self.send_json({
            'type': 'new_connection',
            'data': event['data']
        })
        
    async def new_node(self, event):
        """Handle new node events"""
        await self.send_json({
            'type': 'new_node',
            'data': event['data']
        })
        
    def _subgraph_to_dict(self, subgraph):
        """Convert subgraph to dictionary format"""
        nodes = []
        edges = []
        
        for node_id, attrs in subgraph.nodes(data=True):
            nodes.append({
                'id': node_id,
                'label': attrs.get('title', ''),
                'type': attrs.get('doc_type', ''),
                'degree': subgraph.degree(node_id)
            })
            
        for u, v, data in subgraph.edges(data=True):
            edges.append({
                'source': u,
                'target': v,
                'type': data.get('connections', [{}])[0].get('type', 'related') if data.get('connections') else 'related'
            })
            
        return {'nodes': nodes, 'edges': edges}


# Singleton instance
_graph_service_instance = None

def get_graph_service() -> KnowledgeGraphService:
    """Get singleton instance of graph service"""
    global _graph_service_instance
    if _graph_service_instance is None:
        _graph_service_instance = KnowledgeGraphService()
    return _graph_service_instance