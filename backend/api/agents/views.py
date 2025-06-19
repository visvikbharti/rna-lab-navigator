"""
API views for multi-agent research system
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
import logging
import json
from typing import Dict, Any, List

from .base import AgentOrchestrator
from .literature_agent import LiteratureAnalysisAgent
from .hypothesis_agent import HypothesisGeneratorAgent
from .protocol_agent import ProtocolDesignAgent
from .critique_agent import CriticalReviewAgent
from .contradiction_agent import ContradictionFinderAgent

logger = logging.getLogger(__name__)


@api_view(['POST'])
def analyze_literature(request):
    """
    Analyze multiple papers to find patterns, contradictions, and gaps.
    """
    try:
        papers = request.data.get('papers', [])
        research_question = request.data.get('question', '')
        
        if not papers:
            return Response(
                {"error": "No papers provided for analysis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize agent
        literature_agent = LiteratureAnalysisAgent()
        
        # Perform analysis
        analysis = literature_agent.process({
            'papers': papers,
            'question': research_question
        })
        
        return Response({
            'success': True,
            'analysis': analysis
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Literature analysis error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def generate_hypothesis(request):
    """
    Generate novel hypotheses based on research gaps and patterns.
    """
    try:
        gaps = request.data.get('gaps', [])
        patterns = request.data.get('patterns', [])
        contradictions = request.data.get('contradictions', [])
        domain_context = request.data.get('domain', 'RNA biology')
        
        # Initialize agent
        hypothesis_agent = HypothesisGeneratorAgent()
        
        # Generate hypotheses
        hypotheses = hypothesis_agent.process({
            'gaps': gaps,
            'patterns': patterns,
            'contradictions': contradictions,
            'domain_context': domain_context
        })
        
        return Response({
            'success': True,
            'hypotheses': hypotheses
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Hypothesis generation error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def design_protocol(request):
    """
    Design a complete experimental protocol for a hypothesis.
    """
    try:
        hypothesis = request.data.get('hypothesis', '')
        constraints = request.data.get('constraints', {})
        existing_methods = request.data.get('existing_methods', [])
        
        if not hypothesis:
            return Response(
                {"error": "No hypothesis provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize agent
        protocol_agent = ProtocolDesignAgent()
        
        # Design protocol
        protocol = protocol_agent.process({
            'hypothesis': hypothesis,
            'constraints': constraints,
            'existing_methods': existing_methods
        })
        
        return Response({
            'success': True,
            'protocol': protocol
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Protocol design error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def critique_research(request):
    """
    Critically review a hypothesis, protocol, or analysis.
    """
    try:
        review_type = request.data.get('type', 'general')
        content = request.data.get('content', '')
        context = request.data.get('context', {})
        
        if not content:
            return Response(
                {"error": "No content provided for review"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize agent
        critique_agent = CriticalReviewAgent()
        
        # Perform critique
        critique = critique_agent.process({
            'type': review_type,
            'content': content,
            'context': context
        })
        
        return Response({
            'success': True,
            'critique': critique
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Critique error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def find_contradictions(request):
    """
    Find contradictions across multiple papers.
    """
    try:
        papers = request.data.get('papers', [])
        focus_area = request.data.get('focus_area', '')
        depth = request.data.get('depth', 'standard')
        
        if len(papers) < 2:
            return Response(
                {"error": "Need at least 2 papers to find contradictions"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize agent
        contradiction_agent = ContradictionFinderAgent()
        
        # Find contradictions
        contradictions = contradiction_agent.process({
            'papers': papers,
            'focus_area': focus_area,
            'depth': depth
        })
        
        return Response({
            'success': True,
            'contradictions': contradictions
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Contradiction finding error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def orchestrate_research(request):
    """
    Orchestrate multiple agents for complex research workflows.
    
    Example workflow types:
    - 'full_analysis': Literature → Contradictions → Gaps → Hypotheses → Protocols
    - 'hypothesis_to_protocol': Hypothesis → Critique → Protocol → Validation
    - 'paper_synthesis': Papers → Analysis → Contradictions → Resolution
    """
    try:
        workflow_type = request.data.get('workflow', 'full_analysis')
        input_data = request.data.get('input', {})
        
        # Initialize orchestrator and agents
        orchestrator = AgentOrchestrator()
        
        # Register agents
        orchestrator.register_agent(LiteratureAnalysisAgent())
        orchestrator.register_agent(HypothesisGeneratorAgent())
        orchestrator.register_agent(ProtocolDesignAgent())
        orchestrator.register_agent(CriticalReviewAgent())
        orchestrator.register_agent(ContradictionFinderAgent())
        
        # Define workflow based on type
        if workflow_type == 'full_analysis':
            workflow = [
                {"agent": "LiteratureAnalyst", "action": "process"},
                {"agent": "ContradictionFinder", "action": "process"},
                {"agent": "HypothesisGenerator", "action": "process"},
                {"agent": "CriticalReviewer", "action": "process"},
                {"agent": "ProtocolDesigner", "action": "process"}
            ]
        elif workflow_type == 'hypothesis_to_protocol':
            workflow = [
                {"agent": "CriticalReviewer", "action": "process"},
                {"agent": "ProtocolDesigner", "action": "process"},
                {"agent": "CriticalReviewer", "action": "process"}  # Review the protocol
            ]
        elif workflow_type == 'paper_synthesis':
            workflow = [
                {"agent": "LiteratureAnalyst", "action": "process"},
                {"agent": "ContradictionFinder", "action": "process"},
                {"agent": "HypothesisGenerator", "action": "process"}
            ]
        else:
            # Custom workflow
            workflow = request.data.get('custom_workflow', [])
        
        # Execute workflow
        results = orchestrator.execute_workflow(workflow, input_data)
        
        # Synthesize insights
        synthesis = orchestrator.synthesize_insights(results)
        
        return Response({
            'success': True,
            'workflow_type': workflow_type,
            'results': results,
            'synthesis': synthesis
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Orchestration error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def cross_paper_analysis(request):
    """
    Perform comprehensive cross-paper analysis to generate new research directions.
    """
    try:
        papers = request.data.get('papers', [])
        research_area = request.data.get('area', '')
        
        if not papers:
            return Response(
                {"error": "No papers provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator()
        
        # Register all agents
        literature_agent = LiteratureAnalysisAgent()
        contradiction_agent = ContradictionFinderAgent()
        hypothesis_agent = HypothesisGeneratorAgent()
        
        orchestrator.register_agent(literature_agent)
        orchestrator.register_agent(contradiction_agent)
        orchestrator.register_agent(hypothesis_agent)
        
        # Step 1: Analyze literature
        lit_analysis = literature_agent.process({
            'papers': papers,
            'question': f"What are the key findings in {research_area}?"
        })
        
        # Step 2: Find contradictions
        contradictions = contradiction_agent.process({
            'papers': papers,
            'focus_area': research_area,
            'depth': 'deep'
        })
        
        # Step 3: Generate hypotheses from both gaps and contradictions
        hypotheses = hypothesis_agent.process({
            'gaps': lit_analysis.get('gaps', []),
            'patterns': lit_analysis.get('patterns', []),
            'contradictions': contradictions.get('contradictions', []),
            'domain_context': research_area
        })
        
        # Create comprehensive report
        report = {
            'summary': f"Analyzed {len(papers)} papers in {research_area}",
            'key_patterns': lit_analysis.get('patterns', [])[:5],
            'major_contradictions': contradictions.get('contradictions', [])[:5],
            'research_gaps': lit_analysis.get('gaps', [])[:5],
            'novel_hypotheses': hypotheses.get('top_hypotheses', [])[:5],
            'next_steps': _generate_next_steps(lit_analysis, contradictions, hypotheses)
        }
        
        return Response({
            'success': True,
            'report': report,
            'detailed_results': {
                'literature_analysis': lit_analysis,
                'contradictions': contradictions,
                'hypotheses': hypotheses
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Cross-paper analysis error: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _generate_next_steps(lit_analysis: Dict, contradictions: Dict, hypotheses: Dict) -> List[str]:
    """Generate actionable next steps from analysis."""
    next_steps = []
    
    # Based on contradictions
    if contradictions.get('contradictions'):
        next_steps.append("Design experiments to resolve key contradictions")
    
    # Based on gaps
    if lit_analysis.get('gaps'):
        next_steps.append("Initiate studies to address identified research gaps")
    
    # Based on hypotheses
    if hypotheses.get('top_hypotheses'):
        next_steps.append("Develop protocols to test top-ranked hypotheses")
    
    # Based on patterns
    if lit_analysis.get('patterns'):
        next_steps.append("Validate emerging patterns with targeted experiments")
    
    # Always include
    next_steps.append("Share findings with research team for collaborative planning")
    
    return next_steps[:5]