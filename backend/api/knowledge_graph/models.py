from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.utils import timezone
from api.models import Document


class KnowledgeNode(models.Model):
    """Represents a node in the knowledge graph"""
    NODE_TYPES = [
        ('document', 'Document'),
        ('concept', 'Concept'),
        ('author', 'Author'),
        ('method', 'Method'),
        ('finding', 'Finding'),
        ('protocol', 'Protocol'),
    ]
    
    id = models.AutoField(primary_key=True)
    node_id = models.CharField(max_length=255, unique=True, db_index=True)
    label = models.CharField(max_length=500)
    node_type = models.CharField(max_length=50, choices=NODE_TYPES, db_index=True)
    document = models.ForeignKey(Document, null=True, blank=True, on_delete=models.CASCADE)
    properties = models.JSONField(default=dict)
    embedding = ArrayField(models.FloatField(), size=1536, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['node_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.node_type}: {self.label}"


class KnowledgeEdge(models.Model):
    """Represents connections between nodes"""
    EDGE_TYPES = [
        ('cites', 'Cites'),
        ('uses', 'Uses Method'),
        ('contradicts', 'Contradicts'),
        ('supports', 'Supports'),
        ('extends', 'Extends'),
        ('authored_by', 'Authored By'),
        ('related_to', 'Related To'),
        ('derived_from', 'Derived From'),
    ]
    
    source = models.ForeignKey(KnowledgeNode, on_delete=models.CASCADE, related_name='outgoing_edges')
    target = models.ForeignKey(KnowledgeNode, on_delete=models.CASCADE, related_name='incoming_edges')
    edge_type = models.CharField(max_length=50, choices=EDGE_TYPES, db_index=True)
    weight = models.FloatField(default=1.0)
    properties = models.JSONField(default=dict)
    discovered_at = models.DateTimeField(default=timezone.now)
    confidence = models.FloatField(default=1.0)
    
    class Meta:
        unique_together = [('source', 'target', 'edge_type')]
        indexes = [
            models.Index(fields=['edge_type', 'weight']),
            models.Index(fields=['discovered_at']),
        ]
    
    def __str__(self):
        return f"{self.source.label} --{self.edge_type}--> {self.target.label}"


class GraphCluster(models.Model):
    """Represents topic clusters in the knowledge graph"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    nodes = models.ManyToManyField(KnowledgeNode, related_name='clusters')
    centroid_embedding = ArrayField(models.FloatField(), size=1536, null=True)
    properties = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class GraphUpdate(models.Model):
    """Tracks updates to the knowledge graph for real-time notifications"""
    UPDATE_TYPES = [
        ('node_added', 'Node Added'),
        ('edge_added', 'Edge Added'),
        ('cluster_formed', 'Cluster Formed'),
        ('insight_generated', 'Insight Generated'),
    ]
    
    update_type = models.CharField(max_length=50, choices=UPDATE_TYPES)
    node = models.ForeignKey(KnowledgeNode, null=True, blank=True, on_delete=models.CASCADE)
    edge = models.ForeignKey(KnowledgeEdge, null=True, blank=True, on_delete=models.CASCADE)
    cluster = models.ForeignKey(GraphCluster, null=True, blank=True, on_delete=models.CASCADE)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.update_type} at {self.created_at}"