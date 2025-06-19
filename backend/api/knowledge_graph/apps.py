from django.apps import AppConfig


class KnowledgeGraphConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.knowledge_graph'
    
    def ready(self):
        import api.knowledge_graph.signals