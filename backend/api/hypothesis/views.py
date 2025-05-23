"""
Hypothesis Mode API Views
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import logging

from .services import HypothesisService
from .serializers import (
    HypothesisExplorationSerializer,
    ProtocolGenerationSerializer
)

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])  # Will change to IsAuthenticated when auth is implemented
def explore_hypothesis(request):
    """
    Explore a research hypothesis using advanced AI reasoning
    
    POST /api/hypothesis/explore/
    {
        "question": "What if we could use CRISPR to...",
        "use_advanced_model": false
    }
    """
    serializer = HypothesisExplorationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid input', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    hypothesis_service = HypothesisService()
    
    # Get user ID if authenticated
    user_id = request.user.id if request.user.is_authenticated else None
    
    result = hypothesis_service.explore_hypothesis(
        question=serializer.validated_data['question'],
        user_id=user_id,
        use_advanced_model=serializer.validated_data.get('use_advanced_model', False)
    )
    
    if result['success']:
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(
            {'error': result.get('error', 'Unknown error occurred')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])  # Will change to IsAuthenticated when auth is implemented
def generate_protocol(request):
    """
    Generate a custom lab protocol based on requirements
    
    POST /api/hypothesis/generate-protocol/
    {
        "requirements": "I need a protocol for RNA extraction from...",
        "base_protocol_id": null
    }
    """
    serializer = ProtocolGenerationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid input', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    hypothesis_service = HypothesisService()
    
    # Get user ID if authenticated
    user_id = request.user.id if request.user.is_authenticated else None
    
    result = hypothesis_service.generate_protocol(
        requirements=serializer.validated_data['requirements'],
        base_protocol_id=serializer.validated_data.get('base_protocol_id'),
        user_id=user_id
    )
    
    if result['success']:
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(
            {'error': result.get('error', 'Unknown error occurred')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def hypothesis_status(request):
    """
    Get the status of hypothesis mode features
    
    GET /api/hypothesis/status/
    """
    return Response({
        'hypothesis_mode': {
            'enabled': True,
            'models_available': ['gpt-4o'],
            'advanced_model': 'coming_soon',
            'features': {
                'hypothesis_exploration': True,
                'protocol_generation': True,
                'confidence_scoring': True,
                'experimental_design': True
            }
        },
        'protocol_builder': {
            'enabled': True,
            'features': {
                'custom_generation': True,
                'template_based': True,
                'version_control': False,  # Coming soon
                'collaboration': False     # Coming soon
            }
        }
    }, status=status.HTTP_200_OK)