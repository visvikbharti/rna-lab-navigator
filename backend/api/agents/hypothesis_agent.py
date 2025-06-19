"""
Hypothesis Generator Agent - Creates novel research hypotheses from gaps and contradictions
"""

from typing import Dict, Any, List
from .base import BaseAgent
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class HypothesisGeneratorAgent(BaseAgent):
    """Agent specialized in generating testable hypotheses."""
    
    def __init__(self):
        super().__init__(
            name="HypothesisGenerator",
            role="a creative scientist who generates novel, testable hypotheses by connecting disparate findings and identifying unexplored territories",
            temperature=0.8  # Higher temperature for creativity
        )
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hypotheses based on gaps and patterns."""
        gaps = input_data.get('gaps', [])
        patterns = input_data.get('patterns', [])
        contradictions = input_data.get('contradictions', [])
        domain_context = input_data.get('domain_context', '')
        
        # Generate different types of hypotheses
        mechanistic = self._generate_mechanistic_hypotheses(patterns, gaps, domain_context)
        resolution = self._generate_resolution_hypotheses(contradictions, domain_context)
        bridging = self._generate_bridging_hypotheses(gaps, patterns, domain_context)
        novel = self._generate_novel_hypotheses(patterns, gaps, contradictions, domain_context)
        
        # Rank hypotheses
        all_hypotheses = mechanistic + resolution + bridging + novel
        ranked = self._rank_hypotheses(all_hypotheses)
        
        return {
            "mechanistic_hypotheses": mechanistic,
            "resolution_hypotheses": resolution,
            "bridging_hypotheses": bridging,
            "novel_hypotheses": novel,
            "top_hypotheses": ranked[:5],
            "total_generated": len(all_hypotheses)
        }
    
    def _generate_mechanistic_hypotheses(self, patterns: List[Dict], gaps: List[Dict], 
                                       context: str) -> List[Dict]:
        """Generate hypotheses about mechanisms."""
        prompt = f"""
Based on these patterns and gaps in {context} research:

Patterns: {json.dumps(patterns, indent=2)}
Gaps: {json.dumps(gaps, indent=2)}

Generate 3 mechanistic hypotheses that explain HOW something works.
Each hypothesis should:
1. Build on existing patterns
2. Address a specific gap
3. Propose a testable mechanism
4. Be falsifiable

Format each as:
{{
    "hypothesis": "If X mechanism operates, then Y will occur when Z conditions are met",
    "rationale": "Based on pattern A and gap B...",
    "key_experiment": "To test this, we would...",
    "expected_outcome": "We expect to see...",
    "alternative": "If false, it suggests..."
}}
"""
        
        try:
            response = self.think(prompt)
            # Parse response to extract hypotheses
            hypotheses = self._parse_hypothesis_response(response)
            for h in hypotheses:
                h['type'] = 'mechanistic'
                h['timestamp'] = datetime.now().isoformat()
            return hypotheses
        except Exception as e:
            logger.error(f"Mechanistic hypothesis generation error: {e}")
            return []
    
    def _generate_resolution_hypotheses(self, contradictions: List[Dict], context: str) -> List[Dict]:
        """Generate hypotheses that resolve contradictions."""
        if not contradictions:
            return []
        
        prompt = f"""
These contradictions exist in {context} research:

{json.dumps(contradictions, indent=2)}

Generate hypotheses that could resolve these contradictions.
Consider:
1. Hidden variables that explain both results
2. Context-dependent effects
3. Methodological differences
4. Threshold or dose effects

Format as testable hypotheses with same structure as before.
"""
        
        try:
            response = self.think(prompt)
            hypotheses = self._parse_hypothesis_response(response)
            for h in hypotheses:
                h['type'] = 'resolution'
                h['timestamp'] = datetime.now().isoformat()
            return hypotheses
        except Exception as e:
            logger.error(f"Resolution hypothesis generation error: {e}")
            return []
    
    def _generate_bridging_hypotheses(self, gaps: List[Dict], patterns: List[Dict], 
                                    context: str) -> List[Dict]:
        """Generate hypotheses that bridge different areas."""
        prompt = f"""
In {context} research, can you connect insights from different areas?

Current gaps: {json.dumps(gaps, indent=2)}
Known patterns: {json.dumps(patterns, indent=2)}

Generate "bridging" hypotheses that:
1. Connect findings from different subfields
2. Apply methods from one area to problems in another
3. Suggest unexplored combinations
4. Cross disciplinary boundaries

