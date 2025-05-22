"""
Management command to import legacy feedback into the enhanced system.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from api.models import Feedback
from api.feedback.models import EnhancedFeedback


class Command(BaseCommand):
    help = "Import existing feedback into the enhanced feedback system"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the import without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of items to import'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options.get('limit')
        
        # Get legacy feedback
        queryset = Feedback.objects.all().order_by('-created_at')
        if limit:
            queryset = queryset[:limit]
        
        count = queryset.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING("No legacy feedback found to import."))
            return
        
        self.stdout.write(f"Found {count} legacy feedback items to import.")
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry run completed. No changes made."))
            return
        
        # Import feedback
        with transaction.atomic():
            imported_count = 0
            skipped_count = 0
            
            for legacy in queryset:
                # Check if already imported
                if EnhancedFeedback.objects.filter(query_history=legacy.query_history).exists():
                    skipped_count += 1
                    continue
                
                # Determine category based on specific issues
                category = 'general'
                if legacy.specific_issues:
                    if any('incorrect' in issue.lower() for issue in legacy.specific_issues):
                        category = 'accuracy'
                    elif any('citation' in issue.lower() for issue in legacy.specific_issues):
                        category = 'citations'
                    elif any('missing' in issue.lower() for issue in legacy.specific_issues):
                        category = 'completeness'
                    elif any('verbose' in issue.lower() or 'brief' in issue.lower() for issue in legacy.specific_issues):
                        category = 'clarity'
                
                # Map ratings
                enhanced = EnhancedFeedback(
                    query_history=legacy.query_history,
                    rating=legacy.rating,
                    comment=legacy.comment,
                    specific_issues=legacy.specific_issues,
                    category=category,
                    status='reviewed',  # Mark as reviewed since it's historical
                    created_at=legacy.created_at,
                    # Map detailed ratings if available
                    retrieval_quality=legacy.retrieval_quality,
                    accuracy_rating=legacy.citation_accuracy,  # Approximation
                    citation_rating=legacy.citation_accuracy,
                    relevance_rating=legacy.answer_relevance,
                    # Set review timestamp
                    reviewed_at=timezone.now()
                )
                
                enhanced.save()
                imported_count += 1
                
                if imported_count % 100 == 0:
                    self.stdout.write(f"Imported {imported_count} items...")
        
        self.stdout.write(self.style.SUCCESS(
            f"Import completed. {imported_count} items imported, {skipped_count} skipped."
        ))