"""
Analytics views for search quality monitoring.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status
from django.db.models import Avg, Count, F, Q
from django.utils import timezone
from datetime import timedelta

from .models import SearchAnalytics
from ..models import Feedback, QueryHistory
from .services import SearchService


class SearchQualityViewSet(viewsets.ViewSet):
    """
    ViewSet for accessing search quality metrics and feedback data.
    Provides aggregated metrics on search performance and user satisfaction.
    """
    
    def list(self, request):
        """
        Get summary of search quality metrics.
        
        Returns:
            dict: Summary statistics for search quality
        """
        # Calculate date ranges
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        
        # Get overall search metrics
        total_searches = SearchAnalytics.objects.count()
        recent_searches = SearchAnalytics.objects.filter(timestamp__gte=seven_days_ago).count()
        
        # Get feedback metrics
        search_feedback = Feedback.objects.filter(
            query_history__in=QueryHistory.objects.filter(
                id__in=SearchAnalytics.objects.values_list('query_history', flat=True)
            )
        )
        
        positive_feedback = search_feedback.filter(rating='thumbs_up').count()
        negative_feedback = search_feedback.filter(rating='thumbs_down').count()
        
        total_feedback = positive_feedback + negative_feedback
        feedback_rate = total_feedback / total_searches if total_searches > 0 else 0
        satisfaction_rate = positive_feedback / total_feedback if total_feedback > 0 else 0
        
        # Calculate average ratings for search aspects
        rating_metrics = {}
        for field in ['retrieval_quality', 'answer_relevance', 'citation_accuracy']:
            avg = search_feedback.filter(**{f'{field}__isnull': False}).aggregate(avg=Avg(field))
            rating_metrics[field] = avg['avg']
        
        # Get search performance metrics
        search_times = SearchAnalytics.objects.filter(
            search_time_ms__isnull=False
        ).aggregate(
            avg_search_time=Avg('search_time_ms'),
            avg_reranking_time=Avg('reranking_time_ms'),
            avg_answer_time=Avg('answer_time_ms')
        )
        
        # Calculate recent trends
        recent_search_feedback = search_feedback.filter(created_at__gte=seven_days_ago)
        recent_positive = recent_search_feedback.filter(rating='thumbs_up').count()
        recent_negative = recent_search_feedback.filter(rating='thumbs_down').count()
        
        # Calculate changes from previous period
        previous_period_start = thirty_days_ago
        previous_period_end = seven_days_ago
        
        previous_feedback = search_feedback.filter(
            created_at__gte=previous_period_start,
            created_at__lt=previous_period_end
        )
        
        previous_positive = previous_feedback.filter(rating='thumbs_up').count()
        previous_negative = previous_feedback.filter(rating='thumbs_down').count()
        previous_total = previous_positive + previous_negative
        
        satisfaction_change = 0
        if previous_total > 0 and total_feedback > 0:
            previous_rate = previous_positive / previous_total
            satisfaction_change = ((satisfaction_rate - previous_rate) / previous_rate) * 100
        
        return Response({
            'search_metrics': {
                'total_searches': total_searches,
                'recent_searches': recent_searches,
                'avg_search_time_ms': search_times.get('avg_search_time'),
                'avg_reranking_time_ms': search_times.get('avg_reranking_time'),
                'avg_answer_time_ms': search_times.get('avg_answer_time'),
            },
            'feedback_metrics': {
                'total_feedback': total_feedback,
                'positive_feedback': positive_feedback,
                'negative_feedback': negative_feedback, 
                'feedback_rate': feedback_rate,
                'satisfaction_rate': satisfaction_rate,
                'satisfaction_change': satisfaction_change,
                'rating_metrics': rating_metrics
            }
        })
    
    @action(detail=False, methods=['get'])
    def quality_by_doc_type(self, request):
        """
        Get search quality metrics broken down by document type.
        
        Returns:
            dict: Metrics for each document type
        """
        # Get document types from analytics
        doc_types = set(SearchAnalytics.objects.values_list('doc_type', flat=True).distinct())
        doc_types = [dt for dt in doc_types if dt]  # Filter out empty values
        
        results = {}
        for doc_type in doc_types:
            # Get analytics for this doc type
            analytics = SearchAnalytics.objects.filter(doc_type=doc_type)
            
            # Get feedback for searches with this doc type
            search_feedback = Feedback.objects.filter(
                query_history__in=QueryHistory.objects.filter(
                    id__in=analytics.values_list('query_history', flat=True)
                )
            )
            
            positive_count = search_feedback.filter(rating='thumbs_up').count()
            negative_count = search_feedback.filter(rating='thumbs_down').count()
            total_count = positive_count + negative_count
            
            # Calculate ratings
            rating_metrics = {}
            for field in ['retrieval_quality', 'answer_relevance', 'citation_accuracy']:
                avg = search_feedback.filter(**{f'{field}__isnull': False}).aggregate(avg=Avg(field))
                rating_metrics[field] = avg['avg']
            
            results[doc_type] = {
                'search_count': analytics.count(),
                'feedback_count': total_count,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'satisfaction_rate': positive_count / total_count if total_count > 0 else 0,
                'rating_metrics': rating_metrics,
                'avg_search_time': analytics.filter(search_time_ms__isnull=False).aggregate(avg=Avg('search_time_ms'))['avg']
            }
        
        return Response(results)
    
    @action(detail=False, methods=['get'])
    def quality_by_ranking_profile(self, request):
        """
        Get search quality metrics broken down by search ranking profile.
        
        Returns:
            dict: Metrics for each ranking profile
        """
        # Get profiles from analytics that have been used
        profile_ids = set(
            SearchAnalytics.objects.filter(ranking_profile__isnull=False)
            .values_list('ranking_profile', flat=True)
            .distinct()
        )
        
        # Build metrics for each profile
        results = {}
        for profile_id in profile_ids:
            from .models import SearchRankingProfile
            profile = SearchRankingProfile.objects.get(id=profile_id)
            
            # Get analytics for this profile
            analytics = SearchAnalytics.objects.filter(ranking_profile=profile)
            
            # Get feedback for searches with this profile
            search_feedback = Feedback.objects.filter(
                query_history__in=QueryHistory.objects.filter(
                    id__in=analytics.values_list('query_history', flat=True)
                )
            )
            
            positive_count = search_feedback.filter(rating='thumbs_up').count()
            negative_count = search_feedback.filter(rating='thumbs_down').count()
            total_count = positive_count + negative_count
            
            # Calculate ratings
            rating_metrics = {}
            for field in ['retrieval_quality', 'answer_relevance', 'citation_accuracy']:
                avg = search_feedback.filter(**{f'{field}__isnull': False}).aggregate(avg=Avg(field))
                rating_metrics[field] = avg['avg']
            
            results[str(profile_id)] = {
                'profile_name': profile.name,
                'search_count': analytics.count(),
                'feedback_count': total_count,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'satisfaction_rate': positive_count / total_count if total_count > 0 else 0,
                'rating_metrics': rating_metrics,
                'avg_search_time': analytics.filter(search_time_ms__isnull=False).aggregate(avg=Avg('search_time_ms'))['avg']
            }
        
        return Response(results)
    
    @action(detail=False, methods=['get'])
    def reranking_impact(self, request):
        """
        Get metrics showing the impact of reranking on search quality.
        
        Returns:
            dict: Metrics with and without reranking
        """
        # Get searches with reranking
        with_reranking = SearchAnalytics.objects.filter(
            Q(metadata__has_key='use_reranking') & 
            Q(metadata__use_reranking=True)
        )
        
        # Get searches without reranking
        without_reranking = SearchAnalytics.objects.filter(
            Q(metadata__has_key='use_reranking') & 
            Q(metadata__use_reranking=False)
        )
        
        # Calculate metrics for searches with reranking
        with_reranking_metrics = {}
        if with_reranking.exists():
            with_reranking_feedback = Feedback.objects.filter(
                query_history__in=QueryHistory.objects.filter(
                    id__in=with_reranking.values_list('query_history', flat=True)
                )
            )
            
            positive_count = with_reranking_feedback.filter(rating='thumbs_up').count()
            negative_count = with_reranking_feedback.filter(rating='thumbs_down').count()
            total_count = positive_count + negative_count
            
            with_reranking_metrics = {
                'search_count': with_reranking.count(),
                'feedback_count': total_count,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'satisfaction_rate': positive_count / total_count if total_count > 0 else 0,
                'avg_search_time': with_reranking.filter(search_time_ms__isnull=False).aggregate(avg=Avg('search_time_ms'))['avg'],
                'avg_reranking_time': with_reranking.filter(reranking_time_ms__isnull=False).aggregate(avg=Avg('reranking_time_ms'))['avg'],
            }
        
        # Calculate metrics for searches without reranking
        without_reranking_metrics = {}
        if without_reranking.exists():
            without_reranking_feedback = Feedback.objects.filter(
                query_history__in=QueryHistory.objects.filter(
                    id__in=without_reranking.values_list('query_history', flat=True)
                )
            )
            
            positive_count = without_reranking_feedback.filter(rating='thumbs_up').count()
            negative_count = without_reranking_feedback.filter(rating='thumbs_down').count()
            total_count = positive_count + negative_count
            
            without_reranking_metrics = {
                'search_count': without_reranking.count(),
                'feedback_count': total_count,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'satisfaction_rate': positive_count / total_count if total_count > 0 else 0,
                'avg_search_time': without_reranking.filter(search_time_ms__isnull=False).aggregate(avg=Avg('search_time_ms'))['avg'],
            }
        
        return Response({
            'with_reranking': with_reranking_metrics,
            'without_reranking': without_reranking_metrics,
        })
    
    @action(detail=False, methods=['get'])
    def common_issues(self, request):
        """
        Get common issues reported in search-related feedback.
        
        Returns:
            dict: Categorized issues with counts
        """
        # Get all search-related feedback
        search_feedback = Feedback.objects.filter(
            query_history__in=QueryHistory.objects.filter(
                id__in=SearchAnalytics.objects.values_list('query_history', flat=True)
            )
        )
        
        # Extract specific issues
        issues = []
        for feedback in search_feedback:
            if feedback.specific_issues:
                issues.extend(feedback.specific_issues)
        
        # Count occurrences of each issue
        issue_counts = {}
        for issue in issues:
            if issue in issue_counts:
                issue_counts[issue] += 1
            else:
                issue_counts[issue] = 1
        
        # Sort issues by count
        sorted_issues = [
            {'name': issue, 'count': count}
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Group issues by category if possible
        search_issues = [i for i in sorted_issues if 'search' in i['name'].lower() or 'result' in i['name'].lower()]
        ranking_issues = [i for i in sorted_issues if 'rank' in i['name'].lower() or 'order' in i['name'].lower()]
        relevance_issues = [i for i in sorted_issues if 'relevan' in i['name'].lower()]
        other_issues = [i for i in sorted_issues if i not in search_issues and i not in ranking_issues and i not in relevance_issues]
        
        return Response({
            'all_issues': sorted_issues[:10],
            'search_issues': search_issues[:5],
            'ranking_issues': ranking_issues[:5],
            'relevance_issues': relevance_issues[:5],
            'other_issues': other_issues[:5]
        })
    
    @action(detail=False, methods=['get'])
    def performance_over_time(self, request):
        """
        Get search performance metrics over time.
        
        Query parameters:
        - days: Number of days to look back (default 30)
        - interval: Interval for grouping (day, week, month) (default 'day')
        
        Returns:
            dict: Time series data for search performance metrics
        """
        days = int(request.query_params.get('days', 30))
        interval = request.query_params.get('interval', 'day')
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get search analytics in range
        analytics = SearchAnalytics.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        # Group by interval
        from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
        
        trunc_func = {
            'day': TruncDay,
            'week': TruncWeek,
            'month': TruncMonth
        }.get(interval, TruncDay)
        
        # Calculate aggregated metrics by interval
        time_series = analytics.annotate(
            interval=trunc_func('timestamp')
        ).values('interval').annotate(
            count=Count('id'),
            avg_search_time=Avg('search_time_ms'),
            avg_reranking_time=Avg('reranking_time_ms'),
            avg_answer_time=Avg('answer_time_ms')
        ).order_by('interval')
        
        # Get feedback rates for each interval
        for point in time_series:
            interval_start = point['interval']
            interval_end = interval_start + timedelta(days=1 if interval == 'day' else 7 if interval == 'week' else 30)
            
            # Get search IDs for this interval
            interval_search_ids = analytics.filter(
                timestamp__gte=interval_start,
                timestamp__lt=interval_end
            ).values_list('query_history', flat=True)
            
            # Get feedback for these searches
            interval_feedback = Feedback.objects.filter(
                query_history__in=interval_search_ids
            )
            
            positive_count = interval_feedback.filter(rating='thumbs_up').count()
            negative_count = interval_feedback.filter(rating='thumbs_down').count()
            total_count = positive_count + negative_count
            
            point['feedback_count'] = total_count
            point['positive_count'] = positive_count
            point['negative_count'] = negative_count
            point['feedback_rate'] = total_count / point['count'] if point['count'] > 0 else 0
            point['satisfaction_rate'] = positive_count / total_count if total_count > 0 else 0
        
        return Response(time_series)