# Multi-agent system for intelligent research assistance

from .base import BaseAgent, AgentOrchestrator
from .literature_agent import LiteratureAnalysisAgent
from .hypothesis_agent import HypothesisGeneratorAgent
from .protocol_agent import ProtocolDesignAgent
from .critique_agent import CriticalReviewAgent
from .contradiction_agent import ContradictionFinderAgent

__all__ = [
    'BaseAgent',
    'AgentOrchestrator',
    'LiteratureAnalysisAgent',
    'HypothesisGeneratorAgent',
    'ProtocolDesignAgent',
    'CriticalReviewAgent',
    'ContradictionFinderAgent'
]