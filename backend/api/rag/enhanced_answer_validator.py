"""
Enhanced Answer Validation System for RNA Lab Navigator
======================================================

This module implements quality checks and validation for RAG-generated answers
to ensure they meet the lab's standards for accuracy and helpfulness.
"""

import re
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class AnswerQualityValidator:
    """Validates and enhances answer quality"""
    
    def __init__(self):
        # Quality thresholds
        self.MIN_ANSWER_LENGTH = 100  # Minimum characters for a good answer
        self.MIN_CITATION_COUNT = 1   # Minimum citations required
        self.MIN_CONFIDENCE_SCORE = 0.45
        
        # Common RNA lab terms for relevance checking
        self.lab_terms = {
            'methods': ['pcr', 'qpcr', 'rt-pcr', 'western blot', 'northern blot', 
                       'transfection', 'transformation', 'trizol', 'rna extraction',
                       'crispr', 'cas9', 'cas13', 'grna', 'sgrna'],
            'concepts': ['rna', 'dna', 'mrna', 'mirna', 'lncrna', 'splicing',
                        'transcription', 'translation', 'gene expression'],
            'equipment': ['thermocycler', 'centrifuge', 'nanodrop', 'qubit',
                         'bioanalyzer', 'sequencer', 'microscope'],
            'reagents': ['buffer', 'enzyme', 'primer', 'probe', 'antibody',
                        'plasmid', 'vector', 'competent cells']
        }
        
        # Quality issue patterns
        self.quality_issues = {
            'too_short': 'Answer is too brief',
            'no_citations': 'No source citations provided',
            'low_confidence': 'Low confidence score',
            'no_specifics': 'Lacks specific details or protocols',
            'unclear': 'Answer is vague or unclear',
            'off_topic': 'Answer may not address the question directly'
        }
    
    def validate_answer(self, query: str, answer: str, confidence: float, 
                       sources: List[Dict]) -> Dict[str, Any]:
        """
        Comprehensive answer validation
        
        Returns:
            Dict with validation results and suggestions for improvement
        """
        validation_results = {
            'is_valid': True,
            'issues': [],
            'suggestions': [],
            'quality_score': 0.0,
            'enhanced_answer': answer
        }
        
        # Check answer length
        if len(answer.strip()) < self.MIN_ANSWER_LENGTH:
            validation_results['issues'].append(self.quality_issues['too_short'])
            validation_results['suggestions'].append(
                "Expand the answer with more details from the sources"
            )
        
        # Check for citations
        citation_count = self._count_citations(answer)
        if citation_count < self.MIN_CITATION_COUNT and sources:
            validation_results['issues'].append(self.quality_issues['no_citations'])
            validation_results['suggestions'].append(
                "Add proper citations in format: [Author, Year]"
            )
        
        # Check confidence score
        if confidence < self.MIN_CONFIDENCE_SCORE:
            validation_results['issues'].append(self.quality_issues['low_confidence'])
            validation_results['suggestions'].append(
                "Consider searching for more relevant sources"
            )
        
        # Check for specific details
        if not self._has_specific_details(answer):
            validation_results['issues'].append(self.quality_issues['no_specifics'])
            validation_results['suggestions'].append(
                "Include specific protocols, concentrations, or timings"
            )
        
        # Check relevance to query
        if not self._is_relevant_to_query(query, answer):
            validation_results['issues'].append(self.quality_issues['off_topic'])
            validation_results['suggestions'].append(
                "Ensure the answer directly addresses the question"
            )
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            answer, confidence, citation_count, validation_results['issues']
        )
        validation_results['quality_score'] = quality_score
        
        # Determine if answer is valid
        validation_results['is_valid'] = (
            len(validation_results['issues']) == 0 or 
            (quality_score >= 0.6 and confidence >= 0.3)
        )
        
        # Enhance answer if needed
        if validation_results['issues'] and sources:
            validation_results['enhanced_answer'] = self._enhance_answer(
                query, answer, sources, validation_results['issues']
            )
        
        return validation_results
    
    def _count_citations(self, answer: str) -> int:
        """Count citations in the answer"""
        # Look for patterns like [Author, Year] or (Author, Year)
        citation_patterns = [
            r'\[[\w\s]+,\s*\d{4}\]',  # [Author, 2024]
            r'\([\w\s]+,\s*\d{4}\)',  # (Author, 2024)
            r'According to [\w\s]+ \(\d{4}\)',  # According to Author (2024)
            r'[\w\s]+ et al\.,? \d{4}',  # Author et al. 2024
        ]
        
        citations = set()
        for pattern in citation_patterns:
            matches = re.findall(pattern, answer)
            citations.update(matches)
        
        return len(citations)
    
    def _has_specific_details(self, answer: str) -> bool:
        """Check if answer contains specific technical details"""
        # Look for specific indicators
        specific_patterns = [
            r'\d+\s*[µμ]?[MLlgm]',  # Concentrations (e.g., 10 µM, 5 mL)
            r'\d+\s*°C',  # Temperatures
            r'\d+\s*(minutes?|hours?|mins?|hrs?)',  # Time periods
            r'\d+\s*rpm',  # Centrifuge speeds
            r'step\s*\d+',  # Step numbers
            r'\d+:\d+',  # Ratios
            r'pH\s*\d+\.?\d*',  # pH values
        ]
        
        for pattern in specific_patterns:
            if re.search(pattern, answer, re.IGNORECASE):
                return True
        
        return False
    
    def _is_relevant_to_query(self, query: str, answer: str) -> bool:
        """Check if answer is relevant to the query"""
        # Extract key terms from query
        query_terms = set(query.lower().split())
        answer_terms = set(answer.lower().split())
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                      'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 
                      'was', 'were', 'been', 'have', 'has', 'had', 'do', 'does'}
        
        query_terms = query_terms - stop_words
        
        # Check overlap
        overlap = query_terms.intersection(answer_terms)
        
        # Also check for lab-specific terms
        lab_term_count = 0
        for category, terms in self.lab_terms.items():
            for term in terms:
                if term in answer.lower():
                    lab_term_count += 1
        
        return len(overlap) >= 2 or lab_term_count >= 2
    
    def _calculate_quality_score(self, answer: str, confidence: float, 
                                citation_count: int, issues: List[str]) -> float:
        """Calculate overall quality score"""
        score = 0.0
        
        # Base score from confidence
        score += confidence * 0.4
        
        # Length score
        length_score = min(len(answer) / 500, 1.0) * 0.2
        score += length_score
        
        # Citation score
        citation_score = min(citation_count / 3, 1.0) * 0.2
        score += citation_score
        
        # Technical detail score
        if self._has_specific_details(answer):
            score += 0.1
        
        # Deduct for issues
        score -= len(issues) * 0.1
        
        return max(0.0, min(1.0, score))
    
    def _enhance_answer(self, query: str, answer: str, sources: List[Dict], 
                       issues: List[str]) -> str:
        """Enhance answer to address quality issues"""
        enhanced = answer
        
        # Add citations if missing
        if self.quality_issues['no_citations'] in issues and sources:
            citation_text = "\n\nSources consulted:\n"
            for i, source in enumerate(sources[:3], 1):
                citation_text += f"{i}. {source.get('title', 'Unknown')} "
                citation_text += f"by {source.get('author', 'Unknown')} "
                citation_text += f"({source.get('year', 'N/A')})\n"
            enhanced += citation_text
        
        # Add disclaimer for low confidence
        if self.quality_issues['low_confidence'] in issues:
            disclaimer = "\n\nNote: This answer is based on limited information "
            disclaimer += "from the available documents. For more specific guidance, "
            disclaimer += "please consult with senior lab members or refer to "
            disclaimer += "detailed protocol manuals."
            enhanced += disclaimer
        
        # Add general helpful information if too short
        if self.quality_issues['too_short'] in issues:
            helpful_addition = "\n\nFor additional support:\n"
            helpful_addition += "- Check the lab's protocol database for detailed procedures\n"
            helpful_addition += "- Consult recent papers from the lab for specific methods\n"
            helpful_addition += "- Ask senior lab members for hands-on guidance"
            enhanced += helpful_addition
        
        return enhanced


