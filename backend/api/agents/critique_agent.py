"""
Critical Review Agent - Identifies issues and provides constructive critique
"""

from typing import Dict, Any, List, Optional
from .base import BaseAgent
import logging
import json

logger = logging.getLogger(__name__)


class CriticalReviewAgent(BaseAgent):
    """Agent specialized in critical analysis and review."""
    
    def __init__(self):
        super().__init__(
            name="CriticalReviewer",
            role="a rigorous scientific reviewer who identifies flaws, assumptions, limitations, and potential issues in research proposals and protocols",
            temperature=0.3  # Low temperature for careful analysis
        )
        
        self.review_aspects = [
            "statistical power",
            "control adequacy", 
            "reproducibility",
            "ethical considerations",
            "resource efficiency",
            "technical feasibility",
            "alternative approaches",
            "potential confounders"
        ]
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Critically review a hypothesis, protocol, or research plan."""
        review_type = input_data.get('type', 'general')
        content = input_data.get('content', '')
        context = input_data.get('context', {})
        
        if review_type == 'hypothesis':
            return self._review_hypothesis(content, context)
        elif review_type == 'protocol':
            return self._review_protocol(content, context)
        elif review_type == 'literature':
            return self._review_literature_analysis(content, context)
        else:
            return self._general_review(content, context)
    
    def _review_hypothesis(self, hypothesis: Dict[str, Any], context: Dict) -> Dict[str, Any]:
        """Review a hypothesis for clarity, testability, and significance."""
        hypothesis_text = hypothesis.get('hypothesis', '') if isinstance(hypothesis, dict) else str(hypothesis)
        
        prompt = f"""
Critically review this research hypothesis:
"{hypothesis_text}"

Evaluate:
1. Clarity and specificity
2. Testability and falsifiability
3. Theoretical foundation
4. Potential impact if true/false
5. Hidden assumptions
6. Alternative explanations
7. Required resources and feasibility
8. Ethical considerations

Provide constructive criticism with specific suggestions for improvement.
Be thorough but fair.
"""
        
        review_text = self.think(prompt)
        
        # Structure the review
        issues = self._extract_issues(review_text)
        strengths = self._extract_strengths(review_text)
        suggestions = self._extract_suggestions(review_text)
        
        # Score the hypothesis
        scores = self._score_hypothesis(hypothesis_text, review_text)
        
        return {
            "overall_assessment": self._get_overall_assessment(scores),
            "strengths": strengths,
            "issues": issues,
            "suggestions": suggestions,
            "scores": scores,
            "detailed_review": review_text,
            "recommendation": self._get_recommendation(scores, issues)
        }
    
    def _review_protocol(self, protocol: Dict[str, Any], context: Dict) -> Dict[str, Any]:
        """Review an experimental protocol."""
        # Extract key protocol elements
        methods = protocol.get('methods', [])
        controls = protocol.get('controls', [])
        timeline = protocol.get('timeline', {})
        analysis_plan = protocol.get('analysis_plan', {})
        
        # Create comprehensive review prompt
        prompt = f"""
Review this experimental protocol:

Methods: {json.dumps(methods, indent=2) if methods else 'Not provided'}
Controls: {json.dumps(controls, indent=2) if controls else 'Not provided'}
Timeline: {json.dumps(timeline, indent=2) if timeline else 'Not provided'}
Analysis: {json.dumps(analysis_plan, indent=2) if analysis_plan else 'Not provided'}

Critically evaluate:
1. Methodological rigor
2. Control adequacy
3. Statistical power
4. Timeline feasibility
5. Resource requirements
6. Potential failure points
7. Reproducibility concerns
8. Safety issues

Identify specific weaknesses and suggest improvements.
"""
        
        review_text = self.think(prompt)
        
        # Detailed aspect reviews
        method_review = self._review_methods(methods)
        control_review = self._review_controls(controls)
        stats_review = self._review_statistics(analysis_plan)
        
        issues = []
        if method_review['issues']:
            issues.extend(method_review['issues'])
        if control_review['issues']:
            issues.extend(control_review['issues'])
        if stats_review['issues']:
            issues.extend(stats_review['issues'])
        
        return {
            "overall_review": review_text,
            "method_review": method_review,
            "control_review": control_review,
            "statistics_review": stats_review,
            "critical_issues": self._prioritize_issues(issues),
            "improvement_plan": self._create_improvement_plan(issues),
            "risk_assessment": self._assess_protocol_risks(protocol)
        }
    
    def _review_literature_analysis(self, analysis: Dict[str, Any], context: Dict) -> Dict[str, Any]:
        """Review literature analysis for bias and completeness."""
        patterns = analysis.get('patterns', [])
        contradictions = analysis.get('contradictions', [])
        gaps = analysis.get('gaps', [])
        synthesis = analysis.get('synthesis', {})
        
        prompt = f"""
