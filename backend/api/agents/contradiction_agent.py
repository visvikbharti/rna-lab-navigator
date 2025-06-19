"""
Contradiction Finder Agent - Identifies contradictions and conflicts across papers
"""

from typing import Dict, Any, List, Tuple, Optional
from .base import BaseAgent
import json
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class ContradictionFinderAgent(BaseAgent):
    """Agent specialized in finding contradictions between research findings."""
    
    def __init__(self):
        super().__init__(
            name="ContradictionFinder",
            role="a meticulous analyst who identifies contradictions, conflicts, and inconsistencies across research papers, with expertise in distinguishing genuine contradictions from methodological differences",
            temperature=0.4  # Lower temperature for precision
        )
        
        self.contradiction_types = [
            "direct_conflict",      # A says X, B says not-X
            "magnitude_difference", # A says 2x effect, B says 10x effect
            "mechanism_dispute",    # Different proposed mechanisms
            "temporal_conflict",    # Results that change over time
            "population_variance",  # Different results in different populations
            "methodological_artifact" # Contradictions due to methods
        ]
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Find contradictions across papers."""
        papers = input_data.get('papers', [])
        focus_area = input_data.get('focus_area', '')
        depth = input_data.get('depth', 'standard')  # standard or deep
        
        if len(papers) < 2:
            return {"error": "Need at least 2 papers to find contradictions"}
        
        # Extract key claims from each paper
        paper_claims = self._extract_claims(papers)
        
        # Find pairwise contradictions
        contradictions = self._find_contradictions(paper_claims)
        
        # Analyze contradiction patterns
        patterns = self._analyze_contradiction_patterns(contradictions)
        
        # Deep analysis if requested
        if depth == 'deep':
            resolution_hypotheses = self._generate_resolution_hypotheses(contradictions)
            meta_analysis = self._meta_analyze_contradictions(contradictions, papers)
        else:
            resolution_hypotheses = []
            meta_analysis = {}
        
        # Generate summary insights
        insights = self._generate_insights(contradictions, patterns)
        
        return {
            "contradictions": contradictions,
            "patterns": patterns,
            "insights": insights,
            "resolution_hypotheses": resolution_hypotheses,
            "meta_analysis": meta_analysis,
            "summary": self._create_summary(contradictions, patterns)
        }
    
    def _extract_claims(self, papers: List[Dict]) -> List[Dict]:
        """Extract key claims from each paper."""
        all_claims = []
        
        for paper in papers[:15]:  # Limit to 15 papers for performance
            # Create paper context
            paper_context = f"""
Title: {paper.get('title', 'Unknown')}
Authors: {paper.get('authors', 'Unknown')}
Abstract: {paper.get('abstract', '')[:1000]}
Key Findings: {paper.get('findings', '')}
Methods: {paper.get('methods', '')[:500]}
"""
            
            prompt = f"""
Extract the main scientific claims from this paper:

{paper_context}

For each claim, identify:
1. The specific claim or finding
2. The evidence type (experimental, observational, theoretical)
3. The confidence level stated
4. Any caveats or limitations mentioned
5. Quantitative values if present

Format as JSON list of claims.
"""
            
            try:
                response = self.think(prompt)
                claims = self._parse_claims_response(response)
                
                # Add paper metadata to each claim
                for claim in claims:
                    claim['paper_id'] = paper.get('id', f"paper_{papers.index(paper)}")
                    claim['paper_title'] = paper.get('title', 'Unknown')
                    claim['paper_year'] = paper.get('year', 'Unknown')
                    claim['paper_authors'] = paper.get('authors', 'Unknown')
                
                all_claims.extend(claims)
                
            except Exception as e:
                logger.error(f"Error extracting claims from paper: {e}")
                continue
        
        return all_claims
    
    def _find_contradictions(self, claims: List[Dict]) -> List[Dict]:
        """Find contradictions between claims."""
        contradictions = []
        
        # Group claims by topic for efficient comparison
        topic_groups = self._group_claims_by_topic(claims)
        
        for topic, topic_claims in topic_groups.items():
            if len(topic_claims) < 2:
                continue
            
            # Compare claims within the same topic
            for i, claim1 in enumerate(topic_claims):
                for claim2 in topic_claims[i+1:]:
                    contradiction = self._compare_claims(claim1, claim2)
                    if contradiction:
                        contradiction['topic'] = topic
                        contradictions.append(contradiction)
        
        # Rank contradictions by importance
        ranked = self._rank_contradictions(contradictions)
        
        return ranked
    
    def _group_claims_by_topic(self, claims: List[Dict]) -> Dict[str, List[Dict]]:
        """Group claims by research topic."""
        # Create a prompt to classify claims
        claims_text = "\n".join([
            f"{i+1}. {claim.get('claim', '')}"
            for i, claim in enumerate(claims[:30])  # Limit for prompt size
        ])
        
        prompt = f"""
