"""
Management command to analyze feedback and generate insights.
"""

import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Count, Avg, Q, F

from api.feedback.models import (
    EnhancedFeedback,
    FeedbackTheme,
    FeedbackAnalysis
)
from api.models import QueryHistory


class Command(BaseCommand):
    help = "Analyze feedback and generate improvement recommendations"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of feedback to analyze'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Analyze all historical feedback (overrides --days)'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date for analysis (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for analysis (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format'
        )
        parser.add_argument(
            '--save',
            action='store_true',
            help='Save the analysis to the database'
        )
    
    def handle(self, *args, **options):
        # Determine date range
        end_date = timezone.now()
        
        if options['start_date'] and options['end_date']:
            try:
                start_date = datetime.datetime.strptime(options['start_date'], '%Y-%m-%d')
                end_date = datetime.datetime.strptime(options['end_date'], '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise CommandError("Invalid date format. Use YYYY-MM-DD.")
        elif options['all']:
            # Use the earliest feedback as start date
            first_feedback = EnhancedFeedback.objects.order_by('created_at').first()
            if first_feedback:
                start_date = first_feedback.created_at
            else:
                self.stdout.write(self.style.WARNING("No feedback found. Nothing to analyze."))
                return
        else:
            days = options['days']
            start_date = end_date - datetime.timedelta(days=days)
        
        # Get feedback for analysis
        feedback = EnhancedFeedback.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        if not feedback.exists():
            self.stdout.write(self.style.WARNING("No feedback found in the specified date range."))
            return
        
        # Output the date range being analyzed
        self.stdout.write(self.style.SUCCESS(
            f"Analyzing feedback from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        ))
        self.stdout.write(f"Total feedback items: {feedback.count()}")
        
        # Run the analysis
        results = self._analyze_feedback(feedback, start_date, end_date)
        
        # Save the analysis if requested
        if options['save']:
            analysis = FeedbackAnalysis.objects.create(
                date_range_start=start_date,
                date_range_end=end_date,
                total_feedback_analyzed=feedback.count(),
                positive_feedback_count=feedback.filter(rating='thumbs_up').count(),
                negative_feedback_count=feedback.filter(rating='thumbs_down').count(),
                neutral_feedback_count=feedback.filter(rating='neutral').count(),
                **results
            )
            self.stdout.write(self.style.SUCCESS(
                f"Analysis saved with ID: {analysis.analysis_id}"
            ))
        
        # Output results based on format
        if options['format'] == 'json':
            import json
            self.stdout.write(json.dumps(results, indent=2))
        else:
            self._output_text_report(results, feedback)
    
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
    
    def _output_text_report(self, results, feedback):
        """Output the analysis results in text format"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write(" FEEDBACK ANALYSIS REPORT ")
        self.stdout.write("="*50 + "\n")
        
        # Rating breakdown
        positive_count = feedback.filter(rating='thumbs_up').count()
        negative_count = feedback.filter(rating='thumbs_down').count()
        neutral_count = feedback.filter(rating='neutral').count()
        total_count = feedback.count()
        
        self.stdout.write("RATING BREAKDOWN:")
        self.stdout.write(f"Positive: {positive_count} ({positive_count/total_count*100:.1f}%)")
        self.stdout.write(f"Negative: {negative_count} ({negative_count/total_count*100:.1f}%)")
        self.stdout.write(f"Neutral: {neutral_count} ({neutral_count/total_count*100:.1f}%)")
        self.stdout.write("\n")
        
        # Top Issues
        self.stdout.write("TOP REPORTED ISSUES:")
        if results['top_issues']:
            for issue in results['top_issues']:
                self.stdout.write(f"- {issue['issue']} ({issue['count']} occurrences)")
        else:
            self.stdout.write("- No specific issues reported")
        self.stdout.write("\n")
        
        # Category Distribution
        self.stdout.write("FEEDBACK BY CATEGORY:")
        if results['category_distribution']:
            for category, count in results['category_distribution'].items():
                category_name = category if category else 'Uncategorized'
                self.stdout.write(f"- {category_name}: {count} items")
        else:
            self.stdout.write("- No category data available")
        self.stdout.write("\n")
        
        # Improvement Opportunities
        self.stdout.write("IMPROVEMENT OPPORTUNITIES:")
        if results['improvement_opportunities']:
            for opportunity in results['improvement_opportunities']:
                self.stdout.write(
                    f"- {opportunity['area']} ({opportunity['priority']} priority): "
                    f"{opportunity['description']} ({opportunity['feedback_count']} feedback items)"
                )
        else:
            self.stdout.write("- No specific improvement opportunities identified")
        self.stdout.write("\n")
        
        # Trend Analysis
        self.stdout.write("TREND ANALYSIS:")
        trend = results['trend_analysis']
        first = trend['first_period']
        second = trend['second_period']
        changes = trend['changes']
        
        self.stdout.write(
            f"First period ({first['start']} to {first['end']}): "
            f"{first['positive_percentage']:.1f}% positive ({first['total_feedback']} items)"
        )
        self.stdout.write(
            f"Second period ({second['start']} to {second['end']}): "
            f"{second['positive_percentage']:.1f}% positive ({second['total_feedback']} items)"
        )
        
        direction = "improved" if changes['rating_change'] > 0 else "declined"
        self.stdout.write(
            f"Change: {abs(changes['rating_change']):.1f}% {direction}"
        )
        self.stdout.write("\n")
        
        # Recommendations
        self.stdout.write("RECOMMENDED ACTIONS:")
        if results['recommended_actions']:
            for action in results['recommended_actions']:
                self.stdout.write(
                    f"- {action['priority'].upper()}: {action['action']} - {action['description']}"
                )
        else:
            self.stdout.write("- No specific actions recommended")
        self.stdout.write("\n")
        
        # Priority Areas
        self.stdout.write("PRIORITY AREAS:")
        if results['priority_areas']:
            for area in results['priority_areas']:
                self.stdout.write(
                    f"- {area['priority'].upper()}: {area['area']} - {area['reason']}"
                )
        else:
            self.stdout.write("- No specific priority areas identified")
        
        self.stdout.write("\n" + "="*50)