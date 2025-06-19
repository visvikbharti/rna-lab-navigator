"""
Experiment Mapping API Views
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import logging
import asyncio
from datetime import datetime

from .mapping_service import (
    get_experiment_mapping_service,
    ExperimentData,
    ExperimentalFactor,
    ExperimentRelationship
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def map_experiments(request):
    """
    Map and analyze a series of experiments
    
    POST /api/experiments/map/
    {
        "experiments": [
            {
                "experiment_id": "exp001",
                "experiment_type": "IVC assay",
                "target_locus": "AAVS1",
                "variables": {
                    "cas_variant": "SpCas9",
                    "guide_rna": "sgRNA-1",
                    "pam": "NGG"
                },
                "conditions": {
                    "temperature": 37,
                    "incubation_time": "48h",
                    "cell_type": "HEK293T"
                },
                "outcomes": {
                    "cleavage_efficiency": 0.85,
                    "off_target_rate": 0.02
                },
                "success_metrics": {
                    "efficiency": 0.85,
                    "specificity": 0.98
                },
                "researcher": "Dr. Smith",
                "date_performed": "2024-01-15"
            },
            {
                "experiment_id": "exp002",
                "experiment_type": "IVC assay",
                "target_locus": "AAVS1",
                "variables": {
                    "cas_variant": "FnCas9",
                    "guide_rna": "sgRNA-1",
                    "pam": "NGG"
                },
                "conditions": {
                    "temperature": 37,
                    "incubation_time": "48h",
                    "cell_type": "HEK293T"
                },
                "outcomes": {
                    "cleavage_efficiency": 0.92,
                    "off_target_rate": 0.01
                },
                "success_metrics": {
                    "efficiency": 0.92,
                    "specificity": 0.99
                },
                "researcher": "Dr. Smith",
                "date_performed": "2024-01-20"
            }
        ],
        "analysis_focus": "variant comparison"
    }
    """
    
    experiments_data = request.data.get('experiments', [])
    analysis_focus = request.data.get('analysis_focus')
    
    if not experiments_data:
        return Response(
            {'error': 'No experiments provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Convert to ExperimentData objects
        experiments = []
        for exp_data in experiments_data:
            # Parse date if provided
            date_performed = None
            if exp_data.get('date_performed'):
                try:
                    date_performed = datetime.fromisoformat(exp_data['date_performed'])
                except:
                    date_performed = None
            
            experiment = ExperimentData(
                experiment_id=exp_data.get('experiment_id', ''),
                experiment_type=exp_data.get('experiment_type', ''),
                target_locus=exp_data.get('target_locus', ''),
                variables=exp_data.get('variables', {}),
                conditions=exp_data.get('conditions', {}),
                protocol_id=exp_data.get('protocol_id'),
                outcomes=exp_data.get('outcomes', {}),
                success_metrics=exp_data.get('success_metrics', {}),
                researcher=exp_data.get('researcher'),
                date_performed=date_performed,
                notes=exp_data.get('notes')
            )
            experiments.append(experiment)
        
        # Get mapping service
        mapping_service = get_experiment_mapping_service()
        
        # Run async analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            mapping_service.map_experiment_series(
                experiments=experiments,
                analysis_focus=analysis_focus
            )
        )
        
        loop.close()
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in experiment mapping: {str(e)}")
        return Response(
            {'error': f'Failed to map experiments: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_single_experiment(request):
    """
    Analyze a single experiment in context of existing knowledge
    
    POST /api/experiments/analyze-single/
    {
        "experiment": {
            "experiment_id": "exp003",
            "experiment_type": "CRISPR screen",
            "target_locus": "multiple",
            "variables": {...},
            "conditions": {...},
            "outcomes": {...}
        },
        "compare_with": ["exp001", "exp002"]  // Optional experiment IDs to compare
    }
    """
    
    experiment_data = request.data.get('experiment')
    compare_with_ids = request.data.get('compare_with', [])
    
    if not experiment_data:
        return Response(
            {'error': 'Experiment data required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Convert to ExperimentData
        experiment = ExperimentData(
            experiment_id=experiment_data.get('experiment_id', ''),
            experiment_type=experiment_data.get('experiment_type', ''),
            target_locus=experiment_data.get('target_locus', ''),
            variables=experiment_data.get('variables', {}),
            conditions=experiment_data.get('conditions', {}),
            outcomes=experiment_data.get('outcomes', {}),
            success_metrics=experiment_data.get('success_metrics', {})
        )
        
        # For now, analyze as single experiment series
        mapping_service = get_experiment_mapping_service()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            mapping_service.map_experiment_series(
                experiments=[experiment],
                analysis_focus="single experiment analysis"
            )
        )
        
        loop.close()
        
        # Add comparison note if requested
        if compare_with_ids:
            result['comparison_note'] = f"Comparison with {compare_with_ids} requires fetching those experiments"
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error analyzing experiment: {str(e)}")
        return Response(
            {'error': f'Failed to analyze experiment: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def experiment_mapping_status(request):
    """
    Get the status of experiment mapping features
    
    GET /api/experiments/status/
    """
    return Response({
        'experiment_mapping': {
            'enabled': True,
            'features': {
                'knowledge_graph_generation': True,
                'factor_analysis': True,
                'pattern_detection': True,
                'confounding_identification': True,
                'ai_recommendations': True,
                'visualization_ready': True
            },
            'supported_analyses': [
                'variant_comparison',
                'protocol_optimization',
                'time_series_analysis',
                'factor_influence_mapping'
            ],
            'visualization_types': [
                'force_directed_graph',
                'factor_influence_chart',
                'success_timeline',
                'pattern_summary'
            ]
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def quick_factor_analysis(request):
    """
    Quick analysis of factors from experiment data
    
    POST /api/experiments/quick-factor-analysis/
    {
        "experiments": [...],  // Same format as map_experiments
        "target_factor": "cas_variant"  // Optional specific factor to analyze
    }
    """
    
    experiments_data = request.data.get('experiments', [])
    target_factor = request.data.get('target_factor')
    
    if not experiments_data:
        return Response(
            {'error': 'No experiments provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Quick factor extraction without full mapping
        factors = {}
        
        for exp_data in experiments_data:
            # Extract all factors
            for key, value in exp_data.get('variables', {}).items():
                if key not in factors:
                    factors[key] = {
                        'values': [],
                        'outcomes': []
                    }
                factors[key]['values'].append(value)
                
                # Add average outcome
                success_metrics = exp_data.get('success_metrics', {})
                if success_metrics:
                    avg_success = sum(success_metrics.values()) / len(success_metrics)
                    factors[key]['outcomes'].append(avg_success)
            
            # Also check conditions
            for key, value in exp_data.get('conditions', {}).items():
                if key not in factors:
                    factors[key] = {
                        'values': [],
                        'outcomes': []
                    }
                factors[key]['values'].append(value)
                
                success_metrics = exp_data.get('success_metrics', {})
                if success_metrics:
                    avg_success = sum(success_metrics.values()) / len(success_metrics)
                    factors[key]['outcomes'].append(avg_success)
        
        # Calculate factor statistics
        factor_analysis = {}
        for factor_name, data in factors.items():
            unique_values = list(set(data['values']))
            
            # Calculate average outcome per value
            value_outcomes = {}
            for val, outcome in zip(data['values'], data['outcomes']):
                if val not in value_outcomes:
                    value_outcomes[val] = []
                value_outcomes[val].append(outcome)
            
            avg_outcomes = {
                val: sum(outcomes) / len(outcomes) 
                for val, outcomes in value_outcomes.items()
            }
            
            factor_analysis[factor_name] = {
                'unique_values': unique_values,
                'value_count': len(unique_values),
                'is_variable': len(unique_values) > 1,
                'average_outcomes': avg_outcomes,
                'best_value': max(avg_outcomes.items(), key=lambda x: x[1])[0] if avg_outcomes else None
            }
        
        # Focus on target factor if specified
        if target_factor and target_factor in factor_analysis:
            result = {
                'target_factor': target_factor,
                'analysis': factor_analysis[target_factor],
                'other_factors': {k: v for k, v in factor_analysis.items() if k != target_factor}
            }
        else:
            result = {
                'all_factors': factor_analysis,
                'variable_factors': {k: v for k, v in factor_analysis.items() if v['is_variable']}
            }
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in quick factor analysis: {str(e)}")
        return Response(
            {'error': f'Failed to analyze factors: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )