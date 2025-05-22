"""
Views for the enhanced feedback system.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
import datetime
import json

from .models import (
    EnhancedFeedback,
    FeedbackCategory,
    FeedbackTheme,
    FeedbackAnalysis,
    FeedbackThemeMapping
)
from .serializers import (
    EnhancedFeedbackSerializer,
    EnhancedFeedbackCreateSerializer,
    EnhancedFeedbackUpdateSerializer,
    FeedbackCategorySerializer,
    FeedbackThemeSerializer,
    FeedbackAnalysisSerializer,
    FeedbackThemeMappingSerializer
)
from ..models import QueryHistory


class EnhancedFeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet for enhanced user feedback on answers.
    Provides CRUD operations and analytics for feedback data.
    """
    queryset = EnhancedFeedback.objects.all().order_by('-created_at')
    filterset_fields = ['rating', 'category', 'status']
    search_fields = ['comment', 'review_notes', 'system_response']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['created_at', 'reviewed_at']
    
    def get_permissions(self):
        """
        Override to allow anonymous feedback creation
        but restrict other operations to authenticated users.
        """
        if self.action == 'create':
            return [AllowAny()]
        elif self.action in ['list', 'retrieve', 'stats', 'trends']:
            return [IsAuthenticated()]
        return [IsAdminUser()]
    
    def get_serializer_class(self):
        """Return the appropriate serializer based on the action"""
        if self.action == 'create':
            return EnhancedFeedbackCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EnhancedFeedbackUpdateSerializer
        return EnhancedFeedbackSerializer
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Mark feedback as reviewed"""
        feedback = self.get_object()
        notes = request.data.get('notes', '')
        
        feedback.mark_reviewed(request.user, notes)
        
        return Response({
            'status': 'success',
            'message': 'Feedback marked as reviewed',
            'feedback': EnhancedFeedbackSerializer(feedback).data
        })
    
    @action(detail=True, methods=['post'])
    def action(self, request, pk=None):
        """Mark feedback as actioned with response"""
        feedback = self.get_object()
        response = request.data.get('response', '')
        actions = request.data.get('actions', None)
        
        feedback.mark_actioned(response, actions)
        
        return Response({
            'status': 'success',
            'message': 'Feedback marked as actioned',
            'feedback': EnhancedFeedbackSerializer(feedback).data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get comprehensive feedback statistics.
        Includes ratings distribution, category breakdown, and quality metrics.
        """
        # Base queryset - optionally filter by date range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = EnhancedFeedback.objects.all()
        
        if start_date:
            try:
                start_datetime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=start_datetime)
            except ValueError:
                return Response(
                    {"error": "Invalid start_date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if end_date:
            try:
                end_datetime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(created_at__lte=end_datetime)
            except ValueError:
                return Response(
                    {"error": "Invalid end_date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Total feedback count
        total_count = queryset.count()
        if total_count == 0:
            return Response({
                'total_feedback': 0,
                'message': 'No feedback data available for the selected period'
            })
        
        # Count by rating
        rating_counts = queryset.values('rating').annotate(count=Count('id'))
        rating_distribution = {item['rating']: item['count'] for item in rating_counts}
        
        # Calculate rating percentages
        positive_count = rating_distribution.get('thumbs_up', 0)
        negative_count = rating_distribution.get('thumbs_down', 0)
        neutral_count = rating_distribution.get('neutral', 0)
        
        # Categories breakdown
        category_counts = queryset.values('category').annotate(count=Count('id'))
        category_distribution = {item['category']: item['count'] for item in category_counts}
        
        # Status distribution
        status_counts = queryset.values('status').annotate(count=Count('id'))
        status_distribution = {item['status']: item['count'] for item in status_counts}
        
        # Average ratings for different aspects
        avg_ratings = {}
        for field in ['relevance_rating', 'accuracy_rating', 'completeness_rating', 
                     'clarity_rating', 'citation_rating']:
            display_name = field.replace('_rating', '')
            avg = queryset.filter(**{f'{field}__isnull': False}).aggregate(avg=Avg(field))
            avg_ratings[display_name] = avg['avg']
        
        # Specific issues analysis
        all_issues = []
        feedbacks_with_issues = queryset.filter(
            specific_issues__isnull=False
        ).values_list('specific_issues', flat=True)
        
        for issues in feedbacks_with_issues:
            if issues:
                all_issues.extend(issues)
        
        # Count occurrences of each issue
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Sort by frequency
        sorted_issues = sorted(
            issue_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        top_issues = sorted_issues[:10] if sorted_issues else []
        
        # Recent trend (last 7 days vs previous 7 days)
        today = timezone.now().date()
        week_ago = today - datetime.timedelta(days=7)
        two_weeks_ago = today - datetime.timedelta(days=14)
        
        recent_data = queryset.filter(created_at__gte=week_ago)
        recent_positive = recent_data.filter(rating='thumbs_up').count()
        recent_negative = recent_data.filter(rating='thumbs_down').count()
        
        previous_data = queryset.filter(
            created_at__gte=two_weeks_ago,
            created_at__lt=week_ago
        )
        previous_positive = previous_data.filter(rating='thumbs_up').count()
        previous_negative = previous_data.filter(rating='thumbs_down').count()
        
        # Calculate week-over-week changes
        positive_change = calculate_percentage_change(previous_positive, recent_positive)
        negative_change = calculate_percentage_change(previous_negative, recent_negative)
        
        # Response data
        response_data = {
            'total_feedback': total_count,
            'rating_distribution': rating_distribution,
            'category_distribution': category_distribution,
            'status_distribution': status_distribution,
            'rating_percentages': {
                'positive': (positive_count / total_count) * 100 if total_count > 0 else 0,
                'negative': (negative_count / total_count) * 100 if total_count > 0 else 0,
                'neutral': (neutral_count / total_count) * 100 if total_count > 0 else 0,
            },
            'average_ratings': avg_ratings,
            'top_issues': top_issues,
            'weekly_trend': {
                'recent': {
                    'positive': recent_positive,
                    'negative': recent_negative,
                    'total': recent_data.count()
                },
                'previous': {
                    'positive': previous_positive,
                    'negative': previous_negative,
                    'total': previous_data.count()
                },
                'changes': {
                    'positive': positive_change,
                    'negative': negative_change,
                }
            },
            'period': {
                'start': start_date if start_date else 'all time',
                'end': end_date if end_date else 'present',
            }
        }
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """
        Get feedback trends over time.
        Returns daily and weekly aggregates for visualization.
        """
        # Determine time range - default to last 30 days
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Get feedback in date range
        queryset = EnhancedFeedback.objects.filter(
            created_at__gte=datetime.datetime.combine(start_date, datetime.time.min),
            created_at__lte=datetime.datetime.combine(end_date, datetime.time.max)
        )
        
        # Generate daily counts
        daily_data = []
        current_date = start_date
        
        while current_date <= end_date:
            next_date = current_date + datetime.timedelta(days=1)
            
            day_feedback = queryset.filter(
                created_at__gte=datetime.datetime.combine(current_date, datetime.time.min),
                created_at__lt=datetime.datetime.combine(next_date, datetime.time.min)
            )
            
            daily_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'total': day_feedback.count(),
                'positive': day_feedback.filter(rating='thumbs_up').count(),
                'negative': day_feedback.filter(rating='thumbs_down').count(),
                'neutral': day_feedback.filter(rating='neutral').count(),
            })
            
            current_date = next_date
        
        # Generate weekly aggregates
        weekly_data = []
        for i in range(0, days, 7):
            week_start = end_date - datetime.timedelta(days=min(i+6, days-1))
            week_end = end_date - datetime.timedelta(days=i)
            
            week_feedback = queryset.filter(
                created_at__gte=datetime.datetime.combine(week_start, datetime.time.min),
                created_at__lte=datetime.datetime.combine(week_end, datetime.time.max)
            )
            
            # Calculate average ratings for the week
            week_avg_ratings = {}
            for field in ['relevance_rating', 'accuracy_rating', 'completeness_rating', 
                         'clarity_rating', 'citation_rating']:
                display_name = field.replace('_rating', '')
                avg = week_feedback.filter(**{f'{field}__isnull': False}).aggregate(avg=Avg(field))
                week_avg_ratings[display_name] = avg['avg']
            
            weekly_data.append({
                'week_starting': week_start.strftime('%Y-%m-%d'),
                'week_ending': week_end.strftime('%Y-%m-%d'),
                'total': week_feedback.count(),
                'positive': week_feedback.filter(rating='thumbs_up').count(),
                'negative': week_feedback.filter(rating='thumbs_down').count(),
                'neutral': week_feedback.filter(rating='neutral').count(),
                'average_ratings': week_avg_ratings
            })
        
        # Category trends over time
        category_trends = {}
        
        for category in set(queryset.values_list('category', flat=True)):
            if not category:
                continue
                
            category_data = []
            current_date = start_date
            
            while current_date <= end_date:
                if (end_date - current_date).days % 3 == 0:  # Sample every 3 days to reduce data points
                    next_date = current_date + datetime.timedelta(days=3)
                    
                    period_feedback = queryset.filter(
                        category=category,
                        created_at__gte=datetime.datetime.combine(current_date, datetime.time.min),
                        created_at__lt=datetime.datetime.combine(next_date, datetime.time.min)
                    )
                    
                    category_data.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'count': period_feedback.count(),
                    })
                
                current_date = current_date + datetime.timedelta(days=1)
            
            if category_data:
                category_trends[category] = category_data
        
        return Response({
            'daily': daily_data,
            'weekly': weekly_data,
            'category_trends': category_trends,
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'days': days
            }
        })


class FeedbackCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for feedback categories.
    Allows defining and managing feedback options.
    """
    queryset = FeedbackCategory.objects.all().order_by('display_order', 'name')
    serializer_class = FeedbackCategorySerializer
    filterset_fields = ['type', 'is_active', 'parent']
    
    def get_permissions(self):
        """Allow read access to everyone, but restrict writes to admin"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]
    
    @action(detail=False, methods=['get'])
    def root_categories(self, request):
        """Get only root-level categories (no parent)"""
        categories = FeedbackCategory.objects.filter(
            parent=None,
            is_active=True
        ).order_by('display_order', 'name')
        
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get categories grouped by type"""
        category_type = request.query_params.get('type')
        
        if category_type:
            categories = FeedbackCategory.objects.filter(
                type=category_type,
                is_active=True
            ).order_by('display_order', 'name')
        else:
            # Group by type
            result = {}
            for type_choice in FeedbackCategory.TYPE_CHOICES:
                type_value = type_choice[0]
                categories = FeedbackCategory.objects.filter(
                    type=type_value,
                    is_active=True
                ).order_by('display_order', 'name')
                
                result[type_value] = self.get_serializer(categories, many=True).data
            
            return Response(result)
        
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


class FeedbackThemeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for feedback themes.
    Allows managing themes for feedback categorization and improvement tracking.
    """
    queryset = FeedbackTheme.objects.all().order_by('-feedback_count', 'status')
    serializer_class = FeedbackThemeSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['status', 'priority', 'assigned_to']
    search_fields = ['title', 'description', 'solution_notes', 'tags']
    
    @action(detail=True, methods=['post'])
    def add_feedback(self, request, pk=None):
        """Add feedback to this theme"""
        theme = self.get_object()
        feedback_ids = request.data.get('feedback_ids', [])
        
        if not feedback_ids:
            return Response(
                {"error": "No feedback IDs provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get feedback objects
        feedback_objects = EnhancedFeedback.objects.filter(id__in=feedback_ids)
        if not feedback_objects:
            return Response(
                {"error": "No valid feedback IDs found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create mappings
        created_count = 0
        for feedback in feedback_objects:
            # Skip if mapping already exists
            if FeedbackThemeMapping.objects.filter(feedback=feedback, theme=theme).exists():
                continue
            
            FeedbackThemeMapping.objects.create(
                feedback=feedback,
                theme=theme,
                mapped_by=request.user,
                relevance_score=1.0  # Default to full relevance
            )
            created_count += 1
        
        # Update feedback count on theme
        theme.feedback_count = FeedbackThemeMapping.objects.filter(theme=theme).count()
        theme.save()
        
        return Response({
            'status': 'success',
            'message': f'Added {created_count} feedback items to theme',
            'theme': self.get_serializer(theme).data
        })
    
    @action(detail=True, methods=['get'])
    def feedback(self, request, pk=None):
        """Get all feedback items for this theme"""
        theme = self.get_object()
        
        # Get mappings with feedback
        mappings = FeedbackThemeMapping.objects.filter(theme=theme)
        
        # Return mappings with feedback data
        serializer = FeedbackThemeMappingSerializer(mappings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change the status of this theme"""
        theme = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if new_status not in dict(FeedbackTheme.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status
        theme.status = new_status
        
        # If resolved, set resolution date
        if new_status == 'resolved':
            theme.resolution_date = timezone.now()
        else:
            theme.resolution_date = None
        
        # Update notes if provided
        if notes:
            theme.solution_notes = notes
        
        theme.save()
        
        return Response({
            'status': 'success',
            'message': f'Theme status changed to {new_status}',
            'theme': self.get_serializer(theme).data
        })


class FeedbackAnalysisViewSet(viewsets.ModelViewSet):
    """
    ViewSet for feedback analysis.
    Manages automated analysis of feedback for system improvement.
    """
    queryset = FeedbackAnalysis.objects.all().order_by('-analysis_date')
    serializer_class = FeedbackAnalysisSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate a new feedback analysis.
        Analyzes feedback over a specified period.
        """
        # Get date range
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"error": "Both start_date and end_date are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            date_range_start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            date_range_end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            date_range_end = date_range_end.replace(hour=23, minute=59, second=59)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get feedback for analysis
        feedback = EnhancedFeedback.objects.filter(
            created_at__gte=date_range_start,
            created_at__lte=date_range_end
        )
        
        if not feedback.exists():
            return Response(
                {"error": "No feedback found in the specified date range"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Run the analysis
        analysis_results = self._analyze_feedback(feedback, date_range_start, date_range_end)
        
        # Create the analysis record
        analysis = FeedbackAnalysis.objects.create(
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            total_feedback_analyzed=feedback.count(),
            positive_feedback_count=feedback.filter(rating='thumbs_up').count(),
            negative_feedback_count=feedback.filter(rating='thumbs_down').count(),
            neutral_feedback_count=feedback.filter(rating='neutral').count(),
            **analysis_results
        )
        
        return Response({
            'status': 'success',
            'message': 'Analysis generated successfully',
            'analysis': FeedbackAnalysisSerializer(analysis).data
        })
    
    @action(detail=True, methods=['post'])
    def implement(self, request, pk=None):
        """Mark analysis actions as implemented"""
        analysis = self.get_object()
        actions = request.data.get('actions', [])
        
        if not actions:
            return Response(
                {"error": "No actions provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update implemented actions
        analysis.actions_implemented = actions
        analysis.implementation_date = timezone.now()
        analysis.implemented_by = request.user
        
        # Add effectiveness metrics if provided
        if 'effectiveness_metrics' in request.data:
            analysis.effectiveness_metrics = request.data['effectiveness_metrics']
        
        analysis.save()
        
        return Response({
            'status': 'success',
            'message': 'Analysis implementation updated',
            'analysis': FeedbackAnalysisSerializer(analysis).data
        })
    
    def _analyze_feedback(self, feedback, start_date, end_date):
        """
        Analyze feedback and generate insights.
        Returns dict with analysis results.
        """
        # Top issues analysis
        issues = []
        for fb in feedback.filter(specific_issues__isnull=False):
            if fb.specific_issues:
                issues.extend(fb.specific_issues)
        
        issue_counts = {}
        for issue in issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        top_issues = [
            {"issue": issue, "count": count}
            for issue, count in sorted(
                issue_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        ]
        
        # Category distribution
        category_counts = feedback.values('category').annotate(count=Count('id'))
        category_distribution = {
            item['category']: item['count'] for item in category_counts if item['category']
        }
        
        # Improvement opportunities based on negative feedback
        negative_feedback = feedback.filter(rating='thumbs_down')
        
        improvement_opportunities = []
        
        # 1. Source quality issues
        source_issues = negative_feedback.filter(
            source_quality_issues__isnull=False
        ).exclude(
            source_quality_issues={}
        ).exclude(
            source_quality_issues=[]
        )
        
        if source_issues.exists():
            improvement_opportunities.append({
                "area": "Source Quality",
                "description": "Improve source retrieval and quality",
                "feedback_count": source_issues.count(),
                "priority": "high" if source_issues.count() > 5 else "medium"
            })
        
        # 2. Answer clarity
        clarity_issues = negative_feedback.filter(
            clarity_rating__lt=3
        )
        
        if clarity_issues.exists():
            improvement_opportunities.append({
                "area": "Answer Clarity",
                "description": "Improve answer formatting and clarity",
                "feedback_count": clarity_issues.count(),
                "priority": "high" if clarity_issues.count() > 5 else "medium"
            })
        
        # 3. Answer completeness
        completeness_issues = negative_feedback.filter(
            completeness_rating__lt=3
        )
        
        if completeness_issues.exists():
            improvement_opportunities.append({
                "area": "Answer Completeness",
                "description": "Provide more comprehensive answers",
                "feedback_count": completeness_issues.count(),
                "priority": "high" if completeness_issues.count() > 5 else "medium"
            })
        
        # 4. Citation accuracy
        citation_issues = negative_feedback.filter(
            citation_rating__lt=3
        )
        
        if citation_issues.exists():
            improvement_opportunities.append({
                "area": "Citation Accuracy",
                "description": "Improve citation accuracy and specificity",
                "feedback_count": citation_issues.count(),
                "priority": "high" if citation_issues.count() > 5 else "medium"
            })
        
        # Trend analysis - compare periods
        total_days = (end_date - start_date).days
        mid_point = start_date + datetime.timedelta(days=total_days // 2)
        
        first_half = feedback.filter(created_at__lt=mid_point)
        second_half = feedback.filter(created_at__gte=mid_point)
        
        # Calculate improvement or decline in rating ratios
        first_half_positive = first_half.filter(rating='thumbs_up').count()
        first_half_total = first_half.count() or 1  # Avoid division by zero
        first_half_ratio = (first_half_positive / first_half_total) * 100
        
        second_half_positive = second_half.filter(rating='thumbs_up').count()
        second_half_total = second_half.count() or 1
        second_half_ratio = (second_half_positive / second_half_total) * 100
        
        rating_change = second_half_ratio - first_half_ratio
        
        trend_analysis = {
            "first_period": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": mid_point.strftime('%Y-%m-%d'),
                "positive_percentage": first_half_ratio,
                "total_feedback": first_half_total
            },
            "second_period": {
                "start": mid_point.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d'),
                "positive_percentage": second_half_ratio,
                "total_feedback": second_half_total
            },
            "changes": {
                "rating_change": rating_change,
                "trend": "improving" if rating_change > 0 else "declining"
            }
        }
        
        # Generate recommended actions
        recommended_actions = []
        
        # Add actions based on top issues
        if top_issues:
            recommended_actions.append({
                "action": "Address top reported issues",
                "description": f"Focus on the top {len(top_issues)} reported issues",
                "priority": "high"
            })
        
        # Add actions based on improvement opportunities
        for opportunity in improvement_opportunities:
            recommended_actions.append({
                "action": f"Improve {opportunity['area'].lower()}",
                "description": opportunity['description'],
                "priority": opportunity['priority']
            })
        
        # Add trend-based action
        if rating_change < 0:
            recommended_actions.append({
                "action": "Investigate declining satisfaction",
                "description": "User satisfaction is trending downward - investigate root causes",
                "priority": "critical"
            })
        
        # Identify priority areas
        priority_areas = []
        
        # Categories with high negative feedback
        for category, count in category_distribution.items():
            category_feedback = feedback.filter(category=category)
            negative_count = category_feedback.filter(rating='thumbs_down').count()
            negative_ratio = (negative_count / count) * 100
            
            if negative_ratio > 30:  # More than 30% negative feedback
                priority_areas.append({
                    "area": category,
                    "reason": f"High negative feedback ratio ({negative_ratio:.1f}%)",
                    "priority": "high" if negative_ratio > 50 else "medium"
                })
        
        # Return all analysis results
        return {
            "top_issues": top_issues,
            "category_distribution": category_distribution,
            "improvement_opportunities": improvement_opportunities,
            "trend_analysis": trend_analysis,
            "recommended_actions": recommended_actions,
            "priority_areas": priority_areas
        }


class FeedbackThemeMappingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing feedback-theme mappings.
    Links individual feedback items to thematic issues.
    """
    queryset = FeedbackThemeMapping.objects.all().order_by('-mapped_at')
    serializer_class = FeedbackThemeMappingSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['theme', 'feedback', 'mapped_by']
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple mappings at once"""
        theme_id = request.data.get('theme_id')
        feedback_ids = request.data.get('feedback_ids', [])
        relevance_score = request.data.get('relevance_score', 1.0)
        notes = request.data.get('notes', '')
        
        if not theme_id or not feedback_ids:
            return Response(
                {"error": "theme_id and feedback_ids are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            theme = FeedbackTheme.objects.get(id=theme_id)
        except FeedbackTheme.DoesNotExist:
            return Response(
                {"error": "Theme not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create mappings
        created_mappings = []
        for feedback_id in feedback_ids:
            try:
                feedback = EnhancedFeedback.objects.get(id=feedback_id)
                
                # Skip if mapping already exists
                if FeedbackThemeMapping.objects.filter(feedback=feedback, theme=theme).exists():
                    continue
                
                mapping = FeedbackThemeMapping.objects.create(
                    feedback=feedback,
                    theme=theme,
                    mapped_by=request.user,
                    relevance_score=relevance_score,
                    notes=notes
                )
                
                created_mappings.append(mapping)
            except EnhancedFeedback.DoesNotExist:
                # Skip invalid feedback IDs
                continue
        
        # Update feedback count on theme
        theme.feedback_count = FeedbackThemeMapping.objects.filter(theme=theme).count()
        theme.save()
        
        return Response({
            'status': 'success',
            'message': f'Created {len(created_mappings)} mappings',
            'mappings': FeedbackThemeMappingSerializer(created_mappings, many=True).data
        })


# Helper functions
def calculate_percentage_change(old_value, new_value):
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 100 if new_value > 0 else 0
    
    return ((new_value - old_value) / old_value) * 100