class AnswerEnhancer:
    """Enhances answers with additional context and formatting"""
    
    def __init__(self):
        self.formatting_rules = {
            'protocols': self._format_protocol_answer,
            'troubleshooting': self._format_troubleshooting_answer,
            'comparison': self._format_comparison_answer,
            'general': self._format_general_answer
        }
    
    def enhance_answer(self, query: str, answer: str, 
                      answer_type: str = 'general') -> str:
        """Apply appropriate formatting based on answer type"""
        formatter = self.formatting_rules.get(answer_type, self._format_general_answer)
        return formatter(query, answer)
    
    def detect_answer_type(self, query: str) -> str:
        """Detect the type of answer needed based on query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['protocol', 'procedure', 'method', 'how to']):
            return 'protocols'
        elif any(word in query_lower for word in ['troubleshoot', 'problem', 'issue', 'fix', 'why']):
            return 'troubleshooting'
        elif any(word in query_lower for word in ['compare', 'difference', 'versus', 'vs', 'better']):
            return 'comparison'
        else:
            return 'general'
    
    def _format_protocol_answer(self, query: str, answer: str) -> str:
        """Format protocol-type answers with clear steps"""
        # Check if answer already has numbered steps
        if re.search(r'^\d+\.', answer, re.MULTILINE):
            return answer
        
        # Try to identify and format steps
        lines = answer.split('\n')
        formatted_lines = []
        step_counter = 1
        
        for line in lines:
            line = line.strip()
            if line and self._is_action_step(line):
                formatted_lines.append(f"{step_counter}. {line}")
                step_counter += 1
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_troubleshooting_answer(self, query: str, answer: str) -> str:
        """Format troubleshooting answers with clear problem-solution structure"""
        # Add troubleshooting header if not present
        if not any(word in answer.lower() for word in ['troubleshoot', 'solution', 'try']):
            enhanced = "Troubleshooting Guide:\n\n" + answer
        else:
            enhanced = answer
        
        # Add general troubleshooting tips if answer is short
        if len(answer) < 200:
            enhanced += "\n\nGeneral troubleshooting tips:\n"
            enhanced += "• Verify all reagents are fresh and properly stored\n"
            enhanced += "• Check equipment calibration and settings\n"
            enhanced += "• Review the protocol for any missed steps\n"
            enhanced += "• Consult with lab members who have performed this successfully"
        
        return enhanced
    
    def _format_comparison_answer(self, query: str, answer: str) -> str:
        """Format comparison answers with clear structure"""
        # Look for comparison indicators
        if not any(word in answer for word in ['Advantages:', 'Disadvantages:', 'Pros:', 'Cons:']):
            # Try to structure the comparison
            enhanced = "Comparison Analysis:\n\n" + answer
        else:
            enhanced = answer
        
        return enhanced
    
    def _format_general_answer(self, query: str, answer: str) -> str:
        """Apply general formatting improvements"""
        # Ensure proper paragraph spacing
        paragraphs = answer.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 50:  # Only format substantial paragraphs
                formatted_paragraphs.append(para)
        
        return '\n\n'.join(formatted_paragraphs)
    
    def _is_action_step(self, text: str) -> bool:
        """Check if text line is likely an action step"""
        action_verbs = ['add', 'mix', 'incubate', 'centrifuge', 'transfer', 
                       'wash', 'resuspend', 'dilute', 'prepare', 'collect',
                       'measure', 'adjust', 'heat', 'cool', 'vortex', 'pipette']
        
        text_lower = text.lower()
        return any(verb in text_lower for verb in action_verbs)


# Singleton instances
_validator = None
_enhancer = None

def get_answer_validator() -> AnswerQualityValidator:
    """Get singleton validator instance"""
    global _validator
    if _validator is None:
        _validator = AnswerQualityValidator()
    return _validator

def get_answer_enhancer() -> AnswerEnhancer:
    """Get singleton enhancer instance"""
    global _enhancer
    if _enhancer is None:
        _enhancer = AnswerEnhancer()
    return _enhancer