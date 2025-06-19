"""
Research Query Classifier for RNA Lab Navigator
Intelligently routes queries to appropriate models based on complexity
"""

import re
from typing import Tuple, List, Dict, Any


class ResearchQueryClassifier:
    """Classify research queries to route to appropriate AI models"""
    
    # Research-specific patterns
    SIMPLE_PATTERNS = [
        # Definitions and basic facts
        r"what is (?:a |an |the )?[\w\s]+\??$",
        r"define [\w\s]+",
        r"(?:list|name) (?:the )?\w+",
        r"^[\w\s]+ stand for\??$",
        # Simple lookups
        r"melting temperature of",
        r"molecular weight of",
        r"concentration of",
        r"ph of",
        # Yes/no questions
        r"^(?:is|are|does|do|can|will|should)",
    ]
    
    COMPLEX_PATTERNS = [
        # Protocol design and optimization
        r"(?:design|optimize|improve|modify) (?:a |an |the )?protocol",
        r"troubleshoot(?:ing)?",
        r"why (?:is|are|does|did).*(?:not work|fail)",
        # Comparative analysis
        r"compare (?:and contrast|between)",
        r"difference(?:s)? between",
        r"advantages? and disadvantages?",
        # Hypothesis and experimental design
        r"hypothesis|hypotheses",
        r"experimental design",
        r"control(?:s)? for",
        # Multi-step procedures
        r"step(?:s)?(?:-| )by(?:-| )step",
        r"procedure for",
        r"how (?:do I|to|can I|should I)",
        # Analysis and interpretation
        r"(?:analyze|interpret|explain) (?:the |these |this )?(?:results?|data|findings?)",
        r"what (?:does|do) (?:the |these |this )?(?:results?|data) (?:mean|suggest|indicate)",
        # Mechanism questions
        r"mechanism of",
        r"pathway(?:s)?",
        r"how does [\w\s]+ work",
    ]
    
    ADVANCED_PATTERNS = [
        # Novel research design
        r"novel (?:approach|method|technique)",
        r"innovative",
        r"cutting[- ]edge",
        # Complex multi-component questions
        r"(?:first|then|next|finally|additionally)",
        r"multiple (?:factors|variables|conditions)",
        # Research synthesis
        r"systematic review",
        r"meta[- ]analysis",
        r"literature review",
        # Advanced troubleshooting
        r"(?:systematic|comprehensive) troubleshooting",
        r"root cause analysis",
        # Grant/paper writing
        r"research (?:proposal|grant)",
        r"manuscript",
        r"peer review",
    ]
    
    @classmethod
    def classify_query(cls, query: str, context: Dict[str, Any] = None) -> Tuple[str, float, str]:
        """
        Classify a research query and return appropriate model tier.
        
        Args:
            query: The user's research question
            context: Optional context (previous queries, user expertise, etc.)
            
        Returns:
            Tuple of (model_tier, confidence, reasoning)
        """
        query_lower = query.lower().strip()
        
        # Check for advanced patterns first (most specific)
        for pattern in cls.ADVANCED_PATTERNS:
            if re.search(pattern, query_lower):
                return ('advanced', 0.9, f"Advanced research query: matches '{pattern}'")
        
        # Check for complex patterns
        complex_matches = 0
        for pattern in cls.COMPLEX_PATTERNS:
            if re.search(pattern, query_lower):
                complex_matches += 1
        
        if complex_matches >= 2:
            return ('large', 0.85, f"Multiple complex patterns detected ({complex_matches})")
        elif complex_matches == 1:
            return ('large', 0.75, "Complex research query detected")
        
        # Check for simple patterns
        for pattern in cls.SIMPLE_PATTERNS:
            if re.search(pattern, query_lower):
                return ('small', 0.8, f"Simple lookup query: matches '{pattern}'")
        
        # Analyze query characteristics
        words = query_lower.split()
        word_count = len(words)
        
        # Check for technical terms density
        technical_terms = cls._count_technical_terms(query_lower)
        technical_density = technical_terms / max(word_count, 1)
        
        # Decision based on characteristics
        if word_count < 10 and technical_density < 0.3:
            return ('small', 0.6, "Short query with low technical complexity")
        elif word_count > 30 or technical_density > 0.5:
            return ('large', 0.7, "Long query or high technical density")
        else:
            return ('default', 0.7, "Standard research query")
    
    @classmethod
    def _count_technical_terms(cls, text: str) -> int:
        """Count technical/scientific terms in the text"""
        technical_keywords = [
            'rna', 'dna', 'protein', 'gene', 'expression', 'transcription',
            'translation', 'pcr', 'qpcr', 'western', 'blot', 'primer',
            'antibody', 'cell', 'culture', 'transfection', 'plasmid',
            'vector', 'enzyme', 'substrate', 'inhibitor', 'pathway',
            'phosphorylation', 'methylation', 'acetylation', 'ubiquitination',
            'crispr', 'cas9', 'knockout', 'knockdown', 'overexpression',
            'fluorescence', 'microscopy', 'flow', 'cytometry', 'sequencing',
            'bioinformatics', 'statistical', 'significance', 'p-value',
            'hypothesis', 'control', 'variable', 'replicate', 'protocol'
        ]
        
        count = 0
        text_words = text.lower().split()
        for word in text_words:
            if any(term in word for term in technical_keywords):
                count += 1
        return count
    
    @classmethod
    def get_model_for_query(cls, query: str, settings_tiers: Dict[str, str]) -> Tuple[str, str]:
        """
        Get the appropriate model for a query based on classification.
        
        Args:
            query: The research query
            settings_tiers: MODEL_TIERS from Django settings
            
        Returns:
            Tuple of (model_name, reasoning)
        """
        tier, confidence, reasoning = cls.classify_query(query)
        
        # Override to larger model if confidence is low
        if confidence < 0.6 and tier == 'small':
            tier = 'default'
            reasoning += " (upgraded due to low confidence)"
        
        model = settings_tiers.get(tier, settings_tiers.get('default', 'o4-mini'))
        
        # Special handling for o3 (check availability)
        if model == 'o3' and tier == 'advanced':
            # o3 is very expensive, so only use for truly complex queries
            model = settings_tiers.get('large', 'gpt-4.1')
            reasoning += " (using gpt-4.1 for cost efficiency)"
        
        return model, reasoning


# Example usage and testing
if __name__ == "__main__":
    # Test queries
    test_queries = [
        "What is RNA?",
        "Design a protocol for RNA extraction from mouse brain tissue",
        "Why did my PCR fail?",
        "Compare and contrast CRISPR-Cas9 and CRISPR-Cas12",
        "How do I troubleshoot protein expression issues?",
        "List the steps for Western blot",
        "Explain the mechanism of RNA interference and design an experiment to test its efficacy",
        "What is the melting temperature of this primer: ATCGATCGATCG?",
    ]
    
    classifier = ResearchQueryClassifier()
    example_tiers = {
        'small': 'gpt-4.1-mini',
        'default': 'o4-mini', 
        'large': 'gpt-4.1',
        'advanced': 'o3'
    }
    
    print("Research Query Classification Examples:\n")
    for query in test_queries:
        model, reasoning = classifier.get_model_for_query(query, example_tiers)
        tier, conf, _ = classifier.classify_query(query)
        print(f"Query: {query}")
        print(f"  → Model: {model} (tier: {tier}, confidence: {conf:.2f})")
        print(f"  → Reasoning: {reasoning}\n")