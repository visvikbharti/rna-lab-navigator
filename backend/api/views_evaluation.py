"""
Views for the evaluation system.
"""

from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from celery.result import AsyncResult

from .models import (
    EvaluationSet,
    ReferenceQuestion,
    EvaluationRun,
    QuestionResult
)
from .serializers import (
    EvaluationSetSerializer,
    ReferenceQuestionSerializer,
    EvaluationRunSerializer,
    QuestionResultSerializer,
    TriggerEvaluationSerializer,
    EvaluationReportSerializer
)
from .evaluation.evaluation_utils import (
    run_evaluation,
    compare_runs,
    generate_evaluation_report
)
from .tasks import run_weekly_evaluation


class EvaluationSetViewSet(ModelViewSet):
    """
    ViewSet for managing evaluation sets.
    """
    queryset = EvaluationSet.objects.all().order_by('-created_at')
    serializer_class = EvaluationSetSerializer
    
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """
        Get all questions in this evaluation set.
        """
        evaluation_set = self.get_object()
        questions = ReferenceQuestion.objects.filter(evaluation_set=evaluation_set)
        serializer = ReferenceQuestionSerializer(questions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def runs(self, request, pk=None):
        """
        Get all evaluation runs for this set.
        """
        evaluation_set = self.get_object()
        runs = EvaluationRun.objects.filter(evaluation_set=evaluation_set).order_by('-run_date')
        serializer = EvaluationRunSerializer(runs, many=True)
        return Response(serializer.data)


class ReferenceQuestionViewSet(ModelViewSet):
    """
    ViewSet for managing reference questions.
    """
    queryset = ReferenceQuestion.objects.all()
    serializer_class = ReferenceQuestionSerializer
    
    def get_queryset(self):
        """
        Optionally filter questions by evaluation set.
        """
        queryset = ReferenceQuestion.objects.all()
        eval_set = self.request.query_params.get('evaluation_set', None)
        if eval_set is not None:
            queryset = queryset.filter(evaluation_set__id=eval_set)
        return queryset


class EvaluationRunViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for accessing evaluation runs (read-only).
    """
    queryset = EvaluationRun.objects.all().order_by('-run_date')
    serializer_class = EvaluationRunSerializer
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        Get all question results for this run.
        """
        run = self.get_object()
        results = QuestionResult.objects.filter(evaluation_run=run)
        serializer = QuestionResultSerializer(results, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def compare(self, request, pk=None):
        """
        Compare this run with a previous run.
        """
        current_run = self.get_object()
        previous_run_id = request.query_params.get('previous_run', None)
        
        try:
            comparison = compare_runs(current_run.id, previous_run_id)
            return Response(comparison)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class QuestionResultViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for accessing question results (read-only).
    """
    queryset = QuestionResult.objects.all()
    serializer_class = QuestionResultSerializer
    
    def get_queryset(self):
        """
        Optionally filter results by evaluation run.
        """
        queryset = QuestionResult.objects.all()
        run_id = self.request.query_params.get('run', None)
        if run_id is not None:
            queryset = queryset.filter(evaluation_run__id=run_id)
        return queryset


class TriggerEvaluationView(APIView):
    """
    API endpoint to trigger an evaluation run.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Trigger an evaluation run for a specific evaluation set.
        """
        serializer = TriggerEvaluationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        evaluation_set_id = serializer.validated_data['evaluation_set_id']
        use_hybrid = serializer.validated_data.get('use_hybrid', True)
        use_cache = serializer.validated_data.get('use_cache', False)
        notes = serializer.validated_data.get('notes', '')
        
        # Check if evaluation set exists
        try:
            eval_set = EvaluationSet.objects.get(id=evaluation_set_id)
        except EvaluationSet.DoesNotExist:
            return Response(
                {"error": f"Evaluation set with ID {evaluation_set_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Option 1: Run synchronously (suitable for small evaluation sets)
        if eval_set.questions.count() < 5:  # Small enough to run synchronously
            try:
                evaluation_run = run_evaluation(
                    evaluation_set_id=evaluation_set_id,
                    use_hybrid=use_hybrid,
                    use_cache=use_cache
                )
                
                # Update notes if provided
                if notes:
                    evaluation_run.notes = notes
                    evaluation_run.save()
                
                serializer = EvaluationRunSerializer(evaluation_run)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                return Response(
                    {"error": f"Error running evaluation: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Option 2: Run asynchronously with Celery (for larger evaluation sets)
        else:
            try:
                # Create a placeholder run with status 'pending'
                evaluation_run = EvaluationRun.objects.create(
                    evaluation_set=eval_set,
                    status='pending',
                    total_questions=eval_set.questions.count(),
                    notes=notes
                )
                
                # Trigger the Celery task
                task = run_weekly_evaluation.delay()
                
                return Response({
                    "message": "Evaluation started asynchronously",
                    "run_id": evaluation_run.id,
                    "task_id": task.id,
                    "status": "pending"
                }, status=status.HTTP_202_ACCEPTED)
            
            except Exception as e:
                return Response(
                    {"error": f"Error starting evaluation: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class EvaluationReportView(APIView):
    """
    API endpoint to get a detailed report for an evaluation run.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, run_id):
        """
        Get a detailed report for an evaluation run.
        """
        try:
            # Ensure the run exists
            get_object_or_404(EvaluationRun, id=run_id)
            
            # Generate the report
            report = generate_evaluation_report(run_id)
            
            # Serialize and return the report
            serializer = EvaluationReportSerializer(report)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {"error": f"Error generating report: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )