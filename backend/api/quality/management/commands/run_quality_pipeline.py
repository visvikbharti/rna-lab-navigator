"""
Management command to run the complete quality improvement pipeline.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from api.quality.services import QualityImprovementService


class Command(BaseCommand):
    help = 'Runs the complete quality improvement pipeline'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analysis-type',
            type=str,
            default='general',
            help='Type of analysis to perform',
        )
        parser.add_argument(
            '--days-lookback',
            type=int,
            default=30,
            help='Number of days of feedback to analyze',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (no changes will be applied)',
        )

    def handle(self, *args, **options):
        analysis_type = options['analysis_type']
        days_lookback = options['days_lookback']
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.NOTICE(f"Starting quality improvement pipeline...")
        )
        self.stdout.write(
            self.style.NOTICE(f"Analysis type: {analysis_type}")
        )
        self.stdout.write(
            self.style.NOTICE(f"Days lookback: {days_lookback}")
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be applied")
            )
        
        try:
            service = QualityImprovementService()
            
            # Get metrics before running pipeline
            metrics_before = service.get_quality_metrics(days=days_lookback)
            self.stdout.write(
                self.style.SUCCESS(f"Current quality score: {metrics_before.get('quality_score', 'N/A')}")
            )
            
            if dry_run:
                # In dry-run mode, just generate the analysis but don't implement
                analysis = service.generate_quality_analysis(
                    name=f"Dry Run Analysis - {timezone.now().strftime('%Y-%m-%d')}",
                    analysis_type=analysis_type,
                    days_lookback=days_lookback
                )
                analysis = service.run_quality_analysis(analysis.analysis_id)
                
                # Show recommendations
                recommendations = analysis.improvement_recommendations.all()
                
                self.stdout.write(
                    self.style.SUCCESS(f"Generated {recommendations.count()} improvement recommendations:")
                )
                for i, rec in enumerate(recommendations, 1):
                    self.stdout.write(
                        f"{i}. [{rec.improvement_type}] {rec.title} ({rec.priority})"
                    )
                
                self.stdout.write(
                    self.style.SUCCESS("Dry run completed. No changes applied.")
                )
            else:
                # Run the full pipeline
                results = service.run_quality_improvement_pipeline()
                
                # Display results
                self.stdout.write(
                    self.style.SUCCESS(f"Quality analysis completed: {results.get('analysis').name}")
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Generated {len(results.get('recommendations', []))} recommendations")
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Auto-approved {len(results.get('approved', []))} improvements")
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Implemented {len(results.get('implemented', []))} improvements")
                )
                
                # Get metrics after running pipeline
                metrics_after = service.get_quality_metrics(days=days_lookback)
                
                if 'quality_score' in metrics_before and 'quality_score' in metrics_after:
                    score_before = metrics_before['quality_score']
                    score_after = metrics_after['quality_score']
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"Quality score changed from {score_before:.2f} to {score_after:.2f}")
                    )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error running quality pipeline: {str(e)}")
            )
            raise