Group these scientific claims by topic/theme:

{claims_text}

Identify 3-7 main topics and list which claim numbers belong to each topic.
Focus on grouping claims that make statements about the same phenomenon.

Format: Topic Name: [claim numbers]
"""
        
        response = self.think(prompt)
        
        # Parse grouping
        groups = {}
        lines = response.split('\n')
        
        for line in lines:
            if ':' in line and '[' in line:
                topic = line.split(':')[0].strip()
                # Extract numbers
                numbers_text = line[line.find('['):line.find(']')+1]
                try:
                    numbers = json.loads(numbers_text.replace("'", '"'))
                    groups[topic] = [claims[n-1] for n in numbers if 0 < n <= len(claims)]
                except:
                    # Fallback: extract numbers manually
                    numbers = re.findall(r'\d+', numbers_text)
                    groups[topic] = [claims[int(n)-1] for n in numbers if 0 < int(n) <= len(claims)]
        
        # Fallback: group all claims together if parsing fails
        if not groups:
            groups["General"] = claims
        
        return groups
    
    def _compare_claims(self, claim1: Dict, claim2: Dict) -> Optional[Dict]:
        """Compare two claims for contradictions."""
        # Skip if same paper
        if claim1.get('paper_id') == claim2.get('paper_id'):
            return None
        
        prompt = f"""
Compare these two scientific claims for contradictions:

CLAIM 1 (from {claim1.get('paper_year')}):
"{claim1.get('claim', '')}"
Evidence: {claim1.get('evidence_type', 'Not specified')}
Paper: {claim1.get('paper_title', '')}

CLAIM 2 (from {claim2.get('paper_year')}):  
"{claim2.get('claim', '')}"
Evidence: {claim2.get('evidence_type', 'Not specified')}
Paper: {claim2.get('paper_title', '')}

Determine:
1. Do these claims contradict each other? (yes/no)
2. If yes, what type of contradiction:
   - direct_conflict (opposite claims)
   - magnitude_difference (different effect sizes)
   - mechanism_dispute (different explanations)
   - temporal_conflict (different at different times)
   - population_variance (different in different groups)
   - methodological_artifact (due to different methods)
3. Severity (low/medium/high)
4. Brief explanation

