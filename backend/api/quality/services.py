"""
Services for the answer quality improvement pipeline.

This includes services for analyzing feedback, generating
improvement recommendations, and implementing improvements.
"""

import logging
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Q, F, FloatField
from django.db.models.functions import TruncDate
from typing import Dict, List, Optional, Tuple, Any

from ..models import QueryHistory
from ..feedback.models import EnhancedFeedback, FeedbackTheme
from ..feedback.services import FeedbackAnalysisService
from .models import (
    QualityAnalysis, 
    QualityImprovement,
    ImprovedPrompt,
    RetrievalConfiguration
)

logger = logging.getLogger(__name__)


class QualityImprovementService:
    """
    Service class for analyzing feedback and generating quality improvements.
    
    This service handles the complete pipeline for improving answer quality
    based on user feedback, including:
    
    1. Analyzing feedback patterns to identify issues
    2. Generating improvement recommendations
    3. Implementing approved improvements
    4. Tracking improvement effectiveness
    5. Continuous optimization of prompts and retrieval
    """
    
    def __init__(self):
        """Initialize the quality improvement service."""
        self.feedback_service = FeedbackAnalysisService()
    
    def generate_quality_analysis(
        self, 
        name: str, 
        analysis_type: str = 'general',
        days_lookback: int = 30,
        filters: Dict = None
    ) -> QualityAnalysis:
        """
        Generate a new quality analysis based on recent feedback.
        
        Args:
            name: Name for the analysis
            analysis_type: Type of analysis to perform
            days_lookback: Number of days of feedback to analyze
            filters: Additional filters to apply to feedback selection
            
        Returns:
            A QualityAnalysis object (may be in pending state)
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_lookback)
        
        # Create analysis record
        analysis = QualityAnalysis.objects.create(
            name=name,
            analysis_type=analysis_type,
            description=f"Analysis of feedback from {start_date.date()} to {end_date.date()}",
            date_range_start=start_date,
            date_range_end=end_date,
            feedback_filter=filters
        )
        
        return analysis
    
    def run_quality_analysis(self, analysis_id: str) -> QualityAnalysis:
        """
        Run a pending quality analysis.
        
        Args:
            analysis_id: ID of the analysis to run
            
        Returns:
            The updated QualityAnalysis with results
        """
        try:
            analysis = QualityAnalysis.objects.get(analysis_id=analysis_id)
            
            # Mark as in progress
            analysis.start_analysis()
            
            # Get feedback for analysis
            feedback_query = EnhancedFeedback.objects.filter(
                created_at__gte=analysis.date_range_start,
                created_at__lte=analysis.date_range_end
            )
            
            # Apply additional filters if specified
            if analysis.feedback_filter:
                # Process each filter condition
                for key, value in analysis.feedback_filter.items():
                    if key == 'rating':
                        feedback_query = feedback_query.filter(rating=value)
                    elif key == 'category':
                        feedback_query = feedback_query.filter(category=value)
                    elif key == 'min_relevance_rating':
                        feedback_query = feedback_query.filter(relevance_rating__gte=value)
                    # Add more filter conditions as needed
            
            feedback_count = feedback_query.count()
            if feedback_count == 0:
                analysis.complete_analysis(
                    {'feedback_count': 0}, 
                    "No feedback data available for the specified period and filters."
                )
                return analysis
            
            # Initialize result containers
            identified_issues = []
            issue_frequencies = {}
            topic_clusters = {}
            
            # Process based on analysis type
            if analysis.analysis_type == 'general':
                results = self._analyze_general_feedback(feedback_query)
            elif analysis.analysis_type == 'topic_specific':
                results = self._analyze_topic_specific_feedback(feedback_query)
            elif analysis.analysis_type == 'prompt_focused':
                results = self._analyze_prompt_optimization(feedback_query)
            elif analysis.analysis_type == 'retrieval_focused':
                results = self._analyze_retrieval_optimization(feedback_query)
            elif analysis.analysis_type == 'citation_focused':
                results = self._analyze_citation_quality(feedback_query)
            else:
                results = self._analyze_general_feedback(feedback_query)
            
            # Update with feedback count
            results['feedback_count'] = feedback_count
            
            # Generate a summary
            summary = self._generate_analysis_summary(results)
            
            # Complete the analysis
            analysis.complete_analysis(results, summary)
            
            # Generate improvement recommendations if appropriate
            if results['primary_issues'] and len(results['primary_issues']) > 0:
                self._generate_improvement_recommendations(analysis)
            
            return analysis
            
        except QualityAnalysis.DoesNotExist:
            logger.error(f"Quality analysis {analysis_id} not found")
            raise ValueError(f"Quality analysis {analysis_id} not found")
        except Exception as e:
            logger.exception(f"Error running quality analysis: {str(e)}")
            if 'analysis' in locals():
                analysis.status = 'failed'
                analysis.save()
            raise
    
    def _analyze_general_feedback(self, feedback_query) -> Dict:
        """
        Perform general feedback analysis.
        
        Args:
            feedback_query: QuerySet of EnhancedFeedback objects
            
        Returns:
            Dict of analysis results
        """
        # Calculate overall metrics
        pos_count = feedback_query.filter(rating='thumbs_up').count()
        neg_count = feedback_query.filter(rating='thumbs_down').count()
        neu_count = feedback_query.filter(rating='neutral').count()
        total_count = feedback_query.count()
        
        satisfaction_rate = pos_count / total_count if total_count > 0 else 0
        
        # Get all specific issues reported
        all_issues = []
        for feedback in feedback_query:
            if feedback.specific_issues:
                all_issues.extend(feedback.specific_issues)
        
        # Count frequencies
        issue_frequencies = {}
        for issue in all_issues:
            issue_frequencies[issue] = issue_frequencies.get(issue, 0) + 1
        
        # Sort by frequency (most frequent first)
        sorted_issues = sorted(
            issue_frequencies.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Extract top issues
        top_issues = [{'name': k, 'count': v} for k, v in sorted_issues[:10]]
        
        # Get average ratings
        avg_ratings = {}
        rating_fields = [
            'relevance_rating', 'accuracy_rating', 'completeness_rating', 
            'clarity_rating', 'citation_rating'
        ]
        
        for field in rating_fields:
            avg = feedback_query.exclude(**{f"{field}__isnull": True}).aggregate(
                avg=Avg(field)
            )['avg']
            if avg:
                avg_ratings[field] = avg
        
        # Identify common incorrect sections
        incorrect_sections = []
        for feedback in feedback_query:
            if feedback.incorrect_sections:
                if isinstance(feedback.incorrect_sections, list):
                    incorrect_sections.extend(feedback.incorrect_sections)
                elif isinstance(feedback.incorrect_sections, dict):
                    incorrect_sections.extend(feedback.incorrect_sections.keys())
        
        # Source quality issues
        source_issues = []
        for feedback in feedback_query:
            if feedback.source_quality_issues:
                source_issues.extend(feedback.source_quality_issues)
        
        source_issue_frequencies = {}
        for issue in source_issues:
            source_issue_frequencies[issue] = source_issue_frequencies.get(issue, 0) + 1
        
        # Temporal analysis
        feedback_by_date = feedback_query.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            positive=Count('id', filter=Q(rating='thumbs_up')),
            negative=Count('id', filter=Q(rating='thumbs_down')),
            neutral=Count('id', filter=Q(rating='neutral')),
            total=Count('id')
        ).order_by('date')
        
        daily_trends = {
            str(item['date']): {
                'positive': item['positive'],
                'negative': item['negative'],
                'neutral': item['neutral'],
                'total': item['total'],
                'satisfaction': item['positive'] / item['total'] if item['total'] > 0 else 0
            }
            for item in feedback_by_date
        }
        
        # Calculate quality score
        quality_score = (0.5 * satisfaction_rate) + (0.5 * (sum(avg_ratings.values()) / len(avg_ratings) / 5 if avg_ratings else 0))
        
        # Return combined analysis
        primary_issues = [issue['name'] for issue in top_issues[:5]] if top_issues else []
        
        return {
            'identified_issues': all_issues,
            'issue_frequencies': issue_frequencies,
            'primary_issues': primary_issues,
            'avg_ratings': avg_ratings,
            'incorrect_sections': incorrect_sections,
            'source_issues': source_issue_frequencies,
            'temporal_trends': daily_trends,
            'quality_score': quality_score,
            'difficulty_assessment': {
                'overall_satisfaction': satisfaction_rate,
                'rating_distributions': {
                    'thumbs_up': pos_count,
                    'thumbs_down': neg_count,
                    'neutral': neu_count
                }
            }
        }
    
    def _analyze_topic_specific_feedback(self, feedback_query) -> Dict:
        """
        Analyze feedback grouped by topics.
        
        Args:
            feedback_query: QuerySet of EnhancedFeedback objects
            
        Returns:
            Dict of topic-specific analysis results
        """
        # Group queries by topic
        topic_feedback = {}
        
        for feedback in feedback_query:
            # Extract topics from the query text
            query_text = feedback.query_history.query_text if feedback.query_history else ""
            
            # This is a simplified approach - in a real system, you would
            # use NLP to extract topics or use pre-tagged topics
            # For now, we'll use a basic keyword approach
            topics = self._extract_topics(query_text)
            
            for topic in topics:
                if topic not in topic_feedback:
                    topic_feedback[topic] = []
                topic_feedback[topic].append(feedback)
        
        # Analyze each topic
        topic_analyses = {}
        for topic, feedbacks in topic_feedback.items():
            # Skip topics with too few feedback items
            if len(feedbacks) < 3:
                continue
                
            # Create a queryset from these feedback items
            topic_ids = [f.id for f in feedbacks]
            topic_queryset = EnhancedFeedback.objects.filter(id__in=topic_ids)
            
            # Perform basic analysis
            topic_analysis = self._analyze_general_feedback(topic_queryset)
            
            # Add to results
            topic_analyses[topic] = {
                'feedback_count': len(feedbacks),
                'primary_issues': topic_analysis['primary_issues'],
                'quality_score': topic_analysis['quality_score'],
                'avg_ratings': topic_analysis['avg_ratings']
            }
        
        # Identify topics with the most issues
        problem_topics = sorted(
            [
                {
                    'topic': topic, 
                    'score': analysis['quality_score'],
                    'count': analysis['feedback_count'],
                    'issues': analysis['primary_issues']
                }
                for topic, analysis in topic_analyses.items()
            ],
            key=lambda x: x['score']
        )
        
        # Overall metrics
        overall_analysis = self._analyze_general_feedback(feedback_query)
        
        return {
            'topic_clusters': topic_analyses,
            'problem_topics': problem_topics[:5],
            'identified_issues': overall_analysis['identified_issues'],
            'issue_frequencies': overall_analysis['issue_frequencies'],
            'primary_issues': overall_analysis['primary_issues'],
            'quality_score': overall_analysis['quality_score'],
            'difficulty_assessment': overall_analysis['difficulty_assessment']
        }
    
    def _analyze_prompt_optimization(self, feedback_query) -> Dict:
        """
        Analyze feedback focused on prompt improvements.
        
        Args:
            feedback_query: QuerySet of EnhancedFeedback objects
            
        Returns:
            Dict of prompt optimization analysis results
        """
        # Get general analysis first
        general_analysis = self._analyze_general_feedback(feedback_query)
        
        # Extract feedback that mentions specific prompt-related issues
        prompt_issues = [
            'not directly answering the question',
            'too verbose',
            'too brief',
            'not specific enough',
            'incorrect information',
            'missing information'
        ]
        
        # Count how many feedback items mention each prompt issue
        prompt_issue_counts = {}
        for issue in prompt_issues:
            count = feedback_query.filter(specific_issues__contains=[issue]).count()
            prompt_issue_counts[issue] = count
        
        # Analyze suggested answers when available
        suggested_improvements = []
        for feedback in feedback_query:
            if feedback.suggested_answer and len(feedback.suggested_answer) > 10:
                suggested_improvements.append({
                    'original_query': feedback.query_history.query_text if feedback.query_history else "",
                    'suggestion': feedback.suggested_answer,
                    'issues': feedback.specific_issues,
                    'rating': feedback.rating
                })
        
        # Identify patterns in successful vs unsuccessful prompts
        successful_queries = feedback_query.filter(rating='thumbs_up')
        unsuccessful_queries = feedback_query.filter(rating='thumbs_down')
        
        # Extract query patterns (simplified - would use NLP in real implementation)
        successful_patterns = self._extract_query_patterns(successful_queries)
        unsuccessful_patterns = self._extract_query_patterns(unsuccessful_queries)
        
        # Recommended prompt improvements
        prompt_recommendations = []
        
        # Based on most common issues, generate recommendations
        for issue, count in sorted(prompt_issue_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= 3:  # Only consider issues mentioned at least 3 times
                if issue == 'not directly answering the question':
                    prompt_recommendations.append(
                        "Strengthen the directive to answer the specific question asked"
                    )
                elif issue == 'too verbose':
                    prompt_recommendations.append(
                        "Add instruction to provide concise, focused answers"
                    )
                elif issue == 'too brief':
                    prompt_recommendations.append(
                        "Add instruction to provide comprehensive answers with sufficient detail"
                    )
                elif issue == 'not specific enough':
                    prompt_recommendations.append(
                        "Add instruction to include specific techniques, values, and protocols when relevant"
                    )
                elif issue == 'incorrect information':
                    prompt_recommendations.append(
                        "Strengthen requirement to only include information from provided sources"
                    )
                elif issue == 'missing information':
                    prompt_recommendations.append(
                        "Add instruction to comprehensively cover important aspects of the topic"
                    )
        
        return {
            'identified_issues': general_analysis['identified_issues'],
            'issue_frequencies': general_analysis['issue_frequencies'],
            'primary_issues': general_analysis['primary_issues'],
            'quality_score': general_analysis['quality_score'],
            'difficulty_assessment': general_analysis['difficulty_assessment'],
            'prompt_specific_issues': prompt_issue_counts,
            'suggested_improvements': suggested_improvements[:10],  # Limit to 10 examples
            'successful_patterns': successful_patterns,
            'unsuccessful_patterns': unsuccessful_patterns,
            'prompt_recommendations': prompt_recommendations
        }
    
    def _analyze_retrieval_optimization(self, feedback_query) -> Dict:
        """
        Analyze feedback focused on retrieval improvements.
        
        Args:
            feedback_query: QuerySet of EnhancedFeedback objects
            
        Returns:
            Dict of retrieval optimization analysis results
        """
        # Get general analysis first
        general_analysis = self._analyze_general_feedback(feedback_query)
        
        # Extract feedback that mentions specific retrieval-related issues
        retrieval_issues = [
            'missing information',
            'incorrect citations',
            'irrelevant sources',
            'hallucinated content'
        ]
        
        # Count source quality issues
        source_quality_issues = {}
        for feedback in feedback_query:
            if feedback.source_quality_issues:
                for issue in feedback.source_quality_issues:
                    source_quality_issues[issue] = source_quality_issues.get(issue, 0) + 1
        
        # Analyze feedback by doc type
        doc_type_feedback = {}
        for feedback in feedback_query:
            if not feedback.query_history:
                continue
                
            # Get associated query
            query = feedback.query_history
            
            # Extract doc type from query parameters
            doc_type = query.query_params.get('doc_type', 'all') if query.query_params else 'all'
            
            if doc_type not in doc_type_feedback:
                doc_type_feedback[doc_type] = {
                    'total': 0,
                    'thumbs_up': 0,
                    'thumbs_down': 0,
                    'neutral': 0
                }
            
            doc_type_feedback[doc_type]['total'] += 1
            doc_type_feedback[doc_type][feedback.rating] = doc_type_feedback[doc_type].get(feedback.rating, 0) + 1
        
        # Calculate satisfaction rate by doc type
        for doc_type, stats in doc_type_feedback.items():
            if stats['total'] > 0:
                stats['satisfaction_rate'] = stats['thumbs_up'] / stats['total']
            else:
                stats['satisfaction_rate'] = 0
        
        # Analyze hybrid search impact
        hybrid_impact = {
            'hybrid_on': {
                'total': 0,
                'thumbs_up': 0,
                'satisfaction_rate': 0
            },
            'hybrid_off': {
                'total': 0,
                'thumbs_up': 0,
                'satisfaction_rate': 0
            }
        }
        
        for feedback in feedback_query:
            if not feedback.query_history:
                continue
                
            # Get associated query
            query = feedback.query_history
            
            # Check if hybrid search was used
            use_hybrid = query.query_params.get('use_hybrid', True) if query.query_params else True
            
            category = 'hybrid_on' if use_hybrid else 'hybrid_off'
            hybrid_impact[category]['total'] += 1
            
            if feedback.rating == 'thumbs_up':
                hybrid_impact[category]['thumbs_up'] += 1
        
        # Calculate satisfaction rates
        for category, stats in hybrid_impact.items():
            if stats['total'] > 0:
                stats['satisfaction_rate'] = stats['thumbs_up'] / stats['total']
        
        # Generate retrieval recommendations
        retrieval_recommendations = []
        
        # Based on analysis, generate recommendations
        if source_quality_issues.get('Irrelevant sources retrieved', 0) >= 3:
            retrieval_recommendations.append(
                "Increase semantic search weight in hybrid retrieval"
            )
        
        if source_quality_issues.get('Missing key sources', 0) >= 3:
            retrieval_recommendations.append(
                "Increase number of documents retrieved"
            )
        
        # Compare hybrid search performance
        if (hybrid_impact['hybrid_on']['total'] >= 10 and 
            hybrid_impact['hybrid_off']['total'] >= 10):
            
            if hybrid_impact['hybrid_on']['satisfaction_rate'] > hybrid_impact['hybrid_off']['satisfaction_rate']:
                retrieval_recommendations.append(
                    "Keep hybrid search enabled as default (performing better)"
                )
            else:
                retrieval_recommendations.append(
                    "Consider semantic-only search as default (hybrid not showing improvement)"
                )
        
        # Add doc type specific recommendations
        poor_performing_doc_types = []
        for doc_type, stats in doc_type_feedback.items():
            if stats['total'] >= 10 and stats['satisfaction_rate'] < 0.6:  # Arbitrary threshold
                poor_performing_doc_types.append(doc_type)
                
        if poor_performing_doc_types:
            doc_list = ", ".join(poor_performing_doc_types)
            retrieval_recommendations.append(
                f"Optimize retrieval parameters for document types: {doc_list}"
            )
        
        return {
            'identified_issues': general_analysis['identified_issues'],
            'issue_frequencies': general_analysis['issue_frequencies'],
            'primary_issues': general_analysis['primary_issues'],
            'quality_score': general_analysis['quality_score'],
            'difficulty_assessment': general_analysis['difficulty_assessment'],
            'source_quality_issues': source_quality_issues,
            'doc_type_performance': doc_type_feedback,
            'hybrid_search_performance': hybrid_impact,
            'retrieval_recommendations': retrieval_recommendations
        }
    
    def _analyze_citation_quality(self, feedback_query) -> Dict:
        """
        Analyze feedback focused on citation quality.
        
        Args:
            feedback_query: QuerySet of EnhancedFeedback objects
            
        Returns:
            Dict of citation quality analysis results
        """
        # Get general analysis first
        general_analysis = self._analyze_general_feedback(feedback_query)
        
        # Extract feedback that mentions specific citation-related issues
        citation_issues = [
            'incorrect citations',
            'hallucinated content'
        ]
        
        # Get average citation rating
        avg_citation_rating = feedback_query.exclude(
            citation_rating__isnull=True
        ).aggregate(avg=Avg('citation_rating'))['avg'] or 0
        
        # Count citation issues
        citation_issue_counts = {}
        for issue in citation_issues:
            count = feedback_query.filter(specific_issues__contains=[issue]).count()
            citation_issue_counts[issue] = count
        
        # Source quality issues related to citations
        citation_source_issues = {}
        for feedback in feedback_query:
            if feedback.source_quality_issues:
                for issue in feedback.source_quality_issues:
                    if issue in ['Citations don\'t match content', 'Sources misinterpreted']:
                        citation_source_issues[issue] = citation_source_issues.get(issue, 0) + 1
        
        # Generate citation recommendations
        citation_recommendations = []
        
        # Based on analysis, generate recommendations
        if avg_citation_rating < 3.5 and feedback_query.count() >= 10:
            citation_recommendations.append(
                "Improve citation formatting and clarity in answer generation"
            )
        
        if citation_issue_counts.get('incorrect citations', 0) >= 3:
            citation_recommendations.append(
                "Enhance source attribution verification in prompts"
            )
        
        if citation_issue_counts.get('hallucinated content', 0) >= 3:
            citation_recommendations.append(
                "Strengthen constraints against generating unsourced content"
            )
        
        if citation_source_issues.get('Citations don\'t match content', 0) >= 3:
            citation_recommendations.append(
                "Improve alignment between citations and content"
            )
        
        return {
            'identified_issues': general_analysis['identified_issues'],
            'issue_frequencies': general_analysis['issue_frequencies'],
            'primary_issues': general_analysis['primary_issues'],
            'quality_score': general_analysis['quality_score'],
            'difficulty_assessment': general_analysis['difficulty_assessment'],
            'avg_citation_rating': avg_citation_rating,
            'citation_issue_counts': citation_issue_counts,
            'citation_source_issues': citation_source_issues,
            'citation_recommendations': citation_recommendations
        }
    
    def _extract_topics(self, query_text: str) -> List[str]:
        """
        Extract topics from a query text (simplified implementation).
        
        Args:
            query_text: The text of the query
            
        Returns:
            List of identified topics
        """
        # In a real implementation, this would use:
        # 1. NLP for topic extraction
        # 2. A predefined topic taxonomy
        # 3. Possibly a topic classifier model
        
        # This is a simplified implementation with hardcoded topics
        topics = []
        query_lower = query_text.lower()
        
        # Check for common lab technique topics
        if any(term in query_lower for term in ['pcr', 'polymerase chain reaction']):
            topics.append('PCR')
        
        if any(term in query_lower for term in ['rna', 'extraction', 'isolate rna']):
            topics.append('RNA Extraction')
        
        if any(term in query_lower for term in ['western blot', 'blotting']):
            topics.append('Western Blot')
            
        if any(term in query_lower for term in ['crispr', 'cas9', 'gene edit']):
            topics.append('CRISPR')
            
        if any(term in query_lower for term in ['protocol', 'procedure', 'method']):
            topics.append('Lab Protocols')
            
        # If no specific topics identified, use a generic one
        if not topics:
            topics.append('General')
            
        return topics
    
    def _extract_query_patterns(self, query_feedback) -> Dict:
        """
        Extract common patterns from queries (simplified implementation).
        
        Args:
            query_feedback: QuerySet of feedback items
            
        Returns:
            Dict of identified patterns
        """
        # This would be implemented with NLP in a real system
        # For now, just count some basic patterns
        
        patterns = {
            'starts_with_how': 0,
            'starts_with_what': 0,
            'starts_with_why': 0,
            'contains_protocol': 0,
            'contains_specific_value': 0,
            'query_length_short': 0,
            'query_length_medium': 0,
            'query_length_long': 0,
        }
        
        for feedback in query_feedback:
            if not feedback.query_history:
                continue
                
            query_text = feedback.query_history.query_text.lower()
            
            # Check starting words
            if query_text.startswith('how'):
                patterns['starts_with_how'] += 1
            elif query_text.startswith('what'):
                patterns['starts_with_what'] += 1
            elif query_text.startswith('why'):
                patterns['starts_with_why'] += 1
            
            # Check for keywords
            if 'protocol' in query_text:
                patterns['contains_protocol'] += 1
                
            # Check for specific values (numbers, units, etc.)
            if any(char.isdigit() for char in query_text) or any(unit in query_text for unit in ['mg', 'ml', 'µl', 'nm']):
                patterns['contains_specific_value'] += 1
            
            # Classify by length
            length = len(query_text.split())
            if length < 5:
                patterns['query_length_short'] += 1
            elif length < 15:
                patterns['query_length_medium'] += 1
            else:
                patterns['query_length_long'] += 1
        
        return patterns
    
    def _generate_analysis_summary(self, results: Dict) -> str:
        """
        Generate a text summary of analysis results.
        
        Args:
            results: Analysis results dictionary
            
        Returns:
            Summary text
        """
        # Extract key metrics
        quality_score = results.get('quality_score', 0)
        primary_issues = results.get('primary_issues', [])
        
        feedback_count = results.get('feedback_count', 0)
        
        # Start building summary
        summary_lines = [
            f"Analysis of {feedback_count} feedback items found a quality score of {quality_score:.2f}/1.0.",
        ]
        
        # Add primary issues if present
        if primary_issues:
            summary_lines.append(f"Top identified issues: {', '.join(primary_issues[:3])}.")
        
        # Add recommendations based on analysis type and results
        if 'prompt_recommendations' in results and results['prompt_recommendations']:
            summary_lines.append(f"Primary prompt recommendations: {results['prompt_recommendations'][0]}")
            
        elif 'retrieval_recommendations' in results and results['retrieval_recommendations']:
            summary_lines.append(f"Primary retrieval recommendations: {results['retrieval_recommendations'][0]}")
            
        elif 'citation_recommendations' in results and results['citation_recommendations']:
            summary_lines.append(f"Primary citation recommendations: {results['citation_recommendations'][0]}")
        
        # Add improvement potential
        if quality_score < 0.5:
            summary_lines.append("Significant quality improvements are needed.")
        elif quality_score < 0.7:
            summary_lines.append("Moderate quality improvements would be beneficial.")
        else:
            summary_lines.append("Quality is good, but minor improvements can still be made.")
        
        return " ".join(summary_lines)
    
    def _generate_improvement_recommendations(self, analysis: QualityAnalysis) -> List[QualityImprovement]:
        """
        Generate improvement recommendations based on analysis.
        
        Args:
            analysis: The completed quality analysis
            
        Returns:
            List of created QualityImprovement objects
        """
        improvements = []
        
        # Skip if no primary issues identified
        if not analysis.primary_issues:
            return improvements
        
        # Get analysis results based on type
        if analysis.analysis_type == 'prompt_focused' and analysis.identified_issues:
            # For prompt analysis, use prompt-specific recommendations
            prompt_recommendations = analysis.identified_issues.get('prompt_recommendations', [])
            
            for i, recommendation in enumerate(prompt_recommendations):
                priority = 'high' if i < 2 else 'medium'
                
                improvement = QualityImprovement.objects.create(
                    title=f"Prompt Improvement: {recommendation[:50]}...",
                    description=recommendation,
                    improvement_type='prompt',
                    priority=priority,
                    source_analysis=analysis,
                    expected_impact="Improved answer quality based on feedback patterns",
                    implementation_effort="Medium"
                )
                improvements.append(improvement)
        
        elif analysis.analysis_type == 'retrieval_focused' and analysis.identified_issues:
            # For retrieval analysis, use retrieval-specific recommendations
            retrieval_recommendations = analysis.identified_issues.get('retrieval_recommendations', [])
            
            for i, recommendation in enumerate(retrieval_recommendations):
                priority = 'high' if i < 2 else 'medium'
                
                improvement = QualityImprovement.objects.create(
                    title=f"Retrieval Improvement: {recommendation[:50]}...",
                    description=recommendation,
                    improvement_type='retrieval',
                    priority=priority,
                    source_analysis=analysis,
                    expected_impact="Better document retrieval accuracy and relevance",
                    implementation_effort="Medium"
                )
                improvements.append(improvement)
        
        elif analysis.analysis_type == 'citation_focused' and analysis.identified_issues:
            # For citation analysis, use citation-specific recommendations
            citation_recommendations = analysis.identified_issues.get('citation_recommendations', [])
            
            for i, recommendation in enumerate(citation_recommendations):
                priority = 'high' if i < 2 else 'medium'
                
                improvement = QualityImprovement.objects.create(
                    title=f"Citation Improvement: {recommendation[:50]}...",
                    description=recommendation,
                    improvement_type='citation',
                    priority=priority,
                    source_analysis=analysis,
                    expected_impact="More accurate and helpful citations",
                    implementation_effort="Medium"
                )
                improvements.append(improvement)
        
        else:
            # For general analysis, create generic improvements based on primary issues
            for i, issue in enumerate(analysis.primary_issues[:3]):  # Focus on top 3 issues
                # Determine improvement type based on issue content
                improvement_type = 'other'
                if any(term in issue.lower() for term in ['direct', 'specific', 'verbose', 'brief']):
                    improvement_type = 'prompt'
                elif any(term in issue.lower() for term in ['citation', 'source']):
                    improvement_type = 'citation'
                elif any(term in issue.lower() for term in ['relevant', 'missing information']):
                    improvement_type = 'retrieval'
                
                # Create improvement
                priority = 'high' if i == 0 else 'medium'
                
                improvement = QualityImprovement.objects.create(
                    title=f"Improvement for '{issue}'",
                    description=f"Address the feedback issue: {issue}",
                    improvement_type=improvement_type,
                    priority=priority,
                    source_analysis=analysis,
                    expected_impact="Improved answer quality based on feedback patterns",
                    implementation_effort="Medium"
                )
                improvements.append(improvement)
        
        return improvements
    
    def get_improvement_recommendations(
        self, 
        improvement_type: str = None,
        status: str = 'proposed',
        limit: int = 10
    ) -> List[QualityImprovement]:
        """
        Get current improvement recommendations.
        
        Args:
            improvement_type: Filter by improvement type (optional)
            status: Filter by status (default: proposed)
            limit: Maximum number of recommendations to return
            
        Returns:
            List of QualityImprovement objects
        """
        query = QualityImprovement.objects.filter(status=status)
        
        if improvement_type:
            query = query.filter(improvement_type=improvement_type)
        
        return query.order_by('priority', '-created_at')[:limit]
    
    def approve_improvement(
        self, 
        improvement_id: str,
        user = None
    ) -> QualityImprovement:
        """
        Approve an improvement for implementation.
        
        Args:
            improvement_id: ID of the improvement to approve
            user: User approving the improvement (optional)
            
        Returns:
            The updated QualityImprovement object
        """
        try:
            improvement = QualityImprovement.objects.get(improvement_id=improvement_id)
            improvement.approve(user)
            return improvement
        except QualityImprovement.DoesNotExist:
            logger.error(f"Improvement {improvement_id} not found")
            raise ValueError(f"Improvement {improvement_id} not found")
    
    def implement_improvement(
        self, 
        improvement_id: str
    ) -> Dict:
        """
        Implement an approved improvement.
        
        Args:
            improvement_id: ID of the improvement to implement
            
        Returns:
            Dict with implementation results
        """
        try:
            improvement = QualityImprovement.objects.get(
                improvement_id=improvement_id,
                status='approved'
            )
            
            implementation_details = {}
            
            # Implement based on improvement type
            if improvement.improvement_type == 'prompt':
                implementation_details = self._implement_prompt_improvement(improvement)
            elif improvement.improvement_type == 'retrieval':
                implementation_details = self._implement_retrieval_improvement(improvement)
            elif improvement.improvement_type == 'citation':
                implementation_details = self._implement_citation_improvement(improvement)
            else:
                implementation_details = {
                    'status': 'warning',
                    'message': f"Unknown improvement type: {improvement.improvement_type}"
                }
            
            # Mark as implemented
            improvement.implement(implementation_details)
            
            return {
                'improvement': improvement,
                'results': implementation_details
            }
            
        except QualityImprovement.DoesNotExist:
            logger.error(f"Approved improvement {improvement_id} not found")
            raise ValueError(f"Approved improvement {improvement_id} not found")
        except Exception as e:
            logger.exception(f"Error implementing improvement: {str(e)}")
            raise
    
    def _implement_prompt_improvement(self, improvement: QualityImprovement) -> Dict:
        """
        Implement a prompt improvement.
        
        Args:
            improvement: The improvement to implement
            
        Returns:
            Dict with implementation details
        """
        # Determine prompt type based on the improvement
        prompt_type = 'system'  # Default
        
        description = improvement.description.lower()
        if 'answer' in description or 'specific question' in description:
            prompt_type = 'answer_generation'
        elif 'citation' in description:
            prompt_type = 'citation'
        
        # Get current active prompt or create new
        current_prompt = ImprovedPrompt.objects.filter(
            prompt_type=prompt_type,
            status='active'
        ).first()
        
        if current_prompt:
            # Create new version based on current
            prompt_text = self._modify_prompt_based_on_improvement(
                current_prompt.prompt_text,
                improvement
            )
            
            new_prompt = current_prompt.create_new_version(
                prompt_text=prompt_text,
                description=f"Improvement: {improvement.title}"
            )
        else:
            # Create new prompt from scratch
            base_prompt = self._get_base_prompt_for_type(prompt_type)
            prompt_text = self._modify_prompt_based_on_improvement(
                base_prompt,
                improvement
            )
            
            new_prompt = ImprovedPrompt.objects.create(
                name=f"{prompt_type.title()} Prompt",
                description=f"Initial improved {prompt_type} prompt",
                prompt_type=prompt_type,
                prompt_text=prompt_text,
                status='draft',
                source_improvement=improvement
            )
        
        # Activate the new prompt
        new_prompt.activate()
        
        return {
            'status': 'success',
            'prompt_id': str(new_prompt.prompt_id),
            'prompt_type': prompt_type,
            'message': f"Created and activated new {prompt_type} prompt"
        }
    
    def _implement_retrieval_improvement(self, improvement: QualityImprovement) -> Dict:
        """
        Implement a retrieval configuration improvement.
        
        Args:
            improvement: The improvement to implement
            
        Returns:
            Dict with implementation details
        """
        # Get current active configuration or create new
        current_config = RetrievalConfiguration.objects.filter(
            status='active'
        ).first()
        
        # Default parameters (simplified example)
        default_params = {
            'hybrid_alpha': 0.75,
            'top_k': 5,
            'min_score': 0.2,
            'use_hybrid': True
        }
        
        if current_config:
            # Base new config on current one
            params = current_config.parameters.copy()
        else:
            # Use defaults
            params = default_params
        
        # Modify parameters based on improvement
        params = self._modify_retrieval_params_based_on_improvement(
            params,
            improvement
        )
        
        # Create new configuration
        if current_config:
            new_config = current_config.create_new_version(
                parameters=params,
                description=f"Improvement: {improvement.title}"
            )
        else:
            new_config = RetrievalConfiguration.objects.create(
                name="Base Retrieval Configuration",
                description=f"Initial improved retrieval configuration",
                parameters=params,
                status='draft',
                source_improvement=improvement
            )
        
        # Activate the new configuration
        new_config.activate()
        
        return {
            'status': 'success',
            'config_id': str(new_config.config_id),
            'parameters': params,
            'message': "Created and activated new retrieval configuration"
        }
    
    def _implement_citation_improvement(self, improvement: QualityImprovement) -> Dict:
        """
        Implement a citation improvement.
        
        Args:
            improvement: The improvement to implement
            
        Returns:
            Dict with implementation details
        """
        # Citation improvements may involve both prompt and retrieval changes
        
        # First, check if we need a prompt change
        if any(term in improvement.description.lower() for term in 
              ['format', 'citation style', 'clarity', 'attribution']):
            # Implement as a prompt change
            prompt_result = self._implement_prompt_improvement(improvement)
            
            return {
                'status': 'success',
                'prompt_id': prompt_result.get('prompt_id'),
                'message': "Implemented citation improvement via prompt modification"
            }
        else:
            # Implement as a retrieval configuration change
            config_result = self._implement_retrieval_improvement(improvement)
            
            return {
                'status': 'success',
                'config_id': config_result.get('config_id'),
                'message': "Implemented citation improvement via retrieval modification"
            }
    
    def _get_base_prompt_for_type(self, prompt_type: str) -> str:
        """
        Get the base prompt text for a given prompt type.
        
        Args:
            prompt_type: Type of prompt to get
            
        Returns:
            Base prompt text
        """
        # In a real implementation, these would be stored in a database
        # or configuration file, not hardcoded
        
        if prompt_type == 'system':
            return (
                "Answer only from the provided sources; if unsure, say 'I don't know.' "
                "You are an AI assistant for a RNA biology lab, helping researchers "
                "with protocols, papers, and theses. Provide accurate, concise information "
                "with proper citations to the source documents."
            )
        elif prompt_type == 'answer_generation':
            return (
                "Based on the provided sources, answer the user's question. "
                "Always include citations to the sources. "
                "If the information isn't in the sources, say 'I don't have "
                "enough information to answer this question.'"
            )
        elif prompt_type == 'citation':
            return (
                "Cite sources by their document title when you use information from them. "
                "For example: 'According to [Document Title], ...' "
                "Make sure each piece of information is properly attributed to its source."
            )
        else:
            return "Provide helpful and accurate information based on the sources."
    
    def _modify_prompt_based_on_improvement(
        self, 
        current_prompt: str,
        improvement: QualityImprovement
    ) -> str:
        """
        Modify a prompt based on an improvement.
        
        Args:
            current_prompt: Current prompt text
            improvement: The improvement to implement
            
        Returns:
            Modified prompt text
        """
        # This is a simplified implementation
        # In a real system, this would use more sophisticated NLP to
        # understand the improvement and apply appropriate changes
        
        # Extract key phrases from the improvement
        desc = improvement.description.lower()
        
        # Prepare modifications based on common improvement patterns
        modifications = []
        
        if 'concise' in desc or 'brief' in desc:
            modifications.append("Provide concise and focused answers without unnecessary details.")
            
        if 'comprehensive' in desc or 'detailed' in desc:
            modifications.append("Ensure comprehensive coverage of important aspects of the question.")
            
        if 'specific' in desc:
            modifications.append("Include specific techniques, values, and protocols when relevant.")
            
        if 'directly' in desc or 'specific question' in desc:
            modifications.append("Directly address the specific question being asked.")
            
        if 'citation' in desc or 'source' in desc:
            modifications.append("Include clear citations for every piece of information, formatted as [Document Title].")
            
        if 'incorrect' in desc:
            modifications.append("Only include information that is explicitly stated in the provided sources.")
        
        # If no specific modifications identified, use a generic improvement
        if not modifications:
            modifications.append(improvement.description)
        
        # Apply modifications to the prompt
        new_prompt = current_prompt
        
        # Check if modifications are already present
        for mod in modifications:
            mod_key = mod.split(' ')[0:3]  # Use first few words as a key
            mod_key_str = ' '.join(mod_key).lower()
            
            # Only add if something similar isn't already there
            if mod_key_str not in new_prompt.lower():
                # Add the modification
                new_prompt = f"{new_prompt} {mod}"
        
        return new_prompt
    
    def _modify_retrieval_params_based_on_improvement(
        self, 
        current_params: Dict,
        improvement: QualityImprovement
    ) -> Dict:
        """
        Modify retrieval parameters based on an improvement.
        
        Args:
            current_params: Current retrieval parameters
            improvement: The improvement to implement
            
        Returns:
            Modified parameters
        """
        # This is a simplified implementation
        # In a real system, this would use more sophisticated analysis
        
        desc = improvement.description.lower()
        params = current_params.copy()
        
        # Apply changes based on improvement description
        if 'semantic search weight' in desc or 'vector search weight' in desc:
            # Adjust hybrid alpha
            if 'increase' in desc:
                params['hybrid_alpha'] = min(1.0, params.get('hybrid_alpha', 0.75) + 0.1)
            elif 'decrease' in desc:
                params['hybrid_alpha'] = max(0.0, params.get('hybrid_alpha', 0.75) - 0.1)
        
        if 'number of documents' in desc:
            # Adjust top_k
            if 'increase' in desc:
                params['top_k'] = min(10, params.get('top_k', 5) + 2)
            elif 'decrease' in desc:
                params['top_k'] = max(3, params.get('top_k', 5) - 1)
        
        if 'hybrid search' in desc:
            # Enable/disable hybrid search
            if 'enable' in desc:
                params['use_hybrid'] = True
            elif 'disable' in desc:
                params['use_hybrid'] = False
        
        if 'threshold' in desc or 'minimum score' in desc:
            # Adjust minimum score threshold
            if 'increase' in desc:
                params['min_score'] = min(0.5, params.get('min_score', 0.2) + 0.05)
            elif 'decrease' in desc:
                params['min_score'] = max(0.1, params.get('min_score', 0.2) - 0.05)
        
        return params
    
    def get_quality_metrics(self, days: int = 30) -> Dict:
        """
        Get quality metrics for the specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict of quality metrics
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get feedback in the period
        feedback = EnhancedFeedback.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        total_count = feedback.count()
        if total_count == 0:
            return {
                'period': f"{start_date.date()} to {end_date.date()}",
                'total_feedback': 0,
                'message': "No feedback data available for the period"
            }
        
        # Calculate satisfaction rate
        positive_count = feedback.filter(rating='thumbs_up').count()
        satisfaction_rate = positive_count / total_count
        
        # Get average ratings
        avg_ratings = {}
        rating_fields = [
            'relevance_rating', 'accuracy_rating', 'completeness_rating', 
            'clarity_rating', 'citation_rating'
        ]
        
        for field in rating_fields:
            avg = feedback.exclude(**{f"{field}__isnull": True}).aggregate(
                avg=Avg(field)
            )['avg']
            if avg:
                avg_ratings[field] = avg
        
        # Calculate overall quality score
        quality_score = (
            (0.5 * satisfaction_rate) + 
            (0.5 * (sum(avg_ratings.values()) / len(avg_ratings) / 5 if avg_ratings else 0))
        )
        
        # Get implemented improvements in the period
        improvements = QualityImprovement.objects.filter(
            implemented_at__gte=start_date,
            implemented_at__lte=end_date,
            status='implemented'
        )
        
        # Calculate daily trend
        daily_trend = feedback.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            positive=Count('id', filter=Q(rating='thumbs_up')),
            negative=Count('id', filter=Q(rating='thumbs_down')),
            neutral=Count('id', filter=Q(rating='neutral')),
            total=Count('id')
        ).order_by('date')
        
        daily_quality = {}
        for day in daily_trend:
            date_str = str(day['date'])
            daily_quality[date_str] = {
                'feedback_count': day['total'],
                'satisfaction_rate': day['positive'] / day['total'] if day['total'] > 0 else 0
            }
        
        return {
            'period': f"{start_date.date()} to {end_date.date()}",
            'total_feedback': total_count,
            'satisfaction_rate': satisfaction_rate,
            'quality_score': quality_score,
            'rating_averages': avg_ratings,
            'improvements_implemented': improvements.count(),
            'daily_trend': daily_quality
        }
    
    def run_quality_improvement_pipeline(self) -> Dict:
        """
        Run the complete quality improvement pipeline.
        
        This includes:
        1. Generating a new quality analysis
        2. Generating improvement recommendations
        3. Auto-approving high-priority improvements
        4. Implementing approved improvements
        
        Returns:
            Dict with pipeline results
        """
        results = {
            'analysis': None,
            'recommendations': [],
            'approved': [],
            'implemented': [],
            'metrics_before': self.get_quality_metrics(days=30)
        }
        
        try:
            # Generate analysis
            analysis = self.generate_quality_analysis(
                name=f"Automated Quality Analysis {timezone.now().strftime('%Y-%m-%d')}",
                analysis_type='general',
                days_lookback=30
            )
            
            # Run the analysis
            analysis = self.run_quality_analysis(analysis.analysis_id)
            results['analysis'] = analysis
            
            # Get recommendations
            recommendations = QualityImprovement.objects.filter(
                source_analysis=analysis
            )
            results['recommendations'] = list(recommendations.values('improvement_id', 'title', 'priority'))
            
            # Auto-approve high-priority improvements
            for improvement in recommendations.filter(priority='critical'):
                self.approve_improvement(improvement.improvement_id)
                results['approved'].append(str(improvement.improvement_id))
            
            # Implement approved improvements
            approved_improvements = QualityImprovement.objects.filter(
                status='approved'
            )
            
            for improvement in approved_improvements:
                implementation = self.implement_improvement(improvement.improvement_id)
                results['implemented'].append({
                    'improvement_id': str(improvement.improvement_id),
                    'title': improvement.title,
                    'results': implementation.get('results', {}).get('message', 'Implemented')
                })
            
            return results
            
        except Exception as e:
            logger.exception(f"Error in quality improvement pipeline: {str(e)}")
            results['error'] = str(e)
            return results