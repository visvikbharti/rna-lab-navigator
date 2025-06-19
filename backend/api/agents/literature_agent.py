"""
Literature Analysis Agent - Synthesizes insights from multiple papers
"""

from typing import Dict, Any, List
from .base import BaseAgent
import json
import logging

logger = logging.getLogger(__name__)


class LiteratureAnalysisAgent(BaseAgent):
    """Agent specialized in analyzing and synthesizing literature."""
    
    def __init__(self):
        super().__init__(
            name="LiteratureAnalyst",
            role="a literature synthesis expert who identifies patterns, contradictions, and opportunities across multiple research papers",
            temperature=0.6
        )
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze papers and extract key insights."""
        papers = input_data.get('papers', [])
        research_question = input_data.get('question', '')
        
        if not papers:
            return {"error": "No papers provided for analysis"}
        
        # Prepare paper summaries
        paper_context = self._prepare_paper_context(papers)
        
        # Analyze for patterns
        patterns = self._find_patterns(paper_context, research_question)
        
        # Find contradictions
        contradictions = self._find_contradictions(paper_context)
        
        # Identify gaps
        gaps = self._identify_gaps(paper_context, research_question)
        
        # Generate synthesis
        synthesis = self._synthesize_findings(patterns, contradictions, gaps, research_question)
        
        return {
            "patterns": patterns,
            "contradictions": contradictions,
            "gaps": gaps,
            "synthesis": synthesis,
            "paper_count": len(papers)
        }
    
    def _prepare_paper_context(self, papers: List[Dict]) -> str:
        """Prepare a structured context from papers."""
        context_parts = []
        
        for i, paper in enumerate(papers[:10], 1):  # Limit to 10 papers
            context_parts.append(f"""
Paper {i}: {paper.get('title', 'Untitled')}
Authors: {paper.get('authors', 'Unknown')}
Year: {paper.get('year', 'N/A')}
Key Findings: {paper.get('abstract', '')[:500]}
Methods: {paper.get('methods', 'Not specified')}
""")
        
        return "\n---\n".join(context_parts)
    
    def _find_patterns(self, paper_context: str, research_question: str) -> List[Dict]:
        """Find patterns across papers."""
        prompt = f"""
Given these research papers and the question "{research_question}", identify:

1. Common methodologies used across papers
2. Recurring findings or conclusions
3. Shared limitations or challenges
4. Emerging trends in the field

Papers:
{paper_context}

Provide 3-5 key patterns with evidence from specific papers.
Format as JSON list with structure: [{{"pattern": "...", "evidence": ["paper1", "paper2"], "significance": "..."}}]
"""
        
        try:
            response = self.think(prompt)
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                patterns = json.loads(response[json_start:json_end])
                return patterns
        except Exception as e:
            logger.error(f"Pattern finding error: {e}")
        
        return []
    
    def _find_contradictions(self, paper_context: str) -> List[Dict]:
        """Find contradictions between papers."""
        prompt = f"""
Analyze these papers and identify any contradictions or conflicting findings:

{paper_context}

Look for:
1. Conflicting experimental results
2. Disagreements on mechanisms
3. Different conclusions from similar data
4. Methodological disputes

Format as JSON list: [{{"contradiction": "...", "paper1": "...", "paper2": "...", "implications": "..."}}]
"""
        
        try:
            response = self.think(prompt)
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                contradictions = json.loads(response[json_start:json_end])
                return contradictions
        except Exception as e:
            logger.error(f"Contradiction finding error: {e}")
        
        return []
    
    def _identify_gaps(self, paper_context: str, research_question: str) -> List[Dict]:
        """Identify research gaps."""
        prompt = f"""
Based on these papers and the research question "{research_question}", identify:

1. What questions remain unanswered?
2. What experiments haven't been done?
3. What populations/conditions haven't been studied?
4. What technical limitations need to be overcome?

Papers:
{paper_context}

Format as JSON list: [{{"gap": "...", "opportunity": "...", "approach": "..."}}]
"""
        
        try:
            response = self.think(prompt)
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                gaps = json.loads(response[json_start:json_end])
                return gaps
        except Exception as e:
            logger.error(f"Gap identification error: {e}")
        
        return []
    
    def _synthesize_findings(self, patterns: List[Dict], contradictions: List[Dict], 
                           gaps: List[Dict], research_question: str) -> Dict[str, Any]:
        """Synthesize all findings into actionable insights."""
        prompt = f"""
Synthesize these literature analysis findings for the research question: "{research_question}"

Patterns found: {json.dumps(patterns, indent=2)}
Contradictions: {json.dumps(contradictions, indent=2)}
Research gaps: {json.dumps(gaps, indent=2)}

Provide:
1. Overall state of the field (2-3 sentences)
2. Most promising research direction
3. Immediate actionable experiment
4. Long-term research program (3-5 year vision)
5. Collaboration opportunities

Be specific and actionable.
"""
        
        synthesis = self.think(prompt)
        
        return {
            "summary": synthesis,
            "actionable_insights": self._extract_actionable_insights(synthesis),
            "confidence": "high" if patterns else "medium"
        }
    
    def _extract_actionable_insights(self, synthesis: str) -> List[str]:
        """Extract specific actionable insights from synthesis."""
        # Simple extraction - in practice, could use more sophisticated NLP
        insights = []
        
        lines = synthesis.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['experiment', 'test', 'investigate', 'measure', 'analyze']):
                if len(line) > 20:  # Filter out short fragments
                    insights.append(line)
        
        return insights[:5]  # Top 5 actionable insights