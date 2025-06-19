"""
Knowledge Gap Intelligence API Views
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from django.utils import timezone

from .knowledge_gaps import KnowledgeGapAnalyzer
from .knowledge_graph import get_graph_service
from .serializers import (
    KnowledgeGapSerializer,
    ResearchOpportunitySerializer,
    GapAnalysisRequestSerializer
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def knowledge_gaps_list(request):
    """
    List all identified knowledge gaps.
    
    Query params:
    - gap_type: Filter by gap type (coverage, validation, question, combination)
    - domain: Filter by research domain
    - min_severity: Minimum severity level (low, medium, high)
    """
    analyzer = KnowledgeGapAnalyzer()
    
    # Get filter parameters
    gap_type = request.query_params.get('gap_type')
    domain = request.query_params.get('domain')
    min_severity = request.query_params.get('min_severity', 'low')
    
    # Cache key based on filters
    cache_key = f"knowledge_gaps:list:{gap_type}:{domain}:{min_severity}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        return Response(cached_result)
    
    all_gaps = []
    
    # Get coverage gaps
    if not gap_type or gap_type == 'coverage':
        coverage_analysis = analyzer.analyze_research_coverage(domain)
        if 'coverage_gaps' in coverage_analysis:
            for gap in coverage_analysis['coverage_gaps']:
                gap['gap_type'] = 'coverage'
                all_gaps.append(gap)
    
    # Get validation gaps
    if not gap_type or gap_type == 'validation':
        validation_gaps = analyzer.detect_missing_validations()
        for gap in validation_gaps:
            gap['gap_type'] = 'validation'
            gap['gap_severity'] = 'high' if gap['confidence'] > 0.7 else 'medium'
            all_gaps.append(gap)
    
    # Get unanswered questions
    if not gap_type or gap_type == 'question':
        questions = analyzer.find_unanswered_questions()
        for question in questions:
            all_gaps.append({
                'gap_type': 'question',
                'title': question['question'][:100] + '...' if len(question['question']) > 100 else question['question'],
                'description': question['context'],
                'gap_severity': 'medium',
                'source': question['source_paper'],
                'metadata': {
                    'question_type': question['question_type'],
                    'keywords': question['keywords'],
                    'approaches': question['potential_approaches']
                }
            })
    
    # Get unexplored combinations
    if not gap_type or gap_type == 'combination':
        combinations = analyzer.identify_unexplored_combinations()
        for combo in combinations[:10]:  # Limit to top 10
            all_gaps.append({
                'gap_type': 'combination',
                'title': f"Unexplored: {analyzer._format_combination_title(combo['combination'])}",
                'description': combo['rationale'],
                'gap_severity': 'high' if combo['impact_score'] > 0.7 else 'medium',
                'impact_score': combo['impact_score'],
                'metadata': {
                    'parameters': combo['combination'],
                    'related_papers': combo['related_papers']
                }
            })
    
    # Filter by severity
    severity_levels = {'low': 0, 'medium': 1, 'high': 2}
    min_level = severity_levels.get(min_severity, 0)
    
    filtered_gaps = [
        gap for gap in all_gaps 
        if severity_levels.get(gap.get('gap_severity', 'low'), 0) >= min_level
    ]
    
    # Sort by severity and impact
    filtered_gaps.sort(
        key=lambda x: (
            severity_levels.get(x.get('gap_severity', 'low'), 0),
            x.get('impact_score', 0.5)
        ),
        reverse=True
    )
    
    result = {
        'count': len(filtered_gaps),
        'gaps': filtered_gaps,
        'filters_applied': {
            'gap_type': gap_type,
            'domain': domain,
            'min_severity': min_severity
        },
        'generated_at': timezone.now().isoformat()
    }
    
    # Cache for 30 minutes
    cache.set(cache_key, result, 1800)
    
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_gaps(request):
    """
    Analyze knowledge gaps for a specific research area or topic.
    
    Request body:
    {
        "domain": "RNA editing",
        "analysis_type": "comprehensive",  # or "quick"
        "include_opportunities": true
    }
    """
    serializer = GapAnalysisRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    domain = serializer.validated_data['domain']
    analysis_type = serializer.validated_data.get('analysis_type', 'quick')
    include_opportunities = serializer.validated_data.get('include_opportunities', False)
    
    analyzer = KnowledgeGapAnalyzer()
    
    # Perform analysis based on type
    if analysis_type == 'comprehensive':
        # Full analysis
        coverage = analyzer.analyze_research_coverage(domain)
        combinations = analyzer.identify_unexplored_combinations()
        validations = analyzer.detect_missing_validations()
        questions = analyzer.find_unanswered_questions()
        evolution = analyzer.track_topic_evolution()
        
        result = {
            'domain': domain,
            'analysis_type': analysis_type,
            'coverage_analysis': coverage,
            'unexplored_combinations': combinations[:5],
            'missing_validations': validations[:5],
            'unanswered_questions': questions[:5],
            'topic_evolution': evolution,
            'summary': {
                'total_gaps_identified': (
                    len(coverage.get('coverage_gaps', [])) +
                    len(combinations) +
                    len(validations) +
                    len(questions)
                ),
                'coverage_score': coverage.get('coverage_score', 0),
                'high_priority_gaps': sum(
                    1 for gap in validations[:5] + combinations[:5]
                    if gap.get('confidence', gap.get('impact_score', 0)) > 0.7
                )
            }
        }
        
        if include_opportunities:
            opportunities = analyzer.suggest_research_opportunities()
            result['research_opportunities'] = opportunities
            
    else:
        # Quick analysis - just coverage and top gaps
        coverage = analyzer.analyze_research_coverage(domain)
        
        result = {
            'domain': domain,
            'analysis_type': analysis_type,
            'coverage_score': coverage.get('coverage_score', 0),
            'research_areas': coverage.get('research_areas', {}),
            'top_gaps': coverage.get('coverage_gaps', [])[:10],
            'summary': {
                'total_documents': coverage.get('total_documents', 0),
                'total_areas': len(coverage.get('research_areas', {}).get('areas', {}))
            }
        }
    
    result['analysis_completed_at'] = timezone.now().isoformat()
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def research_opportunities(request):
    """
    Get personalized research opportunity suggestions.
    
    Query params:
    - interests: Comma-separated list of research interests
    - limit: Number of opportunities to return (default: 10)
    """
    analyzer = KnowledgeGapAnalyzer()
    
    # Parse interests
    interests_param = request.query_params.get('interests', '')
    interests = [i.strip() for i in interests_param.split(',') if i.strip()] if interests_param else None
    
    limit = int(request.query_params.get('limit', 10))
    
    # Get opportunities
    opportunities = analyzer.suggest_research_opportunities(interests)[:limit]
    
    # Enhance opportunities with additional context
    enhanced_opportunities = []
    for opp in opportunities:
        enhanced = {
            **opp,
            'feasibility_score': _calculate_feasibility_score(opp),
            'estimated_timeline': _estimate_timeline(opp),
            'potential_collaborators': _suggest_collaborators(opp),
            'funding_opportunities': _suggest_funding(opp)
        }
        enhanced_opportunities.append(enhanced)
    
    result = {
        'count': len(enhanced_opportunities),
        'opportunities': enhanced_opportunities,
        'filters': {
            'interests': interests,
            'limit': limit
        },
        'personalized': interests is not None,
        'generated_at': timezone.now().isoformat()
    }
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def topic_evolution(request):
    """
    Get topic evolution analysis over time.
    
    Query params:
    - days: Time window in days (default: 365)
    - topic: Specific topic to track (optional)
    """
    analyzer = KnowledgeGapAnalyzer()
    
    days = int(request.query_params.get('days', 365))
    specific_topic = request.query_params.get('topic')
    
    # Get evolution analysis
    evolution = analyzer.track_topic_evolution(days)
    
    # Filter by specific topic if requested
    if specific_topic and 'timeline' in evolution:
        filtered_timeline = []
        for period in evolution['timeline']:
            period_topics = [
                t for t in period.get('topics', [])
                if specific_topic.lower() in t['term'].lower()
            ]
            if period_topics:
                filtered_period = {**period, 'topics': period_topics}
                filtered_timeline.append(filtered_period)
        
        evolution['timeline'] = filtered_timeline
        evolution['filtered_by'] = specific_topic
    
    # Add visualization-friendly data
    if 'timeline' in evolution:
        evolution['chart_data'] = _prepare_chart_data(evolution['timeline'])
    
    return Response(evolution)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gap_details(request, gap_id):
    """
    Get detailed information about a specific knowledge gap.
    
    This would typically fetch from a database, but for now
    we'll regenerate based on the gap type encoded in the ID.
    """
    # Parse gap type from ID (format: type_index)
    parts = gap_id.split('_')
    if len(parts) < 2:
        return Response(
            {'error': 'Invalid gap ID format'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    gap_type = parts[0]
    index = int(parts[1])
    
    analyzer = KnowledgeGapAnalyzer()
    
    # Fetch the specific gap
    if gap_type == 'combination':
        combinations = analyzer.identify_unexplored_combinations()
        if index < len(combinations):
            gap = combinations[index]
            detailed = {
                'id': gap_id,
                'type': 'unexplored_combination',
                'title': f"Explore {analyzer._format_combination_title(gap['combination'])}",
                'description': gap['rationale'],
                'impact_score': gap['impact_score'],
                'parameters': gap['combination'],
                'related_papers': gap['related_papers'],
                'suggested_experiments': _suggest_experiments(gap),
                'estimated_resources': analyzer._estimate_resources(gap),
                'potential_outcomes': _predict_outcomes(gap)
            }
            return Response(detailed)
            
    elif gap_type == 'validation':
        validations = analyzer.detect_missing_validations()
        if index < len(validations):
            gap = validations[index]
            detailed = {
                'id': gap_id,
                'type': 'missing_validation',
                'claim': gap['claim'],
                'source': gap['source_paper'],
                'confidence': gap['confidence'],
                'validation_methods': gap['potential_validation_methods'],
                'related_work': gap['related_work'],
                'priority': 'high' if gap['confidence'] > 0.7 else 'medium',
                'next_steps': _suggest_validation_steps(gap)
            }
            return Response(detailed)
            
    elif gap_type == 'question':
        questions = analyzer.find_unanswered_questions()
        if index < len(questions):
            gap = questions[index]
            detailed = {
                'id': gap_id,
                'type': 'unanswered_question',
                'question': gap['question'],
                'context': gap['context'],
                'source': gap['source_paper'],
                'question_type': gap['question_type'],
                'keywords': gap['keywords'],
                'potential_approaches': gap['potential_approaches'],
                'related_gaps': _find_related_gaps(gap, analyzer),
                'research_plan': _generate_research_plan(gap)
            }
            return Response(detailed)
    
    return Response(
        {'error': 'Gap not found'},
        status=status.HTTP_404_NOT_FOUND
    )


# Helper functions
def _calculate_feasibility_score(opportunity):
    """Calculate how feasible an opportunity is."""
    base_score = 0.5
    
    # Adjust based on difficulty
    difficulty_scores = {'low': 0.3, 'medium': 0.2, 'high': 0.1, 'varies': 0.15}
    base_score += difficulty_scores.get(opportunity.get('difficulty', 'medium'), 0.2)
    
    # Adjust based on resources
    resources = opportunity.get('resources_needed', [])
    if len(resources) <= 2:
        base_score += 0.2
    elif len(resources) <= 3:
        base_score += 0.1
    
    return min(base_score, 0.9)


def _estimate_timeline(opportunity):
    """Estimate timeline for research opportunity."""
    opp_type = opportunity.get('type', '')
    
    timelines = {
        'unexplored_combination': '3-6 months',
        'validation_needed': '2-4 months',
        'open_question': '6-12 months',
        'emerging_topic': '12-24 months'
    }
    
    return timelines.get(opp_type, '6-12 months')


def _suggest_collaborators(opportunity):
    """Suggest potential collaborators based on opportunity."""
    suggestions = []
    
    # Based on type and content
    if 'CRISPR' in str(opportunity):
        suggestions.append({'expertise': 'CRISPR specialist', 'reason': 'Technical expertise needed'})
    if 'clinical' in str(opportunity).lower():
        suggestions.append({'expertise': 'Clinical researcher', 'reason': 'Translation to practice'})
    if 'computational' in str(opportunity).lower():
        suggestions.append({'expertise': 'Bioinformatician', 'reason': 'Data analysis support'})
    
    return suggestions


def _suggest_funding(opportunity):
    """Suggest funding sources for opportunity."""
    sources = []
    
    impact = opportunity.get('impact_score', 0.5)
    
    if impact > 0.7:
        sources.append({'source': 'Major grants (NIH, NSF)', 'fit': 'High impact project'})
    else:
        sources.append({'source': 'Seed funding', 'fit': 'Exploratory research'})
    
    if opportunity.get('type') == 'emerging_topic':
        sources.append({'source': 'Innovation grants', 'fit': 'Novel research area'})
    
    return sources


def _prepare_chart_data(timeline):
    """Prepare timeline data for visualization."""
    chart_data = {
        'labels': [],
        'datasets': {}
    }
    
    # Collect all topics
    all_topics = set()
    for period in timeline:
        for topic in period.get('topics', []):
            all_topics.add(topic['term'])
    
    # Initialize datasets
    for topic in all_topics:
        chart_data['datasets'][topic] = []
    
    # Fill data
    for period in timeline:
        chart_data['labels'].append(period['period'])
        
        period_topics = {t['term']: t['score'] for t in period.get('topics', [])}
        
        for topic in all_topics:
            chart_data['datasets'][topic].append(period_topics.get(topic, 0))
    
    return chart_data


def _suggest_experiments(gap):
    """Suggest specific experiments for a gap."""
    experiments = []
    
    params = gap.get('combination', {})
    
    if 'cell_type' in params and 'technique' in params:
        experiments.append({
            'name': 'Cell-type specific validation',
            'description': f"Apply {params['technique']} to {params['cell_type']} cells",
            'duration': '2-3 weeks'
        })
    
    if 'temperature' in params:
        experiments.append({
            'name': 'Temperature optimization',
            'description': 'Test range around identified temperature',
            'duration': '1 week'
        })
    
    return experiments


def _predict_outcomes(gap):
    """Predict potential outcomes of addressing a gap."""
    outcomes = []
    
    impact = gap.get('impact_score', 0.5)
    
    if impact > 0.7:
        outcomes.append('Significant advancement in field understanding')
        outcomes.append('Potential for high-impact publication')
    
    if gap.get('type') == 'unexplored_combination':
        outcomes.append('Discovery of novel parameter dependencies')
        outcomes.append('Optimization of experimental protocols')
    
    return outcomes


def _suggest_validation_steps(gap):
    """Suggest step-by-step validation approach."""
    steps = []
    
    # General validation steps
    steps.append({
        'step': 1,
        'action': 'Literature review',
        'description': 'Comprehensive review of related validation attempts'
    })
    
    steps.append({
        'step': 2,
        'action': 'Experimental design',
        'description': 'Design experiments using suggested methods'
    })
    
    steps.append({
        'step': 3,
        'action': 'Pilot study',
        'description': 'Small-scale validation to test approach'
    })
    
    steps.append({
        'step': 4,
        'action': 'Full validation',
        'description': 'Complete experimental validation with controls'
    })
    
    return steps


def _find_related_gaps(gap, analyzer):
    """Find other gaps related to this one."""
    # This is simplified - in production would use more sophisticated matching
    related = []
    
    keywords = gap.get('keywords', [])
    
    # Check other questions
    other_questions = analyzer.find_unanswered_questions()
    for other in other_questions[:20]:
        if other != gap:
            # Check keyword overlap
            other_keywords = set(other.get('keywords', []))
            if len(set(keywords) & other_keywords) >= 2:
                related.append({
                    'type': 'related_question',
                    'title': other['question'][:100],
                    'similarity': 'high'
                })
    
    return related[:5]


def _generate_research_plan(gap):
    """Generate a research plan for addressing a gap."""
    plan = {
        'phases': [],
        'estimated_duration': '6-9 months',
        'key_milestones': []
    }
    
    # Phase 1: Background
    plan['phases'].append({
        'phase': 1,
        'name': 'Background Research',
        'duration': '1 month',
        'activities': [
            'Literature review',
            'Identify key papers',
            'Map current knowledge'
        ]
    })
    
    # Phase 2: Design
    plan['phases'].append({
        'phase': 2,
        'name': 'Experimental Design',
        'duration': '1 month',
        'activities': [
            'Develop hypotheses',
            'Design experiments',
            'Prepare protocols'
        ]
    })
    
    # Phase 3: Execution
    plan['phases'].append({
        'phase': 3,
        'name': 'Experimental Work',
        'duration': '3-4 months',
        'activities': [
            'Conduct experiments',
            'Collect data',
            'Iterative optimization'
        ]
    })
    
    # Phase 4: Analysis
    plan['phases'].append({
        'phase': 4,
        'name': 'Analysis and Reporting',
        'duration': '1-2 months',
        'activities': [
            'Data analysis',
            'Prepare manuscript',
            'Present findings'
        ]
    })
    
    # Milestones
    plan['key_milestones'] = [
        'Literature review complete',
        'Experimental design approved',
        'Initial results obtained',
        'Publication submitted'
    ]
    
    return plan


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detect_knowledge_gaps(request):
    """
    Detect knowledge gaps based on query or paper IDs.
    
    POST body:
    - query: Query string to analyze
    - paper_ids: List of paper IDs to analyze
    - threshold: Confidence threshold (default: 0.5)
    - gap_types: List of gap types to detect
    """
    serializer = GapAnalysisRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    analyzer = KnowledgeGapAnalyzer()
    
    # Cache key
    cache_key = f"gaps:detect:{data.get('query', '')}:{','.join(map(str, data.get('paper_ids', [])))}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        return Response(cached_result)
    
    gaps = []
    
    # Analyze based on query
    if data.get('query'):
        # Find unanswered questions related to query
        questions = analyzer.find_unanswered_questions()
        for q in questions:
            if data['query'].lower() in q['question'].lower():
                gaps.append({
                    'type': 'question',
                    'gap': q['question'],
                    'confidence': q.get('confidence', 0.7),
                    'severity': 'medium',
                    'keywords': q.get('keywords', [])
                })
    
    # Analyze based on papers
    if data.get('paper_ids'):
        # Get coverage gaps for papers
        coverage = analyzer.analyze_research_coverage()
        if 'coverage_gaps' in coverage:
            for gap in coverage['coverage_gaps']:
                gaps.append({
                    'type': 'coverage',
                    'gap': gap['gap'],
                    'confidence': gap.get('confidence', 0.6),
                    'severity': gap.get('severity', 'medium'),
                    'keywords': gap.get('keywords', [])
                })
    
    # Filter by threshold
    threshold = data.get('threshold', 0.5)
    gaps = [g for g in gaps if g['confidence'] >= threshold]
    
    # Filter by gap types if specified
    if data.get('gap_types'):
        gaps = [g for g in gaps if g['type'] in data['gap_types']]
    
    result = {
        'gaps': gaps[:20],  # Limit to 20 gaps
        'count': len(gaps),
        'query': data.get('query'),
        'threshold': threshold
    }
    
    # Cache for 30 minutes
    cache.set(cache_key, result, 1800)
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gap_analysis(request):
    """
    Get detailed gap analysis for a research area.
    
    Query params:
    - area: Research area to analyze
    """
    area = request.query_params.get('area', '')
    if not area:
        return Response(
            {'error': 'Research area parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    analyzer = KnowledgeGapAnalyzer()
    
    # Get comprehensive analysis
    coverage = analyzer.analyze_research_coverage(area)
    questions = analyzer.find_unanswered_questions()
    validation = analyzer.detect_validation_gaps()
    
    # Filter questions by area
    area_questions = []
    for q in questions:
        if area.lower() in q['question'].lower() or any(area.lower() in k.lower() for k in q.get('keywords', [])):
            area_questions.append(q)
    
    result = {
        'area': area,
        'analysis': {
            'coverage': coverage,
            'unanswered_questions': area_questions[:10],
            'validation_gaps': validation[:5],
            'summary': {
                'total_gaps': len(coverage.get('coverage_gaps', [])) + len(area_questions),
                'high_priority_gaps': sum(1 for g in coverage.get('coverage_gaps', []) if g.get('severity') == 'high'),
                'research_opportunity_score': min(100, len(area_questions) * 10)
            }
        },
        'timestamp': timezone.now().isoformat()
    }
    
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def suggest_research_questions(request):
    """
    Suggest research questions based on identified gaps.
    
    POST body:
    - gaps: List of gap objects
    - context: Additional context for question generation
    """
    gaps = request.data.get('gaps', [])
    context = request.data.get('context', '')
    
    if not gaps:
        return Response(
            {'error': 'Gaps list is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    suggestions = []
    
    for gap in gaps[:10]:  # Limit to 10 gaps
        # Generate questions based on gap type
        if gap.get('type') == 'coverage':
            questions = [
                f"What are the underlying mechanisms of {gap.get('gap', 'this phenomenon')}?",
                f"How does {gap.get('gap', 'this')} vary across different conditions?",
                f"What factors influence {gap.get('gap', 'this process')}?"
            ]
        elif gap.get('type') == 'validation':
            questions = [
                f"Can the findings about {gap.get('gap', 'this')} be replicated in other systems?",
                f"What are the boundary conditions for {gap.get('gap', 'these results')}?",
                f"How robust are the conclusions about {gap.get('gap', 'this phenomenon')}?"
            ]
        else:
            questions = [
                f"What is the current understanding of {gap.get('gap', 'this topic')}?",
                f"What methodologies can address {gap.get('gap', 'this question')}?",
                f"What are the implications of understanding {gap.get('gap', 'this')}?"
            ]
        
        suggestion = {
            'gap': gap,
            'suggested_questions': questions,
            'research_approach': _suggest_approach(gap),
            'priority': gap.get('severity', 'medium')
        }
        
        suggestions.append(suggestion)
    
    result = {
        'suggestions': suggestions,
        'count': len(suggestions),
        'context': context
    }
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def knowledge_gap_heatmap(request):
    """
    Get heatmap data for knowledge gaps across research areas.
    """
    analyzer = KnowledgeGapAnalyzer()
    
    # Get coverage analysis for multiple areas
    areas = ['RNA biology', 'CRISPR', 'Gene regulation', 'Epigenetics', 'Cell signaling']
    heatmap_data = []
    
    for area in areas:
        coverage = analyzer.analyze_research_coverage(area)
        gaps = coverage.get('coverage_gaps', [])
        
        area_data = {
            'area': area,
            'total_gaps': len(gaps),
            'severity_distribution': {
                'high': sum(1 for g in gaps if g.get('severity') == 'high'),
                'medium': sum(1 for g in gaps if g.get('severity') == 'medium'),
                'low': sum(1 for g in gaps if g.get('severity') == 'low')
            },
            'gap_types': {
                'coverage': sum(1 for g in gaps if g.get('type') == 'coverage'),
                'validation': sum(1 for g in gaps if g.get('type') == 'validation'),
                'question': sum(1 for g in gaps if g.get('type') == 'question')
            }
        }
        
        heatmap_data.append(area_data)
    
    result = {
        'heatmap': heatmap_data,
        'areas': areas,
        'timestamp': timezone.now().isoformat()
    }
    
    return Response(result)


def _suggest_approach(gap):
    """Suggest research approach for a gap."""
    approaches = {
        'coverage': [
            'Systematic literature review',
            'Experimental investigation',
            'Computational modeling'
        ],
        'validation': [
            'Replication study',
            'Multi-site validation',
            'Alternative methodology'
        ],
        'question': [
            'Hypothesis-driven research',
            'Exploratory investigation',
            'Interdisciplinary collaboration'
        ]
    }
    
    gap_type = gap.get('type', 'question')
    return approaches.get(gap_type, ['General investigation'])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cross_paper_insights(request):
    """
    Generate insights across multiple papers.
    
    POST body:
    - query: Query to focus insights on
    - paper_ids: List of paper IDs to analyze
    - insight_types: Types of insights to generate
    - min_confidence: Minimum confidence threshold
    """
    from .cross_paper_insights import CrossPaperInsightGenerator
    
    query = request.data.get('query', '')
    paper_ids = request.data.get('paper_ids', [])
    insight_types = request.data.get('insight_types')
    min_confidence = request.data.get('min_confidence', 0.6)
    
    if not query and not paper_ids:
        return Response(
            {'error': 'Either query or paper_ids is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    generator = CrossPaperInsightGenerator()
    
    # Generate insights
    insights = generator.generate_insights(
        query=query,
        paper_ids=paper_ids,
        insight_types=insight_types
    )
    
    # Filter by confidence
    filtered_insights = [
        i for i in insights 
        if i.get('confidence', 0) >= min_confidence
    ]
    
    # Sort by relevance
    filtered_insights.sort(
        key=lambda x: (x.get('relevance', 0), x.get('confidence', 0)),
        reverse=True
    )
    
    result = {
        'insights': filtered_insights[:20],  # Limit to 20
        'count': len(filtered_insights),
        'query': query,
        'paper_count': len(paper_ids),
        'min_confidence': min_confidence
    }
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def research_connections(request):
    """
    Get research connection graph.
    
    Query params:
    - query: Query to focus connections on
    - paper_ids: Comma-separated paper IDs
    - connection_types: Types of connections to include
    """
    from .cross_paper_insights import CrossPaperInsightGenerator
    
    query = request.query_params.get('query', '')
    paper_ids_param = request.query_params.get('paper_ids', '')
    paper_ids = [int(pid) for pid in paper_ids_param.split(',') if pid] if paper_ids_param else []
    connection_types = request.query_params.getlist('connection_types')
    
    generator = CrossPaperInsightGenerator()
    
    # Build connection graph
    connections = generator.build_connection_graph(
        query=query,
        paper_ids=paper_ids,
        connection_types=connection_types
    )
    
    result = {
        'nodes': connections.get('nodes', []),
        'edges': connections.get('edges', []),
        'statistics': {
            'total_nodes': len(connections.get('nodes', [])),
            'total_edges': len(connections.get('edges', [])),
            'connection_types': connections.get('connection_types', {})
        }
    }
    
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_connection(request):
    """
    Validate a research connection or insight.
    
    POST body:
    - insight: The insight object to validate
    """
    from .insight_validation import InsightValidator
    
    insight = request.data.get('insight')
    if not insight:
        return Response(
            {'error': 'Insight object is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validator = InsightValidator()
    validation_result = validator.validate_insight(insight)
    
    result = {
        'is_valid': validation_result.get('is_valid', False),
        'confidence': validation_result.get('confidence', 0),
        'validation_details': validation_result.get('details', {}),
        'suggestions': validation_result.get('suggestions', [])
    }
    
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rank_insights(request):
    """
    Rank insights by relevance and quality.
    
    POST body:
    - insights: List of insights to rank
    - user_query: User's original query
    - preferences: Ranking preferences
    """
    insights = request.data.get('insights', [])
    user_query = request.data.get('user_query', '')
    preferences = request.data.get('preferences', {})
    
    if not insights:
        return Response(
            {'error': 'Insights list is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Rank insights
    ranked_insights = []
    for insight in insights:
        score = 0
        
        # Relevance to query
        if user_query and user_query.lower() in str(insight).lower():
            score += 0.3
        
        # Confidence score
        score += insight.get('confidence', 0) * 0.4
        
        # Novelty score
        score += insight.get('novelty', 0.5) * 0.2
        
        # Impact score
        score += insight.get('impact', 0.5) * 0.1
        
        ranked_insight = {
            **insight,
            'ranking_score': score,
            'ranking_factors': {
                'relevance': 0.3 if user_query and user_query.lower() in str(insight).lower() else 0,
                'confidence': insight.get('confidence', 0),
                'novelty': insight.get('novelty', 0.5),
                'impact': insight.get('impact', 0.5)
            }
        }
        ranked_insights.append(ranked_insight)
    
    # Sort by ranking score
    ranked_insights.sort(key=lambda x: x['ranking_score'], reverse=True)
    
    result = {
        'ranked_insights': ranked_insights,
        'count': len(ranked_insights),
        'ranking_method': 'weighted_composite',
        'preferences': preferences
    }
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trending_connections(request):
    """
    Get trending research connections.
    """
    # This would normally analyze recent queries and insights
    # For now, return mock trending data
    
    trending = [
        {
            'connection': 'RNA modifications and disease',
            'trend_score': 0.92,
            'papers_count': 15,
            'recent_insights': 3,
            'growth_rate': '+23%'
        },
        {
            'connection': 'CRISPR and epigenetics',
            'trend_score': 0.87,
            'papers_count': 12,
            'recent_insights': 2,
            'growth_rate': '+18%'
        },
        {
            'connection': 'Non-coding RNA regulation',
            'trend_score': 0.81,
            'papers_count': 9,
            'recent_insights': 4,
            'growth_rate': '+15%'
        }
    ]
    
    result = {
        'trending': trending,
        'period': 'last_30_days',
        'timestamp': timezone.now().isoformat()
    }
    
    return Response(result)


# Knowledge Graph Views

@api_view(['GET'])
def knowledge_graph_stats(request):
    """Get overall knowledge graph statistics."""
    graph_service = get_graph_service()
    stats = graph_service.get_graph_stats()
    
    return Response({
        'status': 'success',
        'data': stats
    })


@api_view(['GET'])
def graph_search(request):
    """Search nodes in the knowledge graph."""
    query = request.query_params.get('q', '')
    limit = int(request.query_params.get('limit', 10))
    
    if not query:
        return Response({
            'error': 'Query parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    graph_service = get_graph_service()
    results = graph_service.search_nodes(query, limit)
    
    return Response({
        'status': 'success',
        'query': query,
        'results': results,
        'count': len(results)
    })


@api_view(['GET'])
def graph_node_detail(request, node_id):
    """Get detailed information about a specific node."""
    graph_service = get_graph_service()
    
    if node_id not in graph_service.graph:
        return Response({
            'error': 'Node not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    node_attrs = graph_service.graph.nodes[node_id]
    connections = graph_service.get_node_connections(node_id)
    
    return Response({
        'status': 'success',
        'node': {
            'id': node_id,
            'attributes': node_attrs,
            'connections': connections,
            'degree': graph_service.graph.degree(node_id)
        }
    })


@api_view(['GET'])
def graph_suggestions(request, node_id):
    """Get connection suggestions for a specific node."""
    graph_service = get_graph_service()
    
    if node_id not in graph_service.graph:
        return Response({
            'error': 'Node not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    limit = int(request.query_params.get('limit', 5))
    suggestions = graph_service.suggest_connections(node_id, limit)
    
    return Response({
        'status': 'success',
        'node_id': node_id,
        'suggestions': suggestions
    })


@api_view(['GET'])
def graph_export(request):
    """Export the knowledge graph for visualization."""
    graph_service = get_graph_service()
    
    # Get optional filters
    center_node = request.query_params.get('center')
    depth = int(request.query_params.get('depth', 0))
    
    if center_node and depth > 0:
        # Export subgraph
        subgraph = graph_service.get_subgraph(center_node, depth)
        # Convert subgraph to exportable format
        # This would need implementation in the graph service
        data = graph_service.export_for_visualization()  # Simplified for now
    else:
        # Export full graph
        data = graph_service.export_for_visualization()
    
    return Response({
        'status': 'success',
        'data': data
    })