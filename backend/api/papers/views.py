"""
Views for paper monitoring and management
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import MonitoredPaper, PaperKeyword
# Import will be done inside functions to avoid startup errors
# from .auto_ingest import PaperMonitor
import asyncio


@api_view(['GET'])
def paper_dashboard(request):
    """Get overview of monitored papers."""
    
    # Get counts by category
    urgent_count = MonitoredPaper.objects.filter(
        relevance_category='urgent', 
        is_notified=False
    ).count()
    
    relevant_count = MonitoredPaper.objects.filter(
        relevance_category='relevant',
        is_notified=False
    ).count()
    
    # Get recent papers
    recent_papers = MonitoredPaper.objects.order_by('-published_date')[:10]
    
    # Get trending topics (most common keywords in recent papers)
    trending_topics = []  # TODO: Implement keyword extraction
    
    return Response({
        'stats': {
            'urgent_papers': urgent_count,
            'relevant_papers': relevant_count,
            'total_monitored': MonitoredPaper.objects.count(),
            'papers_ingested': MonitoredPaper.objects.filter(is_ingested=True).count()
        },
        'recent_papers': [
            {
                'id': str(paper.id),
                'title': paper.title,
                'authors': paper.authors,
                'published_date': paper.published_date,
                'relevance_category': paper.relevance_category,
                'relevance_score': paper.relevance_score,
                'url': paper.url,
                'smart_summary': paper.smart_summary[:200] + '...' if paper.smart_summary else None
            }
            for paper in recent_papers
        ],
        'trending_topics': trending_topics
    })


@api_view(['GET'])
def get_papers(request):
    """Get papers with filtering options."""
    
    category = request.GET.get('category', 'all')
    limit = int(request.GET.get('limit', 20))
    offset = int(request.GET.get('offset', 0))
    
    # Base queryset
    papers = MonitoredPaper.objects.all()
    
    # Filter by category
    if category != 'all':
        papers = papers.filter(relevance_category=category)
    
    # Filter by notification status
    if request.GET.get('unnotified_only') == 'true':
        papers = papers.filter(is_notified=False)
    
    # Order by relevance and date
    papers = papers.order_by('-relevance_score', '-published_date')
    
    # Paginate
    total = papers.count()
    papers = papers[offset:offset + limit]
    
    return Response({
        'total': total,
        'papers': [
            {
                'id': str(paper.id),
                'title': paper.title,
                'authors': paper.authors,
                'abstract': paper.abstract[:300] + '...',
                'published_date': paper.published_date,
                'source': paper.source,
                'category': paper.category,
                'relevance_category': paper.relevance_category,
                'relevance_score': paper.relevance_score,
                'relevance_reasons': paper.relevance_reasons,
                'smart_summary': paper.smart_summary,
                'experiment_suggestions': paper.experiment_suggestions,
                'url': paper.url,
                'is_ingested': paper.is_ingested,
                'clicked_count': paper.clicked_count
            }
            for paper in papers
        ]
    })


@api_view(['GET', 'POST'])
def paper_detail(request, paper_id):
    """Get or update paper details."""
    
    paper = get_object_or_404(MonitoredPaper, id=paper_id)
    
    if request.method == 'GET':
        # Increment click count
        paper.increment_click()
        
        return Response({
            'paper': {
                'id': str(paper.id),
                'title': paper.title,
                'authors': paper.authors,
                'abstract': paper.abstract,
                'doi': paper.doi,
                'url': paper.url,
                'published_date': paper.published_date,
                'discovered_date': paper.discovered_date,
                'source': paper.source,
                'category': paper.category,
                'relevance_category': paper.relevance_category,
                'relevance_score': paper.relevance_score,
                'relevance_reasons': paper.relevance_reasons,
                'smart_summary': paper.smart_summary,
                'experiment_suggestions': paper.experiment_suggestions,
                'key_findings': paper.key_findings,
                'is_ingested': paper.is_ingested,
                'clicked_count': paper.clicked_count,
                'notes': paper.notes
            }
        })
    
    elif request.method == 'POST':
        # Update paper (mark for ingestion, add notes, etc.)
        if 'mark_for_ingestion' in request.data:
            paper.is_ingested = True
            paper.save()
            
        if 'notes' in request.data:
            paper.notes = request.data['notes']
            paper.save()
            
        if 'flag' in request.data:
            user_id = request.data.get('user_id', 'anonymous')
            if user_id not in paper.flagged_by:
                paper.flagged_by.append(user_id)
                paper.save()
        
        return Response({'success': True})


@api_view(['POST'])
def check_papers_now(request):
    """Manually trigger paper checking."""
    
    try:
        from .auto_ingest import PaperMonitor
        monitor = PaperMonitor()
        
        # Fetch papers from last N hours
        hours = int(request.data.get('hours', 24))
        papers = monitor.fetch_recent_papers(hours=hours)
        
        # Process and categorize
        categorized = monitor.process_papers(papers)
        
        # Save to database
        saved_count = 0
        for category, papers_list in categorized.items():
            if category != 'total_processed':
                for paper_data in papers_list:
                    # Check if paper already exists
                    if not MonitoredPaper.objects.filter(doi=paper_data.get('doi')).exists():
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
        
        return Response({
            'success': True,
            'processed': categorized['total_processed'],
            'saved': saved_count,
            'urgent': len(categorized.get('urgent', [])),
            'relevant': len(categorized.get('relevant', [])),
            'monitoring': len(categorized.get('monitoring', []))
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET', 'POST', 'DELETE'])
def manage_keywords(request):
    """Manage monitoring keywords."""
    
    if request.method == 'GET':
        keywords = PaperKeyword.objects.filter(is_active=True)
        return Response({
            'keywords': [
                {
                    'id': k.id,
                    'keyword': k.keyword,
                    'priority': k.priority,
                    'score_boost': k.score_boost,
                    'created_by': k.created_by,
                    'created_at': k.created_at
                }
                for k in keywords
            ]
        })
    
    elif request.method == 'POST':
        # Add new keyword
        keyword = PaperKeyword.objects.create(
            keyword=request.data['keyword'],
            priority=request.data.get('priority', 'medium'),
            score_boost=request.data.get('score_boost', 10),
            created_by=request.data.get('created_by', 'system')
        )
        return Response({
            'success': True,
            'keyword': {
                'id': keyword.id,
                'keyword': keyword.keyword,
                'priority': keyword.priority
            }
        })
    
    elif request.method == 'DELETE':
        # Deactivate keyword
        keyword_id = request.data.get('id')
        keyword = get_object_or_404(PaperKeyword, id=keyword_id)
        keyword.is_active = False
        keyword.save()
        return Response({'success': True})


@api_view(['POST'])
def generate_digest(request):
    """Generate and preview digest email."""
    
    from .auto_ingest import PaperMonitor
    monitor = PaperMonitor()
    
    # Get unnotified papers
    urgent = MonitoredPaper.objects.filter(
        relevance_category='urgent',
        is_notified=False
    )[:5]
    
    relevant = MonitoredPaper.objects.filter(
        relevance_category='relevant', 
        is_notified=False
    )[:10]
    
    # Generate digest HTML
    categorized = {
        'urgent': list(urgent.values()),
        'relevant': list(relevant.values()),
        'total_processed': urgent.count() + relevant.count()
    }
    
    digest_html = monitor.format_email_digest(categorized)
    
    # Option to send
    if request.data.get('send', False):
        # Send email
        monitor.send_notifications(categorized)
        
        # Mark as notified
        urgent.update(is_notified=True)
        relevant.update(is_notified=True)
        
        return Response({
            'success': True,
            'sent': True,
            'preview': digest_html
        })
    
    return Response({
        'success': True,
        'sent': False,
        'preview': digest_html
    })


@api_view(['GET'])
def paper_stats(request):
    """Get statistics about paper monitoring."""
    
    from django.db.models import Count, Avg
    from datetime import datetime, timedelta
    
    # Papers per day for last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    daily_counts = MonitoredPaper.objects.filter(
        discovered_date__gte=thirty_days_ago
    ).extra(
        select={'day': 'date(discovered_date)'}
    ).values('day').annotate(count=Count('id'))
    
    # Category distribution
    category_dist = MonitoredPaper.objects.values(
        'relevance_category'
    ).annotate(count=Count('id'))
    
    # Source distribution
    source_dist = MonitoredPaper.objects.values(
        'source'
    ).annotate(count=Count('id'))
    
    # Engagement metrics
    avg_clicks = MonitoredPaper.objects.aggregate(
        avg_clicks=Avg('clicked_count')
    )
    
    return Response({
        'daily_counts': list(daily_counts),
        'category_distribution': list(category_dist),
        'source_distribution': list(source_dist),
        'engagement': {
            'average_clicks_per_paper': avg_clicks['avg_clicks'],
            'total_papers_viewed': MonitoredPaper.objects.filter(
                clicked_count__gt=0
            ).count(),
            'papers_ingested': MonitoredPaper.objects.filter(
                is_ingested=True
            ).count()
        }
    })