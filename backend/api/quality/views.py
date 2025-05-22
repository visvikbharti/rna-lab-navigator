"""
API views for the quality improvement system.
"""

import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    QualityAnalysis,
    QualityImprovement,
    ImprovedPrompt,
    RetrievalConfiguration
)
from .serializers import (
    QualityAnalysisSerializer,
    QualityAnalysisDetailSerializer,
    QualityImprovementSerializer,
    QualityImprovementBasicSerializer,
    ImprovedPromptSerializer,
    RetrievalConfigurationSerializer,
    QualityMetricsSerializer,
    ApproveImprovementSerializer,
    ImplementImprovementSerializer,
    CreateAnalysisSerializer
)
from .services import QualityImprovementService
from .tasks import (
    run_quality_analysis_task,
    generate_and_run_quality_analysis_task,
    implement_approved_improvements_task,
    auto_approve_priority_improvements_task,
    run_complete_quality_pipeline_task
)

logger = logging.getLogger(__name__)


class QualityAnalysisViewSet(viewsets.ModelViewSet):
    """
    ViewSet for QualityAnalysis.
    
    Provides CRUD operations and additional actions for 
    quality analysis management.
    """
    
    queryset = QualityAnalysis.objects.all().order_by('-created_at')
    serializer_class = QualityAnalysisSerializer
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'retrieve':
            return QualityAnalysisDetailSerializer
        return QualityAnalysisSerializer
    
    @action(detail=False, methods=['post'])
    def create_and_run(self, request):
        """
        Create and run a quality analysis.
        """
        serializer = CreateAnalysisSerializer(data=request.data)
        
        if serializer.is_valid():
            service = QualityImprovementService()
            
            # Generate the analysis
            analysis = service.generate_quality_analysis(
                name=serializer.validated_data['name'],
                analysis_type=serializer.validated_data['analysis_type'],
                days_lookback=serializer.validated_data['days_lookback'],
                filters=serializer.validated_data.get('filters')
            )
            
            # Start the task to run the analysis
            task = run_quality_analysis_task.delay(str(analysis.analysis_id))
            
            return Response({
                'analysis_id': str(analysis.analysis_id),
                'name': analysis.name,
                'status': analysis.status,
                'task_id': task.id,
                'message': 'Analysis created and running'
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """
        Run an existing quality analysis.
        """
        analysis = self.get_object()
        
        if analysis.status != 'pending':
            return Response({
                'error': f"Analysis is in '{analysis.status}' status. Only 'pending' analyses can be run."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Start the task to run the analysis
        task = run_quality_analysis_task.delay(str(analysis.analysis_id))
        
        return Response({
            'analysis_id': str(analysis.analysis_id),
            'name': analysis.name,
            'task_id': task.id,
            'message': 'Analysis running'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['post'])
    def schedule(self, request):
        """
        Schedule a new quality analysis to run asynchronously.
        """
        serializer = CreateAnalysisSerializer(data=request.data)
        
        if serializer.is_valid():
            # Start the task to generate and run the analysis
            task = generate_and_run_quality_analysis_task.delay(
                name=serializer.validated_data['name'],
                analysis_type=serializer.validated_data['analysis_type'],
                days_lookback=serializer.validated_data['days_lookback']
            )
            
            return Response({
                'task_id': task.id,
                'name': serializer.validated_data['name'],
                'message': 'Analysis scheduled'
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QualityImprovementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for QualityImprovement.
    
    Provides CRUD operations and additional actions for 
    quality improvement management.
    """
    
    queryset = QualityImprovement.objects.all().order_by('-created_at')
    serializer_class = QualityImprovementSerializer
    
    def get_queryset(self):
        """Return filtered queryset."""
        queryset = QualityImprovement.objects.all().order_by('-created_at')
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by type
        type_param = self.request.query_params.get('type')
        if type_param:
            queryset = queryset.filter(improvement_type=type_param)
        
        # Filter by priority
        priority_param = self.request.query_params.get('priority')
        if priority_param:
            queryset = queryset.filter(priority=priority_param)
        
        # Filter by source analysis
        analysis_param = self.request.query_params.get('analysis')
        if analysis_param:
            queryset = queryset.filter(source_analysis_id=analysis_param)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve an improvement.
        """
        improvement = self.get_object()
        
        if improvement.status != 'proposed':
            return Response({
                'error': f"Improvement is in '{improvement.status}' status. Only 'proposed' improvements can be approved."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = QualityImprovementService()
        improvement = service.approve_improvement(str(improvement.improvement_id), request.user)
        
        return Response({
            'improvement_id': str(improvement.improvement_id),
            'title': improvement.title,
            'status': improvement.status,
            'message': 'Improvement approved'
        })
    
    @action(detail=True, methods=['post'])
    def implement(self, request, pk=None):
        """
        Implement an improvement.
        """
        improvement = self.get_object()
        
        if improvement.status != 'approved':
            return Response({
                'error': f"Improvement is in '{improvement.status}' status. Only 'approved' improvements can be implemented."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = QualityImprovementService()
        result = service.implement_improvement(str(improvement.improvement_id))
        
        return Response({
            'improvement_id': str(improvement.improvement_id),
            'title': improvement.title,
            'status': 'implemented',
            'message': 'Improvement implemented',
            'result': result.get('results', {})
        })
    
    @action(detail=False, methods=['post'])
    def implement_all_approved(self, request):
        """
        Implement all approved improvements.
        """
        task = implement_approved_improvements_task.delay()
        
        return Response({
            'task_id': task.id,
            'message': 'Task started to implement all approved improvements'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['post'])
    def auto_approve_priority(self, request):
        """
        Auto approve high-priority improvements.
        """
        task = auto_approve_priority_improvements_task.delay()
        
        return Response({
            'task_id': task.id,
            'message': 'Task started to auto-approve priority improvements'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """
        Get current improvement recommendations.
        """
        improvement_type = request.query_params.get('type')
        status_filter = request.query_params.get('status', 'proposed')
        limit = int(request.query_params.get('limit', 10))
        
        service = QualityImprovementService()
        improvements = service.get_improvement_recommendations(
            improvement_type=improvement_type,
            status=status_filter,
            limit=limit
        )
        
        serializer = QualityImprovementBasicSerializer(improvements, many=True)
        return Response(serializer.data)


class ImprovedPromptViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ImprovedPrompt.
    
    Provides CRUD operations and additional actions for 
    improved prompt management.
    """
    
    queryset = ImprovedPrompt.objects.all().order_by('-created_at')
    serializer_class = ImprovedPromptSerializer
    
    def get_queryset(self):
        """Return filtered queryset."""
        queryset = ImprovedPrompt.objects.all().order_by('-created_at')
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by type
        type_param = self.request.query_params.get('type')
        if type_param:
            queryset = queryset.filter(prompt_type=type_param)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a prompt.
        """
        prompt = self.get_object()
        
        if prompt.status != 'draft' and prompt.status != 'testing':
            return Response({
                'error': f"Prompt is in '{prompt.status}' status. Only 'draft' or 'testing' prompts can be activated."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        prompt.activate()
        
        return Response({
            'prompt_id': str(prompt.prompt_id),
            'name': prompt.name,
            'status': prompt.status,
            'message': 'Prompt activated'
        })
    
    @action(detail=True, methods=['post'])
    def create_new_version(self, request, pk=None):
        """
        Create a new version of a prompt.
        """
        prompt = self.get_object()
        
        if 'prompt_text' not in request.data:
            return Response({
                'error': "Missing required field: prompt_text"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        new_prompt = prompt.create_new_version(
            prompt_text=request.data['prompt_text'],
            description=request.data.get('description')
        )
        
        serializer = self.get_serializer(new_prompt)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get all active prompts.
        """
        active_prompts = ImprovedPrompt.objects.filter(status='active')
        serializer = self.get_serializer(active_prompts, many=True)
        return Response(serializer.data)


class RetrievalConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for RetrievalConfiguration.
    
    Provides CRUD operations and additional actions for 
    retrieval configuration management.
    """
    
    queryset = RetrievalConfiguration.objects.all().order_by('-created_at')
    serializer_class = RetrievalConfigurationSerializer
    
    def get_queryset(self):
        """Return filtered queryset."""
        queryset = RetrievalConfiguration.objects.all().order_by('-created_at')
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a configuration.
        """
        config = self.get_object()
        
        if config.status != 'draft' and config.status != 'testing':
            return Response({
                'error': f"Configuration is in '{config.status}' status. Only 'draft' or 'testing' configurations can be activated."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        config.activate()
        
        return Response({
            'config_id': str(config.config_id),
            'name': config.name,
            'status': config.status,
            'message': 'Configuration activated'
        })
    
    @action(detail=True, methods=['post'])
    def create_new_version(self, request, pk=None):
        """
        Create a new version of a configuration.
        """
        config = self.get_object()
        
        if 'parameters' not in request.data:
            return Response({
                'error': "Missing required field: parameters"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        new_config = config.create_new_version(
            parameters=request.data['parameters'],
            description=request.data.get('description')
        )
        
        serializer = self.get_serializer(new_config)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get the active configuration.
        """
        active_config = RetrievalConfiguration.objects.filter(status='active').first()
        
        if not active_config:
            return Response({
                'message': 'No active configuration found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(active_config)
        return Response(serializer.data)


class QualityMetricsViewSet(viewsets.ViewSet):
    """
    ViewSet for quality metrics.
    
    Provides actions for retrieving quality metrics.
    """
    
    @action(detail=False, methods=['get'])
    def overall(self, request):
        """
        Get overall quality metrics.
        """
        days = int(request.query_params.get('days', 30))
        
        service = QualityImprovementService()
        metrics = service.get_quality_metrics(days=days)
        
        serializer = QualityMetricsSerializer(metrics)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def run_pipeline(self, request):
        """
        Run the complete quality improvement pipeline.
        """
        task = run_complete_quality_pipeline_task.delay()
        
        return Response({
            'task_id': task.id,
            'message': 'Quality improvement pipeline started'
        }, status=status.HTTP_202_ACCEPTED)