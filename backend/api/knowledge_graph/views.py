from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count, Q, Avg
from django.db import models
import logging
from .models import KnowledgeNode, KnowledgeEdge, GraphCluster, GraphUpdate
from .services import KnowledgeGraphService

logger = logging.getLogger(__name__)


@api_view(['GET'])
def graph_overview(request):
    """Get graph overview statistics"""
    stats = {
        'nodes': {
            'total': KnowledgeNode.objects.count(),
            'by_type': dict(KnowledgeNode.objects.values_list('node_type').annotate(count=Count('id')))
        },
        'edges': {
            'total': KnowledgeEdge.objects.count(),
            'by_type': dict(KnowledgeEdge.objects.values_list('edge_type').annotate(count=Count('id')))
        },
        'clusters': {
            'total': GraphCluster.objects.count(),
            'avg_size': GraphCluster.objects.annotate(
                size=Count('nodes')
            ).aggregate(avg=models.Avg('size'))['avg'] or 0
        },
        'recent_updates': list(
            GraphUpdate.objects.values(
                'update_type', 'created_at'
            ).order_by('-created_at')[:10]
        )
    }
    
    return Response(stats)


@api_view(['POST'])
def trigger_discovery(request):
    """Trigger connection discovery for all nodes"""
    service = KnowledgeGraphService()
    
    # Get all nodes with embeddings
    nodes = KnowledgeNode.objects.exclude(embedding__isnull=True)
    
    discovered = 0
    for node in nodes:
        try:
            service.discover_connections(node)
            discovered += 1
        except Exception as e:
            logger.error(f"Error discovering connections for {node.node_id}: {e}")
    
    return Response({
        'status': 'success',
        'nodes_processed': discovered,
        'message': f'Discovered connections for {discovered} nodes'
    })


@api_view(['POST'])
def trigger_clustering(request):
    """Trigger graph clustering"""
    service = KnowledgeGraphService()
    
    try:
        service.cluster_nodes(
            min_samples=request.data.get('min_samples', 3),
            eps=request.data.get('eps', 0.3)
        )
        
        return Response({
            'status': 'success',
            'clusters': GraphCluster.objects.count()
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_temporal_evolution(request):
    """Get temporal evolution data for animation"""
    # Get time range
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    # Build query
    query = Q()
    if from_date:
        query &= Q(created_at__gte=from_date)
    if to_date:
        query &= Q(created_at__lte=to_date)
    
    # Get nodes and edges by time
    nodes_timeline = list(
        KnowledgeNode.objects.filter(query)
        .values('created_at__date', 'node_type')
        .annotate(count=Count('id'))
        .order_by('created_at__date')
    )
    
    edges_timeline = list(
        KnowledgeEdge.objects.filter(query)
        .values('discovered_at__date', 'edge_type')
        .annotate(count=Count('id'))
        .order_by('discovered_at__date')
    )
    
    return Response({
        'nodes_timeline': nodes_timeline,
        'edges_timeline': edges_timeline
    })


@api_view(['POST'])
def search_graph(request):
    """Search nodes in the graph"""
    query = request.data.get('query', '')
    node_types = request.data.get('node_types', [])
    
    if not query:
        return Response({'results': []})
    
    # Search nodes
    nodes_query = KnowledgeNode.objects.filter(
        Q(label__icontains=query) |
        Q(properties__icontains=query)
    )
    
    if node_types:
        nodes_query = nodes_query.filter(node_type__in=node_types)
    
    results = []
    for node in nodes_query[:20]:  # Limit to 20 results
        results.append({
            'id': node.node_id,
            'label': node.label,
            'type': node.node_type,
            'properties': node.properties
        })
    
    return Response({'results': results})