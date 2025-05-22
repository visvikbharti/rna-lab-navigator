"""
Simplified views for the feedback app for demo purposes.
"""

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def feedback_summary(request):
    """
    Simplified feedback summary endpoint for demo purposes.
    """
    # Return mock feedback summary
    return JsonResponse({
        'summary': {
            'total_feedbacks': 387,
            'average_rating': 4.2,
            'rating_distribution': {
                '1': 12,
                '2': 25,
                '3': 78,
                '4': 142,
                '5': 130
            }
        },
        'by_doc_type': {
            'protocol': {
                'average_rating': 4.3,
                'count': 125
            },
            'paper': {
                'average_rating': 4.1,
                'count': 210
            },
            'thesis': {
                'average_rating': 4.5,
                'count': 52
            }
        },
        'last_30_days': {
            'trend': 'stable',
            'change': '+0.1'
        }
    })