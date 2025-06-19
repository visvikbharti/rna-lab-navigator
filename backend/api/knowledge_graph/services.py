import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from django.db import transaction
from django.db.models import Count, Avg, Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

from api.models import Document
from api.llm.openai_embeddings import get_embeddings
from .models import KnowledgeNode, KnowledgeEdge, GraphCluster, GraphUpdate

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Service for managing the knowledge graph"""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    @transaction.atomic
    def create_document_node(self, document: Document) -> KnowledgeNode:
        """Create a node for a document"""
        node_id = f"doc_{document.id}"
        
        node, created = KnowledgeNode.objects.update_or_create(
            node_id=node_id,
            defaults={
                'label': document.title,
                'node_type': 'document',
                'document': document,
                'properties': {
                    'authors': document.authors,
                    'year': document.year,
                    'doc_type': document.doc_type,
                    'abstract': document.abstract[:500] if document.abstract else '',
                }
            }
        )
        
        if created:
            # Generate embedding for the node
            text = f"{document.title} {document.abstract[:1000] if document.abstract else ''}"
            try:
                embedding = get_embeddings(text)
                node.embedding = embedding
                node.save()
            except Exception as e:
                logger.error(f"Error generating embedding for node {node_id}: {e}")
            
            # Create update notification
            self._create_update('node_added', node=node)
            
            # Extract and create related nodes
            self._extract_concepts_from_document(document, node)
        
        return node
    
    def _extract_concepts_from_document(self, document: Document, doc_node: KnowledgeNode):
        """Extract concepts, methods, and findings from document"""
        # This is a simplified version - in production, use NLP/LLM for extraction
        
        # Extract authors
        if document.authors:
            for author in document.authors.split(','):
                author = author.strip()
                if author:
                    author_node = self._create_concept_node(
                        node_id=f"author_{author.lower().replace(' ', '_')}",
                        label=author,
                        node_type='author'
                    )
                    self._create_edge(doc_node, author_node, 'authored_by')
        
        # Extract methods (simplified - look for common method keywords)
        if document.content:
            methods = self._extract_methods(document.content)
            for method in methods:
                method_node = self._create_concept_node(
                    node_id=f"method_{method.lower().replace(' ', '_')}",
                    label=method,
                    node_type='method'
                )
                self._create_edge(doc_node, method_node, 'uses')
    
    def _extract_methods(self, content: str) -> List[str]:
        """Extract method names from content"""
        # Simplified extraction - in production use NER or pattern matching
        method_keywords = [
            'PCR', 'Western blot', 'CRISPR', 'RNA-seq', 'ChIP-seq',
            'Flow cytometry', 'Microscopy', 'Mass spectrometry',
            'Immunofluorescence', 'qPCR', 'Northern blot'
        ]
        
        found_methods = []
        content_lower = content.lower()
        for method in method_keywords:
            if method.lower() in content_lower:
                found_methods.append(method)
        
        return found_methods
    
    def _create_concept_node(self, node_id: str, label: str, node_type: str) -> KnowledgeNode:
        """Create or get a concept node"""
        node, created = KnowledgeNode.objects.get_or_create(
            node_id=node_id,
            defaults={
                'label': label,
                'node_type': node_type,
                'properties': {}
            }
        )
        
        if created:
            # Generate embedding
            try:
                embedding = get_embeddings(label)
                node.embedding = embedding
                node.save()
            except Exception as e:
                logger.error(f"Error generating embedding for concept {node_id}: {e}")
            
            self._create_update('node_added', node=node)
        
        return node
    
    def _create_edge(self, source: KnowledgeNode, target: KnowledgeNode, 
                     edge_type: str, weight: float = 1.0, properties: Dict = None):
        """Create an edge between nodes"""
        edge, created = KnowledgeEdge.objects.get_or_create(
            source=source,
            target=target,
            edge_type=edge_type,
            defaults={
                'weight': weight,
                'properties': properties or {}
            }
        )
        
        if created:
            self._create_update('edge_added', edge=edge)
        
        return edge
    
    def discover_connections(self, node: KnowledgeNode, similarity_threshold: float = 0.7):
        """Discover connections based on semantic similarity"""
        if not node.embedding:
            return
        
        # Find similar nodes
        similar_nodes = self._find_similar_nodes(node, similarity_threshold)
        
        for similar_node, similarity in similar_nodes:
            # Create edge if it doesn't exist
            if not KnowledgeEdge.objects.filter(
                Q(source=node, target=similar_node) | Q(source=similar_node, target=node),
                edge_type='related_to'
            ).exists():
                self._create_edge(
                    node, similar_node, 'related_to',
                    weight=similarity,
                    properties={'similarity_score': similarity}
                )
    
    def _find_similar_nodes(self, node: KnowledgeNode, threshold: float) -> List[Tuple[KnowledgeNode, float]]:
        """Find nodes similar to the given node"""
        if not node.embedding:
            return []
        
        # Get all nodes with embeddings
        other_nodes = KnowledgeNode.objects.exclude(
            id=node.id
        ).exclude(embedding__isnull=True)
        
        similar_nodes = []
        node_embedding = np.array(node.embedding).reshape(1, -1)
        
        for other in other_nodes:
            other_embedding = np.array(other.embedding).reshape(1, -1)
            similarity = cosine_similarity(node_embedding, other_embedding)[0][0]
            
            if similarity >= threshold:
                similar_nodes.append((other, float(similarity)))
        
        # Sort by similarity
        similar_nodes.sort(key=lambda x: x[1], reverse=True)
        return similar_nodes[:10]  # Return top 10
    
    def cluster_nodes(self, min_samples: int = 3, eps: float = 0.3):
        """Cluster nodes based on their embeddings"""
        # Get all nodes with embeddings
        nodes = list(KnowledgeNode.objects.exclude(embedding__isnull=True))
        
        if len(nodes) < min_samples:
            return
        
        # Extract embeddings
        embeddings = np.array([node.embedding for node in nodes])
        
        # Perform clustering
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
        labels = clustering.fit_predict(embeddings)
        
        # Create clusters
        unique_labels = set(labels)
        for label in unique_labels:
            if label == -1:  # Noise
                continue
            
            cluster_nodes = [nodes[i] for i, l in enumerate(labels) if l == label]
            
            # Calculate cluster centroid
            cluster_embeddings = embeddings[labels == label]
            centroid = np.mean(cluster_embeddings, axis=0)
            
            # Create cluster
            cluster = GraphCluster.objects.create(
                name=f"Cluster {label}",
                centroid_embedding=centroid.tolist(),
                properties={
                    'size': len(cluster_nodes),
                    'coherence': self._calculate_cluster_coherence(cluster_embeddings)
                }
            )
            
            cluster.nodes.set(cluster_nodes)
            
            self._create_update('cluster_formed', cluster=cluster)
    
    def _calculate_cluster_coherence(self, embeddings: np.ndarray) -> float:
        """Calculate cluster coherence (average pairwise similarity)"""
        if len(embeddings) < 2:
            return 1.0
        
        similarities = cosine_similarity(embeddings)
        # Get upper triangle (excluding diagonal)
        upper_triangle = np.triu_indices_from(similarities, k=1)
        return float(np.mean(similarities[upper_triangle]))
    
    def get_graph_data(self, node_types: List[str] = None, 
                      edge_types: List[str] = None,
                      cluster_id: int = None) -> Dict[str, Any]:
        """Get graph data for visualization"""
        # Filter nodes
        node_query = KnowledgeNode.objects.all()
        if node_types:
            node_query = node_query.filter(node_type__in=node_types)
        if cluster_id:
            node_query = node_query.filter(clusters__id=cluster_id)
        
        nodes = []
        node_map = {}
        
        for i, node in enumerate(node_query):
            node_data = {
                'id': node.node_id,
                'label': node.label,
                'type': node.node_type,
                'properties': node.properties,
                'index': i
            }
            nodes.append(node_data)
            node_map[node.id] = i
        
        # Filter edges
        edge_query = KnowledgeEdge.objects.filter(
            source__in=node_query,
            target__in=node_query
        )
        if edge_types:
            edge_query = edge_query.filter(edge_type__in=edge_types)
        
        edges = []
        for edge in edge_query:
            if edge.source_id in node_map and edge.target_id in node_map:
                edges.append({
                    'source': node_map[edge.source_id],
                    'target': node_map[edge.target_id],
                    'type': edge.edge_type,
                    'weight': edge.weight,
                    'properties': edge.properties
                })
        
        # Get clusters
        clusters = []
        for cluster in GraphCluster.objects.all():
            cluster_nodes = [
                node_map[n.id] for n in cluster.nodes.all() 
                if n.id in node_map
            ]
            if cluster_nodes:
                clusters.append({
                    'id': cluster.id,
                    'name': cluster.name,
                    'nodes': cluster_nodes,
                    'properties': cluster.properties
                })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'clusters': clusters,
            'stats': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'total_clusters': len(clusters)
            }
        }
    
    def _create_update(self, update_type: str, node: KnowledgeNode = None,
                      edge: KnowledgeEdge = None, cluster: GraphCluster = None):
        """Create an update and send WebSocket notification"""
        update = GraphUpdate.objects.create(
            update_type=update_type,
            node=node,
            edge=edge,
            cluster=cluster,
            metadata=self._get_update_metadata(update_type, node, edge, cluster)
        )
        
        # Send WebSocket notification
        self._send_update_notification(update)
    
    def _get_update_metadata(self, update_type: str, node: KnowledgeNode = None,
                            edge: KnowledgeEdge = None, cluster: GraphCluster = None) -> Dict:
        """Get metadata for update"""
        metadata = {'update_type': update_type}
        
        if node:
            metadata['node'] = {
                'id': node.node_id,
                'label': node.label,
                'type': node.node_type
            }
        
        if edge:
            metadata['edge'] = {
                'source': edge.source.label,
                'target': edge.target.label,
                'type': edge.edge_type
            }
        
        if cluster:
            metadata['cluster'] = {
                'id': cluster.id,
                'name': cluster.name,
                'size': cluster.nodes.count()
            }
        
        return metadata
    
    def _send_update_notification(self, update: GraphUpdate):
        """Send update notification via WebSocket"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                'knowledge_graph',
                {
                    'type': 'graph_update',
                    'update': {
                        'id': update.id,
                        'type': update.update_type,
                        'metadata': update.metadata,
                        'created_at': update.created_at.isoformat()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {e}")
    
    def get_node_details(self, node_id: str) -> Dict[str, Any]:
        """Get detailed information about a node"""
        try:
            node = KnowledgeNode.objects.get(node_id=node_id)
            
            # Get connected nodes
            outgoing = KnowledgeEdge.objects.filter(source=node).select_related('target')
            incoming = KnowledgeEdge.objects.filter(target=node).select_related('source')
            
            return {
                'node': {
                    'id': node.node_id,
                    'label': node.label,
                    'type': node.node_type,
                    'properties': node.properties,
                    'created_at': node.created_at.isoformat(),
                    'document': {
                        'id': node.document.id,
                        'title': node.document.title
                    } if node.document else None
                },
                'connections': {
                    'outgoing': [
                        {
                            'target': edge.target.label,
                            'target_id': edge.target.node_id,
                            'type': edge.edge_type,
                            'weight': edge.weight
                        } for edge in outgoing
                    ],
                    'incoming': [
                        {
                            'source': edge.source.label,
                            'source_id': edge.source.node_id,
                            'type': edge.edge_type,
                            'weight': edge.weight
                        } for edge in incoming
                    ]
                },
                'clusters': [
                    {
                        'id': cluster.id,
                        'name': cluster.name
                    } for cluster in node.clusters.all()
                ]
            }
        except KnowledgeNode.DoesNotExist:
            return None