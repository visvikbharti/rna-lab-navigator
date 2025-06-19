"""
Celery tasks for automated paper monitoring
"""

from celery import shared_task
from .models import MonitoredPaper
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_new_papers():
    """
    Celery task to check for new papers periodically.
    Should be run every 6 hours via Celery Beat.
    """
    try:
        from .auto_ingest import PaperMonitor
        
        logger.info("Starting automated paper check...")
        monitor = PaperMonitor()
        
        # Fetch papers from last 24 hours
        papers = monitor.fetch_recent_papers(hours=24)
        logger.info(f"Found {len(papers)} papers to process")
        
        # Process and categorize
        categorized = monitor.process_papers(papers)
        
        # Save to database
        saved_count = 0
        duplicate_count = 0
        
        for category, papers_list in categorized.items():
            if category != 'total_processed':
                for paper_data in papers_list:
                    # Skip if DOI already exists
                    if paper_data.get('doi') and MonitoredPaper.objects.filter(doi=paper_data['doi']).exists():
                        duplicate_count += 1
                        continue
                    
                    # Check by title if no DOI
                    if MonitoredPaper.objects.filter(title=paper_data['title']).exists():
                        duplicate_count += 1
                        continue
                    
                    # Create new paper record
                    MonitoredPaper.objects.create(
                        title=paper_data['title'],
                        authors=paper_data['authors'],
                        abstract=paper_data['abstract'],
                        doi=paper_data.get('doi'),
                        url=paper_data['link'],
                        source=paper_data['source'],
                        category=paper_data['category'],
                        published_date=paper_data['published'],
                        relevance_score=paper_data['relevance_score'],
                        relevance_category=category,
                        relevance_reasons=paper_data['relevance_reasons'],
                        smart_summary=paper_data.get('summary', '')
                    )
                    saved_count += 1
        
        # Send notifications if urgent papers found
        if categorized.get('urgent'):
            monitor.send_notifications(categorized)
            
            # Mark as notified
            MonitoredPaper.objects.filter(
                relevance_category='urgent',
                is_notified=False
            ).update(is_notified=True)
        
        logger.info(f"Paper check complete: {saved_count} new, {duplicate_count} duplicates")
        
        return {
            'success': True,
            'processed': categorized['total_processed'],
            'saved': saved_count,
            'duplicates': duplicate_count,
            'urgent': len(categorized.get('urgent', [])),
            'relevant': len(categorized.get('relevant', []))
        }
        
    except Exception as e:
        logger.error(f"Error in paper check task: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def generate_weekly_digest():
    """
    Generate weekly digest of important papers.
    Should be run every Monday at 9 AM via Celery Beat.
    """
    try:
        from .auto_ingest import PaperMonitor
        from datetime import datetime, timedelta
        
        logger.info("Generating weekly paper digest...")
        monitor = PaperMonitor()
        
        # Get papers from last week
        week_ago = datetime.now() - timedelta(days=7)
        
        # Get top papers by category
        urgent = MonitoredPaper.objects.filter(
            discovered_date__gte=week_ago,
            relevance_category='urgent'
        ).order_by('-relevance_score')[:10]
        
        relevant = MonitoredPaper.objects.filter(
            discovered_date__gte=week_ago,
            relevance_category='relevant'
        ).order_by('-relevance_score')[:20]
        
        if urgent.exists() or relevant.exists():
            categorized = {
                'urgent': list(urgent.values()),
                'relevant': list(relevant.values()),
                'total_processed': urgent.count() + relevant.count()
            }
            
            # Send digest email
            monitor.send_notifications(categorized)
            
            logger.info(f"Weekly digest sent: {urgent.count()} urgent, {relevant.count()} relevant papers")
            
            return {
                'success': True,
                'urgent_count': urgent.count(),
                'relevant_count': relevant.count()
            }
        else:
            logger.info("No papers to include in weekly digest")
            return {
                'success': True,
                'message': 'No papers found for digest'
            }
            
    except Exception as e:
        logger.error(f"Error generating weekly digest: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def analyze_paper_trends():
    """
    Analyze trending topics and keywords from recent papers.
    Updates the dashboard with insights.
    """
    try:
        from collections import Counter
        from datetime import datetime, timedelta
        import re
        
        logger.info("Analyzing paper trends...")
        
        # Get papers from last 30 days
        month_ago = datetime.now() - timedelta(days=30)
        recent_papers = MonitoredPaper.objects.filter(
            discovered_date__gte=month_ago
        )
        
        # Extract keywords from titles and abstracts
        all_text = ' '.join([
            f"{paper.title} {paper.abstract}"
            for paper in recent_papers
        ])
        
        # Simple keyword extraction (in production, use NLP)
        words = re.findall(r'\b[A-Z][a-z]+\b', all_text)
        
        # Filter common words and count
        stop_words = {'The', 'This', 'That', 'These', 'Those', 'And', 'But', 'For', 'With'}
        keywords = [w for w in words if w not in stop_words and len(w) > 4]
        
        # Get top 20 trending terms
        trending = Counter(keywords).most_common(20)
        
        logger.info(f"Found trending topics: {trending[:5]}")
        
        return {
            'success': True,
            'trending_topics': trending,
            'papers_analyzed': recent_papers.count()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing trends: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def ingest_flagged_papers():
    """
    Automatically ingest papers that have been flagged by multiple users.
    """
    try:
        logger.info("Checking for flagged papers to ingest...")
        
        # Get papers flagged by 2+ users that haven't been ingested
        flagged_papers = MonitoredPaper.objects.filter(
            is_ingested=False
        ).exclude(flagged_by=[])
        
        ingested_count = 0
        
        for paper in flagged_papers:
            if len(paper.flagged_by) >= 2:
                # TODO: Implement actual ingestion logic
                # For now, just mark as ingested
                paper.is_ingested = True
                paper.save()
                ingested_count += 1
                
                logger.info(f"Ingested paper: {paper.title}")
        
        logger.info(f"Ingested {ingested_count} flagged papers")
        
        return {
            'success': True,
            'ingested_count': ingested_count
        }
        
    except Exception as e:
        logger.error(f"Error ingesting flagged papers: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }