"""
Celery tasks for the RNA Lab Navigator.
"""

import requests
import json
from celery import shared_task
from datetime import datetime, timedelta
import time
import re
from django.conf import settings
from django.core.mail import send_mail

from api.models import Document, EvaluationSet, EvaluationRun
from api.ingestion.chunking_utils import chunk_text
from api.ingestion.embeddings_utils import (
    create_schema_if_not_exists,
    add_document_chunk_to_weaviate
)
from api.evaluation.evaluation_utils import (
    run_evaluation,
    compare_runs,
    generate_evaluation_report
)


@shared_task(name="fetch_biorxiv_preprints")
def fetch_biorxiv_preprints():
    """
    Fetch the latest RNA-biology related preprints from bioRxiv.
    Runs daily at 2 AM (configured in settings.py).
    """
    # Keywords to search for
    rna_keywords = [
        "RNA biology", "RNA editing", "RNA splicing", "RNA processing",
        "CRISPR", "Cas13", "RNA therapeutics"
    ]
    
    # Ensure Weaviate schema exists
    create_schema_if_not_exists()
    
    # Calculate date range (previous day)
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    
    total_papers = 0
    
    # Try each keyword
    for keyword in rna_keywords:
        try:
            # bioRxiv API endpoint for search
            url = "https://api.biorxiv.org/details/biorxiv/2022-01-01/2025-01-01/0"
            # Note: In a real implementation, use the date_str for the date range
            # This is a placeholder as the actual API might differ
            
            response = requests.get(url, params={"term": keyword}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Extract papers - schema will depend on actual API
                papers = data.get("collection", [])
                
                for paper in papers:
                    # Extract details
                    title = paper.get("title", "")
                    abstract = paper.get("abstract", "")
                    authors = paper.get("authors", "")
                    doi = paper.get("doi", "")
                    date = paper.get("date", "")
                    
                    # Skip if no abstract
                    if not abstract:
                        continue
                    
                    # Create db record
                    try:
                        year = int(date.split("-")[0]) if "-" in date else None
                        doc = Document.objects.create(
                            title=title,
                            doc_type="paper",
                            author=authors.split(",")[0] if authors else "",  # First author
                            year=year
                        )
                    except Exception as e:
                        print(f"Error creating Document record: {e}")
                        continue
                    
                    # Combine title and abstract for better context
                    full_text = f"Title: {title}\n\nAbstract: {abstract}"
                    
                    # Chunk the text
                    chunks = chunk_text(full_text)
                    
                    # Add each chunk to Weaviate
                    for i, chunk in enumerate(chunks):
                        metadata = {
                            "doc_type": "paper",
                            "title": title,
                            "author": authors.split(",")[0] if authors else "",
                            "year": year,
                            "source": f"bioRxiv: {doi}"
                        }
                        
                        # Add to Weaviate
                        add_document_chunk_to_weaviate(chunk, metadata)
                        
                        # Rate limiting to avoid API rate limits
                        if i > 0 and i % 5 == 0:
                            time.sleep(1)
                    
                    total_papers += 1
            
            # Sleep to avoid hitting rate limits
            time.sleep(1)
        
        except Exception as e:
            print(f"Error fetching papers for keyword '{keyword}': {e}")
            continue
    
    return f"Fetched and processed {total_papers} new preprints."


@shared_task(name="run_weekly_evaluation")
def run_weekly_evaluation():
    """
    Weekly evaluation of the RAG system against reference questions.
    Runs every Sunday at 3 AM.
    """
    # Find active evaluation sets
    active_sets = EvaluationSet.objects.filter(is_active=True)
    
    if not active_sets.exists():
        return "No active evaluation sets found."
    
    results = []
    
    # Run evaluations for each active set
    for eval_set in active_sets:
        try:
            # Run the evaluation
            evaluation_run = run_evaluation(eval_set.id, use_hybrid=True, use_cache=False)
            
            # Compare with previous run
            comparison = compare_runs(evaluation_run.id)
            
            # Generate detailed report
            report = generate_evaluation_report(evaluation_run.id)
            
            results.append({
                "set_name": eval_set.name,
                "run_id": evaluation_run.id,
                "success_rate": f"{evaluation_run.success_count / evaluation_run.total_questions * 100:.2f}%",
                "regression_detected": comparison.get("regression_detected", False)
            })
            
            # Send alert email if regression detected
            if comparison.get("regression_detected", False) and hasattr(settings, 'EMAIL_ALERTS_ENABLED') and settings.EMAIL_ALERTS_ENABLED:
                send_evaluation_alert(report, comparison)
                
        except Exception as e:
            print(f"Error running evaluation for set '{eval_set.name}': {e}")
            results.append({
                "set_name": eval_set.name,
                "error": str(e)
            })
    
    return f"Weekly evaluation completed: {json.dumps(results)}"


def send_evaluation_alert(report, comparison):
    """
    Send an email alert when a regression is detected in the system.
    
    Args:
        report (dict): Evaluation report data
        comparison (dict): Comparison with previous run
    """
    try:
        # Subject with alert indicator
        subject = f"⚠️ ALERT: RNA Lab Navigator performance regression detected"
        
        # Format the email body
        body = f"""
PERFORMANCE REGRESSION DETECTED

Evaluation Set: {report['set_name']}
Run Date: {report['run_date']}

CHANGES:
- Confidence Score: {comparison['changes']['score_change']:.2f}%
- Retrieval Precision: {comparison['changes']['precision_change']:.2f}%
- Answer Relevance: {comparison['changes']['relevance_change']:.2f}%
- Success Rate: {comparison['changes']['success_rate_change']:.2f}%

DETAILS:
- Current Success Rate: {report['summary']['success_rate'] * 100:.2f}%
- Total Questions: {report['summary']['total_questions']}
- Successful Answers: {report['summary']['success_count']}
- Failed Answers: {report['summary']['failure_count']}

WORST PERFORMING QUESTIONS:
{chr(10).join([f"- {item['question'][:100]}..." for item in report['worst_performers']])}

Please review the system as soon as possible.
Full report available at: http://rna-navigator-admin/evaluations/{report['run_id']}
        """
        
        # Send the email
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=settings.ADMIN_EMAILS,
            fail_silently=False,
        )
        
    except Exception as e:
        print(f"Error sending evaluation alert email: {e}")


@shared_task(name="cleanup_old_cache_entries")
def cleanup_old_cache_entries():
    """
    Clean up old cache entries to prevent database bloat.
    Removes entries that haven't been accessed in 30+ days.
    Runs weekly.
    """
    from api.models import QueryCache
    from django.utils import timezone
    
    # Calculate cutoff date (30 days ago)
    cutoff_date = timezone.now() - timezone.timedelta(days=30)
    
    # Delete old entries
    old_entries = QueryCache.objects.filter(last_accessed__lt=cutoff_date)
    count = old_entries.count()
    old_entries.delete()
    
    return f"Cleaned up {count} old cache entries."