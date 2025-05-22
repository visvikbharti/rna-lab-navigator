from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from .services import QuerySuggestionService, SearchService
from .models import QuerySuggestion

logger = logging.getLogger(__name__)

@shared_task
def update_query_suggestion_metrics():
    """
    Update metrics for query suggestions based on recent usage.
    This task should run periodically to ensure metrics like success_rate
    and popularity scores are kept up to date.
    """
    try:
        service = QuerySuggestionService()
        updated_count = service.update_all_metrics()
        logger.info(f"Updated metrics for {updated_count} query suggestions")
        return updated_count
    except Exception as e:
        logger.error(f"Error updating query suggestion metrics: {str(e)}")
        raise


@shared_task
def generate_trending_suggestions(days=7, min_count=3):
    """
    Generate trending query suggestions from recent search history.
    
    Args:
        days: Number of days to look back for trending queries
        min_count: Minimum query count to be considered trending
    """
    try:
        service = QuerySuggestionService()
        new_suggestions = service.generate_trending_suggestions(
            days=days,
            min_count=min_count
        )
        logger.info(f"Generated {len(new_suggestions)} trending query suggestions")
        return len(new_suggestions)
    except Exception as e:
        logger.error(f"Error generating trending suggestions: {str(e)}")
        raise


@shared_task
def cleanup_old_suggestions(days=90):
    """
    Remove old, unused query suggestions to keep the database clean.
    
    Args:
        days: Remove suggestions not used in this many days
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Don't delete curated suggestions
        deleted, _ = QuerySuggestion.objects.filter(
            is_curated=False,
            last_used__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted} old query suggestions")
        return deleted
    except Exception as e:
        logger.error(f"Error cleaning up old suggestions: {str(e)}")
        raise


@shared_task
def update_search_analytics_aggregates():
    """
    Update aggregated search analytics for reporting and performance monitoring.
    """
    try:
        service = SearchService()
        updated = service.update_analytics_aggregates()
        logger.info(f"Updated search analytics aggregates: {updated} records")
        return updated
    except Exception as e:
        logger.error(f"Error updating search analytics aggregates: {str(e)}")
        raise