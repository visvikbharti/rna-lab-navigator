"""
Hypothesis Mode API Views
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import logging
import asyncio
import uuid

from .services import HypothesisService
# Temporarily commenting out for testing
# from .enhanced_services import get_enhanced_hypothesis_service, HypothesisContext
# from ..protocols.enhanced_services import (
#     get_enhanced_protocol_service, 
#     ProtocolRequirements, 
#     LabCapabilities, 
#     ProtocolOptimization
# )
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

@api_view(['POST'])
@permission_classes([AllowAny])
def explore_hypothesis_enhanced(request):
    """
    Explore a hypothesis with enhanced reasoning and knowledge synthesis
    
    POST /api/hypothesis/explore-enhanced/
    {
        "question": "What if we could use CRISPR to...",
        "session_id": "optional-session-id",
        "user_context": {
            "expertise_level": "graduate",
            "research_area": "RNA biology"
        },
        "hypothesis_context": {
            "research_area": "RNA splicing",
            "lab_expertise": ["CRISPR", "RNA-seq"],
            "available_equipment": ["qPCR", "Flow cytometer"],
            "constraints": {"budget": "limited", "timeline": "6 months"}
        }
    }
    """
    question = request.data.get('question')
    if not question:
        return Response(
            {'error': 'Question is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    session_id = request.data.get('session_id', str(uuid.uuid4()))
    user_context = request.data.get('user_context', {})
    hypothesis_context_data = request.data.get('hypothesis_context', {})
    
    # Create HypothesisContext if provided
    hypothesis_context = None
    if hypothesis_context_data:
        hypothesis_context = HypothesisContext(
            research_area=hypothesis_context_data.get('research_area', ''),
            lab_expertise=hypothesis_context_data.get('lab_expertise', []),
            available_equipment=hypothesis_context_data.get('available_equipment', []),
            previous_experiments=hypothesis_context_data.get('previous_experiments', []),
            constraints=hypothesis_context_data.get('constraints', {})
        )
    
    try:
        enhanced_service = get_enhanced_hypothesis_service()
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            enhanced_service.explore_hypothesis_with_reasoning(
                question=question,
                session_id=session_id,
                user_context=user_context,
                hypothesis_context=hypothesis_context
            )
        )
        
        loop.close()
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in enhanced hypothesis exploration: {str(e)}")
        
        # Fallback to basic service
        basic_service = HypothesisService()
        result = basic_service.explore_hypothesis(
            question=question,
            user_id=request.user.id if request.user.is_authenticated else None
        )
        
        if result['success']:
            result['fallback_used'] = True
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Failed to process hypothesis'},
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
                'experimental_design': True,
                'enhanced_reasoning': True,
                'knowledge_synthesis': True
            }
        },
        'protocol_builder': {
            'enabled': True,
            'features': {
                'custom_generation': True,
                'template_based': True,
                'version_control': False,  # Coming soon
                'collaboration': False,     # Coming soon
                'lab_context_aware': True
            }
        },
        'enhanced_features': {
            'chain_of_thought': True,
            'multi_stage_analysis': True,
            'knowledge_graph_integration': True,
            'experimental_design_ai': True,
            'gap_analysis': True
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def generate_protocol_enhanced(request):
    """
    Generate a protocol with enhanced AI reasoning and lab awareness
    
    POST /api/hypothesis/generate-protocol-enhanced/
    {
        "requirements": {
            "experiment_type": "RNA extraction",
            "sample_type": "cell culture",
            "sample_size": 12,
            "objectives": ["Extract high-quality RNA", "Minimize degradation"],
            "constraints": {"time": "4 hours", "budget": "limited"},
            "safety_level": "BSL-2",
            "timeline": "same day",
            "budget": "standard"
        },
        "lab_capabilities": {
            "equipment": ["Centrifuge", "Vortex", "Spectrophotometer"],
            "reagents": ["TRIzol", "Chloroform", "Isopropanol"],
            "expertise": ["RNA handling", "Cell culture"],
            "typical_protocols": ["Basic RNA extraction"]
        },
        "optimization": {
            "optimize_for": "quality",
            "critical_steps": ["RNA extraction", "DNase treatment"],
            "flexibility_areas": ["Incubation times"]
        },
        "session_id": "optional-session-id",
        "base_protocol_id": null
    }
    """
    requirements_data = request.data.get('requirements')
    if not requirements_data:
        return Response(
            {'error': 'Requirements are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create data objects
    try:
        requirements = ProtocolRequirements(
            experiment_type=requirements_data.get('experiment_type', ''),
            sample_type=requirements_data.get('sample_type', ''),
            sample_size=requirements_data.get('sample_size', 1),
            objectives=requirements_data.get('objectives', []),
            constraints=requirements_data.get('constraints', {}),
            safety_level=requirements_data.get('safety_level', 'BSL-1'),
            timeline=requirements_data.get('timeline', 'flexible'),
            budget=requirements_data.get('budget', 'standard')
        )
        
        lab_capabilities = None
        if request.data.get('lab_capabilities'):
            lab_data = request.data['lab_capabilities']
            lab_capabilities = LabCapabilities(
                equipment=lab_data.get('equipment', []),
                reagents=lab_data.get('reagents', []),
                expertise=lab_data.get('expertise', []),
                typical_protocols=lab_data.get('typical_protocols', [])
            )
        
        optimization = None
        if request.data.get('optimization'):
            opt_data = request.data['optimization']
            optimization = ProtocolOptimization(
                optimize_for=opt_data.get('optimize_for', 'balanced'),
                critical_steps=opt_data.get('critical_steps', []),
                flexibility_areas=opt_data.get('flexibility_areas', [])
            )
        
        session_id = request.data.get('session_id')
        base_protocol_id = request.data.get('base_protocol_id')
        
        # Get enhanced protocol service
        protocol_service = get_enhanced_protocol_service()
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            protocol_service.generate_intelligent_protocol(
                requirements=requirements,
                lab_capabilities=lab_capabilities,
                optimization=optimization,
                session_id=session_id,
                base_protocol_id=base_protocol_id
            )
        )
        
        loop.close()
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in enhanced protocol generation: {str(e)}")
        
        # Fallback to basic service
        basic_service = HypothesisService()
        basic_requirements = requirements_data.get('experiment_type', '') + ' ' + ' '.join(requirements_data.get('objectives', []))
        
        result = basic_service.generate_protocol(
            requirements=basic_requirements,
            base_protocol_id=request.data.get('base_protocol_id'),
            user_id=request.user.id if request.user.is_authenticated else None
        )
        
        if result['success']:
            result['fallback_used'] = True
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Failed to generate protocol'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )