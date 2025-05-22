"""
Simplified views for the quality app for demo purposes.
"""

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def quality_metrics(request):
    """
    Simplified quality metrics endpoint for demo purposes.
    """
    # Return mock quality metrics
    return JsonResponse({
        'metrics': {
            'overall_quality_score': 0.87,
            'retrieval_precision': 0.92,
            'answer_relevance': 0.85,
            'response_time': 4.3  # seconds
        },
        'by_doc_type': {
            'protocol': {
                'quality_score': 0.89,
                'count': 125
            },
            'paper': {
                'quality_score': 0.85,
                'count': 210
            },
            'thesis': {
                'quality_score': 0.91,
                'count': 42
            }
        },
        'last_30_days': {
            'trend': 'improving',
            'change': '+0.03'
        }
    })