"""
Service layer for feedback processing and analysis.
"""

import datetime
from django.utils import timezone
from django.db.models import Count, Avg, F, Q, Sum
import json
import logging

from .models import (
    EnhancedFeedback,
    FeedbackTheme,
    FeedbackAnalysis,
    FeedbackThemeMapping,
    FeedbackCategory
)
from ..models import QueryHistory, Feedback
from ..security.error_handling import SecurityError

logger = logging.getLogger(__name__)


class FeedbackService:
    """
    Service class for processing and analyzing feedback.
    Provides methods for working with feedback data.
    """
    
    @staticmethod
    def process_new_feedback(feedback):
        """
        Process a new feedback submission.
        Analyzes feedback content and triggers appropriate actions.
        
        Args:
            feedback: EnhancedFeedback instance
            
        Returns:
            dict: Processing results
        """
        results = {
            'feedback_id': feedback.id,
            'actions_performed': [],
            'themes_identified': [],
            'suggested_improvements': [],
        }
        
        try:
            # Add to relevant themes
            themes = FeedbackService._identify_themes(feedback)
            if themes:
                results['themes_identified'] = [
                    {'id': theme.id, 'title': theme.title} for theme in themes
                ]
            
            # Check for critical issues
            if feedback.rating == 'thumbs_down':
                if FeedbackService._is_critical_issue(feedback):
                    results['actions_performed'].append('flagged_as_critical')
                    # Could send notifications or other alerts here
            
            # Generate improvement suggestions
            suggestions = FeedbackService._generate_improvement_suggestions(feedback)
            if suggestions:
                results['suggested_improvements'] = suggestions
                
            return results
        except Exception as e:
            logger.error(f"Error processing feedback {feedback.id}: {str(e)}")
            return {
                'feedback_id': feedback.id,
                'error': str(e),
                'status': 'processing_failed'
            }
    
    @staticmethod
    def _identify_themes(feedback):
        """
        Identify themes relevant to this feedback.
        Uses content analysis to find matching themes.
        
        Args:
            feedback: EnhancedFeedback instance
            
        Returns:
            list: Matching FeedbackTheme instances
        """
        matching_themes = []
        
        # Get active themes
        active_themes = FeedbackTheme.objects.filter(
            status__in=['active', 'investigating', 'implementing']
        )
        
        if not active_themes:
            return []
        
        # Extract text content from feedback
        content = FeedbackService._extract_feedback_content(feedback)
        
        # Match against themes
        for theme in active_themes:
            # Skip already mapped themes
            if FeedbackThemeMapping.objects.filter(feedback=feedback, theme=theme).exists():
                continue
                
            # Basic keyword matching
            # In a real system, this would use more sophisticated NLP
            keywords = theme.title.lower().split() + theme.description.lower().split()
            keywords = [k for k in keywords if len(k) > 3]  # Skip short words
            
            matches = 0
            for keyword in keywords:
                if keyword in content:
                    matches += 1
            
            # If significant number of matches, create mapping
            if matches >= 2 or (matches > 0 and len(keywords) < 5):
                # Create mapping with relevance based on match ratio
                relevance = min(1.0, matches / max(len(keywords) * 0.5, 1))
                
                FeedbackThemeMapping.objects.create(
                    feedback=feedback,
                    theme=theme,
                    relevance_score=relevance,
                    notes=f"Automatic mapping based on content analysis"
                )
                
                # Update feedback count
                theme.feedback_count = FeedbackThemeMapping.objects.filter(theme=theme).count()
                theme.save()
                
                matching_themes.append(theme)
        
        return matching_themes
    
    @staticmethod
    def _is_critical_issue(feedback):
        """
        Determine if feedback represents a critical issue.
        
        Args:
            feedback: EnhancedFeedback instance
            
        Returns:
            bool: True if critical issue
        """
        # Critical patterns
        critical_patterns = [
            'incorrect', 'wrong', 'false', 'error', 'mistaken',
            'hallucination', 'made up', 'fabricated'
        ]
        
        # Check for critical words in comment
        if feedback.comment:
            if any(pattern in feedback.comment.lower() for pattern in critical_patterns):
                return True
        
        # Check for critical issues in specific_issues
        if feedback.specific_issues:
            if any('incorrect' in issue.lower() for issue in feedback.specific_issues):
                return True
            if any('hallucinated' in issue.lower() for issue in feedback.specific_issues):
                return True
        
        # Check for very low ratings
        if feedback.accuracy_rating == 1 or feedback.citation_rating == 1:
            return True
        
        return False
    
    @staticmethod
    def _generate_improvement_suggestions(feedback):
        """
        Generate improvement suggestions based on feedback.
        
        Args:
            feedback: EnhancedFeedback instance
            
        Returns:
            list: Improvement suggestions
        """
        suggestions = []
        
        # Check negative feedback for improvement areas
        if feedback.rating != 'thumbs_down':
            return suggestions
        
        # Check specific aspects
        if feedback.relevance_rating and feedback.relevance_rating < 3:
            suggestions.append({
                'area': 'relevance',
                'suggestion': 'Improve query understanding to provide more relevant answers',
                'priority': 'high' if feedback.relevance_rating == 1 else 'medium'
            })
        
        if feedback.accuracy_rating and feedback.accuracy_rating < 3:
            suggestions.append({
                'area': 'accuracy',
                'suggestion': 'Review source documents for this topic and improve factual accuracy',
                'priority': 'high' if feedback.accuracy_rating == 1 else 'medium'
            })
        
        if feedback.completeness_rating and feedback.completeness_rating < 3:
            suggestions.append({
                'area': 'completeness',
                'suggestion': 'Provide more comprehensive answers with all relevant details',
                'priority': 'medium'
            })
        
        if feedback.clarity_rating and feedback.clarity_rating < 3:
            suggestions.append({
                'area': 'clarity',
                'suggestion': 'Improve answer formatting and readability',
                'priority': 'medium'
            })
        
        if feedback.citation_rating and feedback.citation_rating < 3:
            suggestions.append({
                'area': 'citations',
                'suggestion': 'Improve citation accuracy and specificity',
                'priority': 'high' if feedback.citation_rating == 1 else 'medium'
            })
        
        # Check for suggested answer
        if feedback.suggested_answer:
            suggestions.append({
                'area': 'content',
                'suggestion': 'Review user-suggested answer for this query',
                'priority': 'high'
            })
        
        # Check for source quality issues
        if feedback.source_quality_issues:
            suggestions.append({
                'area': 'sources',
                'suggestion': 'Investigate source quality issues for this query',
                'priority': 'high'
            })
        
        return suggestions
    
    @staticmethod
    def _extract_feedback_content(feedback):
        """
        Extract all textual content from feedback for analysis.
        
        Args:
            feedback: EnhancedFeedback instance
            
        Returns:
            str: Combined content
        """
        content_parts = []
        
        # Add comment
        if feedback.comment:
            content_parts.append(feedback.comment.lower())
        
        # Add specific issues
        if feedback.specific_issues:
            content_parts.extend([issue.lower() for issue in feedback.specific_issues])
        
        # Add suggested answer
        if feedback.suggested_answer:
            content_parts.append(feedback.suggested_answer.lower())
        
        # Add original query and answer
        content_parts.append(feedback.query_history.query_text.lower())
        content_parts.append(feedback.query_history.answer.lower())
        
        # Combine all content
        return ' '.join(content_parts)