Review this literature analysis for potential issues:

Patterns identified: {len(patterns)}
Contradictions found: {len(contradictions)}
Gaps discovered: {len(gaps)}

Sample patterns: {json.dumps(patterns[:2], indent=2) if patterns else 'None'}
Sample contradictions: {json.dumps(contradictions[:2], indent=2) if contradictions else 'None'}

Evaluate:
1. Selection bias in papers reviewed
2. Overinterpretation of patterns
3. Missed contradictions
4. Confirmation bias
5. Temporal bias (older vs newer studies)
6. Geographic/population bias
7. Methodological bias
8. Publication bias

Be specific about potential blind spots.
"""
        
        review_text = self.think(prompt)
        
        return {
            "bias_assessment": self._assess_biases(review_text),
            "completeness_score": self._score_completeness(analysis),
            "missed_aspects": self._identify_missed_aspects(analysis, review_text),
            "quality_concerns": self._extract_quality_concerns(review_text),
            "recommendations": self._literature_recommendations(analysis, review_text)
        }
    
    def _review_methods(self, methods: List[Dict]) -> Dict[str, Any]:
        """Deep review of experimental methods."""
        if not methods:
            return {"issues": ["No methods provided"], "score": 0}
        
        issues = []
        strengths = []
        
        # Check for critical steps
        critical_steps = sum(1 for m in methods if m.get('critical', False))
        if critical_steps == 0:
            issues.append("No critical steps identified - suggests incomplete planning")
        elif critical_steps > len(methods) / 2:
            issues.append("Too many critical steps - high risk of failure")
        
        # Check for timing
        has_timing = sum(1 for m in methods if m.get('duration'))
        if has_timing < len(methods) / 2:
            issues.append("Insufficient timing information for reproducibility")
        
        # Check for detail level
        detailed_steps = sum(1 for m in methods if len(m.get('details', '')) > 50)
        if detailed_steps < len(methods) / 3:
            issues.append("Insufficient detail in method descriptions")
        else:
            strengths.append("Good level of detail in methods")
        
        return {
            "issues": issues,
            "strengths": strengths,
            "score": max(0, 100 - len(issues) * 20)
        }
    
    def _review_controls(self, controls: List[Dict]) -> Dict[str, Any]:
        """Review experimental controls."""
        if not controls:
            return {"issues": ["No controls specified - major concern"], "score": 0}
        
        issues = []
        control_types = [c.get('type', '') for c in controls]
        
        # Check for essential controls
        if 'negative control' not in control_types:
            issues.append("Missing negative control")
        if 'positive control' not in control_types:
            issues.append("Missing positive control - cannot validate method")
        
        # Check for statistical controls
        has_replicates = any('replicate' in ct for ct in control_types)
        if not has_replicates:
            issues.append("No replicates specified - statistical power concern")
        
        return {
            "issues": issues,
            "control_coverage": len(control_types),
            "score": max(0, 100 - len(issues) * 25)
        }
    
    def _review_statistics(self, analysis_plan: Dict) -> Dict[str, Any]:
        """Review statistical analysis plan."""
        if not analysis_plan:
            return {"issues": ["No statistical analysis plan provided"], "score": 0}
        
        issues = []
        
        # Check key statistical elements
        if not analysis_plan.get('statistical_tests'):
            issues.append("No specific statistical tests identified")
        
        if not analysis_plan.get('power_calculation'):
            issues.append("Missing power calculation - unknown sample size adequacy")
        
        if not analysis_plan.get('success_criteria'):
            issues.append("No clear success criteria defined")
        
        return {
            "issues": issues,
            "completeness": len(analysis_plan),
            "score": max(0, 100 - len(issues) * 30)
        }
    
    def _extract_issues(self, text: str) -> List[Dict[str, str]]:
        """Extract issues from review text."""
        issues = []
        
        # Look for issue indicators
        issue_keywords = ['concern', 'problem', 'issue', 'weakness', 'limitation', 
                         'unclear', 'missing', 'insufficient', 'lack', 'risk']
        
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in issue_keywords):
                issues.append({
                    "issue": line.strip(),
                    "severity": self._assess_severity(line)
                })
        
        return issues[:10]  # Top 10 issues
    
    def _extract_strengths(self, text: str) -> List[str]:
        """Extract strengths from review text."""
        strengths = []
        
        strength_keywords = ['strength', 'good', 'excellent', 'clear', 'well-defined',
                           'appropriate', 'solid', 'robust', 'comprehensive']
        
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in strength_keywords):
                strengths.append(line.strip())
        
        return strengths[:5]  # Top 5 strengths
    
    def _extract_suggestions(self, text: str) -> List[Dict[str, str]]:
        """Extract improvement suggestions."""
        suggestions = []
        
        suggestion_keywords = ['suggest', 'recommend', 'consider', 'should', 'could',
                             'improve', 'alternative', 'instead', 'better']
        
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in suggestion_keywords):
                suggestions.append({
                    "suggestion": line.strip(),
                    "priority": self._assess_priority(line)
                })
        
        return sorted(suggestions, key=lambda x: x['priority'], reverse=True)[:7]
    
    def _score_hypothesis(self, hypothesis: str, review: str) -> Dict[str, int]:
        """Score hypothesis on multiple dimensions."""
        scores = {
            "clarity": 70,  # Default scores
            "testability": 70,
            "significance": 70,
            "feasibility": 70,
            "novelty": 70
        }
        
        # Adjust based on review content
        if 'clear' in review.lower() and 'specific' in review.lower():
            scores['clarity'] = 85
        elif 'unclear' in review.lower() or 'vague' in review.lower():
            scores['clarity'] = 40
        
        if 'testable' in review.lower() and 'falsifiable' in review.lower():
            scores['testability'] = 85
        elif 'difficult to test' in review.lower():
            scores['testability'] = 40
        
        # Overall score
        scores['overall'] = sum(scores.values()) // len(scores)
        
        return scores
    
    def _get_overall_assessment(self, scores: Dict[str, int]) -> str:
        """Get overall assessment based on scores."""
        overall = scores.get('overall', 0)
        
        if overall >= 80:
            return "Strong hypothesis with minor improvements needed"
        elif overall >= 60:
            return "Decent hypothesis requiring moderate refinement"
        elif overall >= 40:
            return "Weak hypothesis needing substantial revision"
        else:
            return "Fundamental issues requiring complete reconceptualization"
    
    def _get_recommendation(self, scores: Dict[str, int], issues: List[Dict]) -> str:
        """Get recommendation based on review."""
        critical_issues = [i for i in issues if i.get('severity') == 'critical']
        
        if critical_issues:
            return "Address critical issues before proceeding"
        elif scores.get('overall', 0) >= 70:
            return "Proceed with minor modifications"
        elif scores.get('overall', 0) >= 50:
            return "Revise and resubmit for review"
        else:
            return "Major revision required"
    
    def _assess_severity(self, text: str) -> str:
        """Assess issue severity."""
        critical_words = ['fatal', 'major', 'serious', 'critical', 'fundamental']
        moderate_words = ['concern', 'issue', 'problem', 'weakness']
        
        text_lower = text.lower()
        if any(word in text_lower for word in critical_words):
            return 'critical'
        elif any(word in text_lower for word in moderate_words):
            return 'moderate'
        else:
            return 'minor'
    
    def _assess_priority(self, text: str) -> int:
        """Assess suggestion priority (1-10)."""
        high_priority_words = ['must', 'critical', 'essential', 'immediately']
        medium_priority_words = ['should', 'recommend', 'important']
        
        text_lower = text.lower()
        if any(word in text_lower for word in high_priority_words):
            return 9
        elif any(word in text_lower for word in medium_priority_words):
            return 6
        else:
            return 3
    
    def _prioritize_issues(self, issues: List[Dict]) -> List[Dict]:
        """Prioritize issues by severity and impact."""
        # Sort by severity
        severity_order = {'critical': 3, 'moderate': 2, 'minor': 1}
        
        return sorted(issues, 
                     key=lambda x: severity_order.get(x.get('severity', 'minor'), 0),
                     reverse=True)
    
    def _create_improvement_plan(self, issues: List[Dict]) -> List[Dict]:
        """Create actionable improvement plan."""
        plan = []
        
        for i, issue in enumerate(issues[:5], 1):  # Top 5 issues
            plan.append({
                "step": i,
                "issue": issue.get('issue', ''),
                "action": f"Address {issue.get('severity', 'moderate')} issue",
                "timeline": "Before protocol execution" if issue.get('severity') == 'critical' else "Within 1 week"
            })
        
        return plan
    
    def _assess_protocol_risks(self, protocol: Dict) -> Dict[str, Any]:
        """Assess overall protocol risks."""
        risks = {
            "technical_risk": "medium",  # Default
            "resource_risk": "low",
            "timeline_risk": "medium",
            "ethical_risk": "low"
        }
        
        # Assess based on protocol complexity
        if len(protocol.get('methods', [])) > 20:
            risks['technical_risk'] = "high"
            risks['timeline_risk'] = "high"
        
        # Check for expensive materials
        materials = protocol.get('materials', {})
        total_items = sum(len(items) for items in materials.values() if isinstance(items, list))
        if total_items > 50:
            risks['resource_risk'] = "high"
        
        return risks
    
    def _assess_biases(self, review_text: str) -> List[Dict[str, str]]:
        """Assess potential biases in literature analysis."""
        biases = []
        
        bias_types = {
            "selection": "Papers may not represent full literature",
            "confirmation": "Analysis may favor expected outcomes",
            "recency": "Newer papers may be overweighted",
            "geographic": "Studies from certain regions may dominate",
            "publication": "Negative results may be underrepresented"
        }
        
        for bias_type, description in bias_types.items():
            if bias_type in review_text.lower():
                biases.append({
                    "type": bias_type,
                    "description": description,
                    "mitigation": f"Actively search for {bias_type} counterexamples"
                })
        
        return biases
    
    def _score_completeness(self, analysis: Dict) -> int:
        """Score completeness of literature analysis."""
        score = 50  # Base score
        
        # Add points for comprehensive analysis
        if len(analysis.get('patterns', [])) > 3:
            score += 15
        if len(analysis.get('contradictions', [])) > 0:
            score += 20
        if len(analysis.get('gaps', [])) > 2:
            score += 15
        
        return min(100, score)
    
    def _identify_missed_aspects(self, analysis: Dict, review: str) -> List[str]:
        """Identify potentially missed aspects."""
        missed = []
        
        # Standard aspects that should be covered
        expected_aspects = [
            "temporal trends",
            "methodological evolution", 
            "cross-cultural differences",
            "funding sources",
            "negative results"
        ]
        
        analysis_text = json.dumps(analysis)
        for aspect in expected_aspects:
            if aspect not in analysis_text.lower() and aspect not in review.lower():
                missed.append(f"Analysis may have missed: {aspect}")
        
        return missed
    
    def _extract_quality_concerns(self, text: str) -> List[str]:
        """Extract quality concerns from review."""
        concerns = []
        
        quality_keywords = ['quality', 'rigor', 'validity', 'reliability', 'bias']
        
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in quality_keywords):
                if any(neg in line.lower() for neg in ['poor', 'low', 'concern', 'issue']):
                    concerns.append(line.strip())
        
        return concerns
    
    def _literature_recommendations(self, analysis: Dict, review: str) -> List[str]:
        """Generate recommendations for improving literature analysis."""
        recommendations = [
            "Expand search to include pre-print servers",
            "Include systematic review methodology",
            "Add temporal analysis of findings evolution",
            "Consider meta-analysis where applicable",
            "Include failed experiments and negative results"
        ]
        
        # Customize based on analysis
        if len(analysis.get('contradictions', [])) == 0:
            recommendations.insert(0, "Actively search for contradictory findings")
        
        if len(analysis.get('patterns', [])) < 3:
            recommendations.insert(0, "Deepen pattern analysis across papers")
        
        return recommendations[:5]
    
    def _general_review(self, content: str, context: Dict) -> Dict[str, Any]:
        """General critical review for any content."""
        prompt = f"""
Provide a critical scientific review of:
{content}

Consider all aspects that could be improved or might be problematic.
Be constructive but thorough in identifying issues.
"""
        
        review = self.think(prompt)
        
        return {
            "review": review,
            "issues": self._extract_issues(review),
            "suggestions": self._extract_suggestions(review),
            "strengths": self._extract_strengths(review)
        }