Focus on high-impact connections that haven't been explored.
"""
        
        try:
            response = self.think(prompt)
            hypotheses = self._parse_hypothesis_response(response)
            for h in hypotheses:
                h['type'] = 'bridging'
                h['timestamp'] = datetime.now().isoformat()
            return hypotheses
        except Exception as e:
            logger.error(f"Bridging hypothesis generation error: {e}")
            return []
    
    def _generate_novel_hypotheses(self, patterns: List[Dict], gaps: List[Dict], 
                                  contradictions: List[Dict], context: str) -> List[Dict]:
        """Generate completely novel hypotheses."""
        prompt = f"""
Given the current state of {context} research, generate BOLD, NOVEL hypotheses.

Current knowledge:
- Patterns: {len(patterns)} identified
- Gaps: {len(gaps)} found
- Contradictions: {len(contradictions)} noted

Think outside the box:
1. Challenge fundamental assumptions
2. Propose radical new mechanisms
3. Suggest paradigm shifts
4. Combine ideas in unexpected ways

These should be high-risk, high-reward hypotheses that could transform the field if true.
Make them specific and testable, not just philosophical.
"""
        
        try:
            response = self.think(prompt)
            hypotheses = self._parse_hypothesis_response(response)
            for h in hypotheses:
                h['type'] = 'novel'
                h['risk_level'] = 'high'
                h['potential_impact'] = 'transformative'
                h['timestamp'] = datetime.now().isoformat()
            return hypotheses
        except Exception as e:
            logger.error(f"Novel hypothesis generation error: {e}")
            return []
    
    def _parse_hypothesis_response(self, response: str) -> List[Dict]:
        """Parse hypothesis from LLM response."""
        hypotheses = []
        
        # Try to find JSON blocks
        import re
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                # Clean up the match
                clean_match = match.replace('\n', ' ').strip()
                hypothesis = json.loads(clean_match)
                
                # Ensure required fields
                if 'hypothesis' in hypothesis:
                    hypotheses.append(hypothesis)
            except json.JSONDecodeError:
                # Try manual parsing as fallback
                hypothesis = self._manual_parse_hypothesis(match)
                if hypothesis:
                    hypotheses.append(hypothesis)
        
        # If no JSON found, try to extract from text
        if not hypotheses:
            hypotheses = self._extract_hypotheses_from_text(response)
        
        return hypotheses
    
    def _manual_parse_hypothesis(self, text: str) -> Dict[str, Any]:
        """Manually parse hypothesis from text."""
        hypothesis = {}
        
        # Look for key patterns
        patterns = {
            'hypothesis': r'hypothesis["\s:]+([^"]+)',
            'rationale': r'rationale["\s:]+([^"]+)',
            'key_experiment': r'key_experiment["\s:]+([^"]+)',
            'expected_outcome': r'expected_outcome["\s:]+([^"]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hypothesis[key] = match.group(1).strip()
        
        return hypothesis if 'hypothesis' in hypothesis else None
    
    def _extract_hypotheses_from_text(self, text: str) -> List[Dict]:
        """Extract hypotheses from plain text."""
        hypotheses = []
        
        # Split by common delimiters
        sections = re.split(r'(?:Hypothesis \d+:|^\d+\.|^-)', text)
        
        for section in sections:
            if len(section) > 50:  # Minimum length for a hypothesis
                hypothesis = {
                    'hypothesis': section.strip()[:200],
                    'rationale': 'Extracted from text analysis',
                    'type': 'extracted'
                }
                hypotheses.append(hypothesis)
        
        return hypotheses[:5]  # Limit to 5
    
    def _rank_hypotheses(self, hypotheses: List[Dict]) -> List[Dict]:
        """Rank hypotheses by potential impact and feasibility."""
        if not hypotheses:
            return []
        
        # Create ranking prompt
        hypothesis_list = "\n".join([
            f"{i+1}. {h.get('hypothesis', 'No hypothesis text')}"
            for i, h in enumerate(hypotheses)
        ])
        
        prompt = f"""
Rank these hypotheses by their potential scientific impact and feasibility:

{hypothesis_list}

Consider:
1. Potential to advance the field
2. Feasibility with current technology
3. Clarity and testability
4. Novelty and originality

Provide ranking with scores (0-100) and brief justification for top 5.
"""
        
        try:
            ranking_response = self.think(prompt)
            
            # Simple scoring based on response
            for i, hypothesis in enumerate(hypotheses):
                # Default score
                hypothesis['impact_score'] = 50
                hypothesis['feasibility_score'] = 50
                hypothesis['overall_score'] = 50
                
                # Try to extract scores from response
                if str(i+1) in ranking_response:
                    # Look for scores near the hypothesis number
                    score_match = re.search(rf'{i+1}.*?(\d+)', ranking_response)
                    if score_match:
                        hypothesis['overall_score'] = int(score_match.group(1))
            
            # Sort by overall score
            return sorted(hypotheses, key=lambda x: x.get('overall_score', 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Hypothesis ranking error: {e}")
            return hypotheses[:5]  # Return first 5 as fallback