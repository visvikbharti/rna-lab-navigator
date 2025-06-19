from celery import shared_task
import logging
from .services import KnowledgeGraphService
from api.models import Document

logger = logging.getLogger(__name__)


@shared_task
def process_document_for_graph(document_id: int):
    """Process a document and add it to the knowledge graph"""
    try:
        document = Document.objects.get(id=document_id)
        service = KnowledgeGraphService()
        
        # Create document node
        node = service.create_document_node(document)
        
        # Discover connections
        service.discover_connections(node)
        
        logger.info(f"Processed document {document_id} for knowledge graph")
        return True
    
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        return False


@shared_task
def periodic_graph_clustering():
    """Periodically cluster the knowledge graph"""
    try:
        service = KnowledgeGraphService()
        service.cluster_nodes()
        logger.info("Completed periodic graph clustering")
        return True
    except Exception as e:
        logger.error(f"Error in periodic clustering: {e}")
        return False


@shared_task
def discover_all_connections():
    """Discover connections for all nodes"""
    from .models import KnowledgeNode
    
    service = KnowledgeGraphService()
    nodes = KnowledgeNode.objects.exclude(embedding__isnull=True)
    
    discovered = 0
    for node in nodes:
        try:
            service.discover_connections(node)
            discovered += 1
        except Exception as e:
            logger.error(f"Error discovering connections for {node.node_id}: {e}")
    
    logger.info(f"Discovered connections for {discovered} nodes")
    return discovered