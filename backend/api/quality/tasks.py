"""
Celery tasks for the quality improvement pipeline.
"""

import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .services import QualityImprovementService

logger = logging.getLogger(__name__)


@shared_task
def run_quality_analysis_task(analysis_id):
    """
    Task to run a quality analysis.
    
    Args:
        analysis_id (str): ID of the analysis to run
    """
    try:
        service = QualityImprovementService()
        analysis = service.run_quality_analysis(analysis_id)
        
        logger.info(f"Quality analysis {analysis_id} completed: {analysis.name}")
        return str(analysis_id)
    except Exception as e:
        logger.exception(f"Error running quality analysis {analysis_id}: {str(e)}")
        raise


@shared_task
def generate_and_run_quality_analysis_task(name=None, analysis_type='general', days_lookback=30):
    """
    Task to generate and run a quality analysis.
    
    Args:
        name (str, optional): Name for the analysis
        analysis_type (str): Type of analysis to run
        days_lookback (int): Number of days to analyze
        
    Returns:
        str: ID of the created analysis
    """
    try:
        # Use a default name if none provided
        if not name:
            name = f"Scheduled Analysis - {timezone.now().strftime('%Y-%m-%d')}"
            
        service = QualityImprovementService()
        
        # Generate the analysis
        analysis = service.generate_quality_analysis(
            name=name,
            analysis_type=analysis_type,
            days_lookback=days_lookback
        )
        
        # Run the analysis
        analysis = service.run_quality_analysis(analysis.analysis_id)
        
        logger.info(f"Generated and ran quality analysis: {analysis.name}")
        return str(analysis.analysis_id)
    except Exception as e:
        logger.exception(f"Error generating and running quality analysis: {str(e)}")
        raise


@shared_task
def implement_approved_improvements_task():
    """
    Task to implement all approved quality improvements.
    
    Returns:
        int: Number of improvements implemented
    """
    try:
        from .models import QualityImprovement
        
        service = QualityImprovementService()
        count = 0
        
        # Get all approved improvements
        approved_improvements = QualityImprovement.objects.filter(status='approved')
        
        for improvement in approved_improvements:
            try:
                service.implement_improvement(improvement.improvement_id)
                count += 1
                logger.info(f"Implemented improvement: {improvement.title}")
            except Exception as e:
                logger.exception(f"Error implementing improvement {improvement.improvement_id}: {str(e)}")
        
        return count
    except Exception as e:
        logger.exception(f"Error implementing approved improvements: {str(e)}")
        raise


@shared_task
def auto_approve_priority_improvements_task():
    """
    Task to automatically approve high-priority quality improvements.
    
    Returns:
        int: Number of improvements approved
    """
    try:
        from .models import QualityImprovement
        
        service = QualityImprovementService()
        count = 0
        
        # Get critical priority improvements with proposed status
        priority_improvements = QualityImprovement.objects.filter(
            status='proposed',
            priority='critical'
        )
        
        for improvement in priority_improvements:
            try:
                service.approve_improvement(improvement.improvement_id)
                count += 1
                logger.info(f"Auto-approved improvement: {improvement.title}")
            except Exception as e:
                logger.exception(f"Error auto-approving improvement {improvement.improvement_id}: {str(e)}")
        
        return count
    except Exception as e:
        logger.exception(f"Error auto-approving priority improvements: {str(e)}")
        raise


@shared_task
def run_complete_quality_pipeline_task():
    """
    Task to run the complete quality improvement pipeline.
    
    This includes:
    1. Generating a new quality analysis
    2. Generating improvement recommendations
    3. Auto-approving high-priority improvements
    4. Implementing approved improvements
    
    Returns:
        dict: Results of the pipeline run
    """
    try:
        service = QualityImprovementService()
        results = service.run_quality_improvement_pipeline()
        
        logger.info(f"Quality pipeline ran successfully. Analysis: {results.get('analysis')}")
        logger.info(f"Generated {len(results.get('recommendations', []))} recommendations")
        logger.info(f"Auto-approved {len(results.get('approved', []))} improvements")
        logger.info(f"Implemented {len(results.get('implemented', []))} improvements")
        
        return results
    except Exception as e:
        logger.exception(f"Error running quality pipeline: {str(e)}")
        raise