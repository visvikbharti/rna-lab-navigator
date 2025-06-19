from django.db.models.signals import post_save
from django.dispatch import receiver
from api.models import Document
from .tasks import process_document_for_graph


@receiver(post_save, sender=Document)
def document_saved(sender, instance, created, **kwargs):
    """Handle document save signal to update knowledge graph"""
    if created:
        # Process document asynchronously
        process_document_for_graph.delay(instance.id)