Answer in JSON format.
"""
        
        try:
            response = self.think(prompt)
            
            # Parse response
            contradiction_data = self._parse_contradiction_response(response)
            
            if contradiction_data.get('is_contradiction'):
                return {
                    "claim1": claim1,
                    "claim2": claim2,
                    "type": contradiction_data.get('type', 'unknown'),
                    "severity": contradiction_data.get('severity', 'medium'),
                    "explanation": contradiction_data.get('explanation', ''),
                    "discovered_at": datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Error comparing claims: {e}")
        
        return None
    
    def _parse_claims_response(self, response: str) -> List[Dict]:
        """Parse claims from LLM response."""
        claims = []
        
        # Try to find JSON
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            try:
                claims_data = json.loads(json_match.group())
                for claim_item in claims_data:
                    if isinstance(claim_item, dict):
                        claims.append(claim_item)
                    else:
                        # Simple string claim
                        claims.append({"claim": str(claim_item)})
                return claims
            except:
                pass
        
        # Fallback: extract claims from numbered list
        lines = response.split('\n')
        for line in lines:
            if re.match(r'^\d+\.', line) or line.strip().startswith('-'):
                claim_text = re.sub(r'^\d+\.\s*|-\s*', '', line).strip()
                if len(claim_text) > 20:  # Minimum claim length
                    claims.append({
                        "claim": claim_text,
                        "evidence_type": "extracted",
                        "confidence": "unknown"
                    })
        
        return claims
    
    def _parse_contradiction_response(self, response: str) -> Dict:
        """Parse contradiction analysis response."""
        result = {
            "is_contradiction": False,
            "type": "unknown",
            "severity": "low",
            "explanation": ""
        }
        
        # Try JSON parsing first
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                result.update(data)
                # Handle various ways of expressing boolean
                if 'is_contradiction' in data:
                    result['is_contradiction'] = str(data['is_contradiction']).lower() in ['yes', 'true', '1']
                elif 'contradiction' in data:
                    result['is_contradiction'] = str(data['contradiction']).lower() in ['yes', 'true', '1']
                return result
            except:
                pass
        
        # Fallback: parse from text
        response_lower = response.lower()
        
        # Check for contradiction
        if 'yes' in response_lower and 'contradict' in response_lower:
            result['is_contradiction'] = True
        elif 'no' in response_lower and 'contradict' in response_lower:
            result['is_contradiction'] = False
            return result
        
        # Extract type
        for c_type in self.contradiction_types:
            if c_type.replace('_', ' ') in response_lower:
                result['type'] = c_type
                break
        
        # Extract severity
        if 'high' in response_lower:
            result['severity'] = 'high'
        elif 'medium' in response_lower:
            result['severity'] = 'medium'
        elif 'low' in response_lower:
            result['severity'] = 'low'
        
        # Extract explanation
        if 'explanation:' in response_lower:
            result['explanation'] = response.split('explanation:')[1].strip()[:200]
        else:
            # Use first substantial sentence as explanation
            sentences = response.split('.')
            for sentence in sentences:
                if len(sentence.strip()) > 30:
                    result['explanation'] = sentence.strip()
                    break
        
        return result
    
    def _rank_contradictions(self, contradictions: List[Dict]) -> List[Dict]:
        """Rank contradictions by importance."""
        # Assign scores
        severity_scores = {'high': 3, 'medium': 2, 'low': 1}
        type_scores = {
            'direct_conflict': 3,
            'mechanism_dispute': 2.5,
            'magnitude_difference': 2,
            'temporal_conflict': 1.5,
            'population_variance': 1,
            'methodological_artifact': 0.5
        }
        
        for contradiction in contradictions:
            severity = contradiction.get('severity', 'medium')
            c_type = contradiction.get('type', 'unknown')
            
            score = severity_scores.get(severity, 1) * type_scores.get(c_type, 1)
            
            # Bonus for recent papers
            year1 = contradiction.get('claim1', {}).get('paper_year', '0')
            year2 = contradiction.get('claim2', {}).get('paper_year', '0')
            
            try:
                avg_year = (int(year1) + int(year2)) / 2
                if avg_year > 2020:
                    score *= 1.2
            except:
                pass
            
            contradiction['importance_score'] = score
        
        # Sort by importance
        return sorted(contradictions, key=lambda x: x.get('importance_score', 0), reverse=True)
    
    def _analyze_contradiction_patterns(self, contradictions: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in contradictions."""
        patterns = {
            "by_type": {},
            "by_severity": {},
            "temporal_trends": [],
            "author_conflicts": [],
            "methodological_patterns": []
        }
        
        # Count by type
        for c in contradictions:
            c_type = c.get('type', 'unknown')
            patterns['by_type'][c_type] = patterns['by_type'].get(c_type, 0) + 1
        
        # Count by severity
        for c in contradictions:
            severity = c.get('severity', 'unknown')
            patterns['by_severity'][severity] = patterns['by_severity'].get(severity, 0) + 1
        
        # Temporal analysis
        year_conflicts = {}
        for c in contradictions:
            year1 = c.get('claim1', {}).get('paper_year', 'Unknown')
            year2 = c.get('claim2', {}).get('paper_year', 'Unknown')
            
            if year1 != year2 and year1 != 'Unknown' and year2 != 'Unknown':
                year_pair = f"{min(year1, year2)}-{max(year1, year2)}"
                year_conflicts[year_pair] = year_conflicts.get(year_pair, 0) + 1
        
        patterns['temporal_trends'] = [
            {"period": k, "conflicts": v} 
            for k, v in sorted(year_conflicts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Look for author patterns
        author_pairs = {}
        for c in contradictions:
            authors1 = c.get('claim1', {}).get('paper_authors', '').split(',')[0].strip()
            authors2 = c.get('claim2', {}).get('paper_authors', '').split(',')[0].strip()
            
            if authors1 and authors2:
                pair = tuple(sorted([authors1, authors2]))
                author_pairs[pair] = author_pairs.get(pair, 0) + 1
        
        patterns['author_conflicts'] = [
            {"authors": list(k), "conflict_count": v}
            for k, v in sorted(author_pairs.items(), key=lambda x: x[1], reverse=True)
            if v > 1  # Only repeated conflicts
        ]
        
        return patterns
    
    def _generate_resolution_hypotheses(self, contradictions: List[Dict]) -> List[Dict]:
        """Generate hypotheses that could resolve contradictions."""
        hypotheses = []
        
        # Analyze top contradictions
        for contradiction in contradictions[:5]:  # Top 5
            prompt = f"""
These two research claims contradict each other:

Claim 1: {contradiction.get('claim1', {}).get('claim', '')}
Claim 2: {contradiction.get('claim2', {}).get('claim', '')}

Type: {contradiction.get('type', '')}
Explanation: {contradiction.get('explanation', '')}

Generate 2-3 hypotheses that could resolve this contradiction.
Consider:
- Hidden variables
- Context-dependent effects
- Methodological differences
- Threshold effects
- Time-dependent changes

Format each hypothesis clearly and make it testable.
"""
            
            response = self.think(prompt)
            
            # Parse hypotheses
            hyp_list = self._extract_hypotheses_from_text(response)
            
            for hyp in hyp_list:
                hypotheses.append({
                    "contradiction_type": contradiction.get('type', ''),
                    "hypothesis": hyp,
                    "testable": True,
                    "related_papers": [
                        contradiction.get('claim1', {}).get('paper_title', ''),
                        contradiction.get('claim2', {}).get('paper_title', '')
                    ]
                })
        
        return hypotheses
    
    def _extract_hypotheses_from_text(self, text: str) -> List[str]:
        """Extract hypotheses from text."""
        hypotheses = []
        
        # Look for numbered items or bullet points
        lines = text.split('\n')
        for line in lines:
            if re.match(r'^(?:\d+\.|[-•*])\s*', line):
                hyp_text = re.sub(r'^(?:\d+\.|[-•*])\s*', '', line).strip()
                if len(hyp_text) > 30 and any(word in hyp_text.lower() for word in ['if', 'when', 'could', 'may']):
                    hypotheses.append(hyp_text)
        
        # If no numbered items, look for hypothesis-like sentences
        if not hypotheses:
            sentences = text.split('.')
            for sentence in sentences:
                if len(sentence) > 30 and any(word in sentence.lower() for word in ['hypothesis', 'could be', 'might be', 'suggests']):
                    hypotheses.append(sentence.strip())
        
        return hypotheses[:3]  # Max 3 hypotheses
    
    def _meta_analyze_contradictions(self, contradictions: List[Dict], papers: List[Dict]) -> Dict[str, Any]:
        """Perform meta-analysis of contradictions."""
        meta = {
            "total_papers": len(papers),
            "total_contradictions": len(contradictions),
            "contradiction_rate": len(contradictions) / max(len(papers) * (len(papers) - 1) / 2, 1),
            "most_controversial_topics": [],
            "resolution_difficulty": "",
            "field_maturity_assessment": ""
        }
        
        # Find most controversial topics
        topic_conflicts = {}
        for c in contradictions:
            topic = c.get('topic', 'Unknown')
            topic_conflicts[topic] = topic_conflicts.get(topic, 0) + 1
        
        meta['most_controversial_topics'] = [
            {"topic": k, "conflicts": v}
            for k, v in sorted(topic_conflicts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Assess resolution difficulty
        high_severity = sum(1 for c in contradictions if c.get('severity') == 'high')
        if high_severity > len(contradictions) * 0.3:
            meta['resolution_difficulty'] = "High - many fundamental disagreements"
        elif high_severity > len(contradictions) * 0.1:
            meta['resolution_difficulty'] = "Medium - some core conflicts"
        else:
            meta['resolution_difficulty'] = "Low - mostly minor disagreements"
        
        # Field maturity assessment
        method_artifacts = sum(1 for c in contradictions if c.get('type') == 'methodological_artifact')
        if method_artifacts > len(contradictions) * 0.5:
            meta['field_maturity_assessment'] = "Early stage - methodological standardization needed"
        elif len(contradictions) < 5:
            meta['field_maturity_assessment'] = "Mature - consensus on most topics"
        else:
            meta['field_maturity_assessment'] = "Active research area - healthy debate ongoing"
        
        return meta
    
    def _generate_insights(self, contradictions: List[Dict], patterns: Dict) -> List[Dict]:
        """Generate actionable insights from contradictions."""
        insights = []
        
        # Insight 1: Most controversial area
        if patterns.get('most_controversial_topics'):
            top_topic = patterns['most_controversial_topics'][0]
            insights.append({
                "type": "research_focus",
                "insight": f"The topic '{top_topic['topic']}' shows the most contradictions ({top_topic['conflicts']}), suggesting it needs focused research",
                "action": "Design experiments specifically to resolve these contradictions",
                "priority": "high"
            })
        
        # Insight 2: Methodological issues
        method_conflicts = patterns.get('by_type', {}).get('methodological_artifact', 0)
        if method_conflicts > len(contradictions) * 0.3:
            insights.append({
                "type": "methodology",
                "insight": "Many contradictions stem from methodological differences",
                "action": "Standardize protocols or conduct method comparison studies",
                "priority": "high"
            })
        
        # Insight 3: Temporal evolution
        if patterns.get('temporal_trends'):
            insights.append({
                "type": "temporal",
                "insight": "Contradictions show temporal patterns, suggesting field evolution",
                "action": "Focus on recent findings and track how understanding has changed",
                "priority": "medium"
            })
        
        # Insight 4: Direct conflicts needing resolution
        direct_conflicts = patterns.get('by_type', {}).get('direct_conflict', 0)
        if direct_conflicts > 0:
            insights.append({
                "type": "fundamental",
                "insight": f"Found {direct_conflicts} direct contradictions requiring immediate attention",
                "action": "Design definitive experiments to resolve these conflicts",
                "priority": "critical"
            })
        
        return insights
    
    def _create_summary(self, contradictions: List[Dict], patterns: Dict) -> str:
        """Create executive summary of contradiction analysis."""
        total = len(contradictions)
        high_severity = sum(1 for c in contradictions if c.get('severity') == 'high')
        
        summary = f"""
Contradiction Analysis Summary:
- Total contradictions found: {total}
- High severity contradictions: {high_severity}
- Most common type: {max(patterns.get('by_type', {'none': 0}), key=patterns.get('by_type', {}).get)}
- Papers with most conflicts: {len(set(c.get('claim1', {}).get('paper_id', '') for c in contradictions))}

Key Finding: """
        
        if high_severity > total * 0.3:
            summary += "The field shows significant disagreement on fundamental issues."
        elif total < 5:
            summary += "The field shows good consensus with few contradictions."
        else:
            summary += "The field shows healthy scientific debate with resolvable contradictions."
        
        return summary.strip()