class FeedbackAnalysisService:
    """
    Service class for analyzing feedback trends and generating insights.
    Provides methods for aggregating and analyzing feedback data.
    """
    
    @staticmethod
    def analyze_feedback_period(start_date, end_date):
        """
        Analyze feedback for a specific period.
        Generates insights and improvement recommendations.
        
        Args:
            start_date: datetime object for period start
            end_date: datetime object for period end
            
        Returns:
            FeedbackAnalysis: The created analysis object
        """
        # Get feedback for period
        feedback = EnhancedFeedback.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        if not feedback.exists():
            raise ValueError("No feedback found in the specified date range")
        
        # Count ratings
        total_count = feedback.count()
        positive_count = feedback.filter(rating='thumbs_up').count()
        negative_count = feedback.filter(rating='thumbs_down').count()
        neutral_count = feedback.filter(rating='neutral').count()
        
        # Run analysis
        analysis_results = FeedbackAnalysisService._generate_analysis(
            feedback, start_date, end_date
        )
        
        # Create analysis record
        analysis = FeedbackAnalysis.objects.create(
            date_range_start=start_date,
            date_range_end=end_date,
            total_feedback_analyzed=total_count,
            positive_feedback_count=positive_count,
            negative_feedback_count=negative_count,
            neutral_feedback_count=neutral_count,
            **analysis_results
        )
        
        return analysis
    
    @staticmethod
    def _generate_analysis(feedback, start_date, end_date):
        """
        Generate detailed analysis of feedback data.
        
        Args:
            feedback: QuerySet of EnhancedFeedback objects
            start_date: Start of analysis period
            end_date: End of analysis period
            
        Returns:
            dict: Analysis results
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
    
    @staticmethod
    def get_daily_feedback_stats(days=30):
        """
        Get daily feedback statistics for the specified number of days.
        
        Args:
            days: Number of days to include
            
        Returns:
            list: Daily statistics
        """
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=days-1)
        
        daily_stats = []
        
        current_date = start_date
        while current_date <= end_date:
            current_datetime = datetime.datetime.combine(current_date, datetime.time.min)
            next_date = current_date + datetime.timedelta(days=1)
            next_datetime = datetime.datetime.combine(next_date, datetime.time.min)
            
            # Get feedback for the day
            day_feedback = EnhancedFeedback.objects.filter(
                created_at__gte=current_datetime,
                created_at__lt=next_datetime
            )
            
            # Count by rating
            total = day_feedback.count()
            positive = day_feedback.filter(rating='thumbs_up').count()
            negative = day_feedback.filter(rating='thumbs_down').count()
            neutral = day_feedback.filter(rating='neutral').count()
            
            # Add to results
            daily_stats.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'total': total,
                'positive': positive,
                'negative': negative,
                'neutral': neutral,
                'positive_ratio': (positive / total * 100) if total > 0 else 0
            })
            
            current_date = next_date
        
        return daily_stats