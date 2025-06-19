"""
Insight Validation Service
Validates and scores the quality of generated insights
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from django.core.cache import cache

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from api.models import Document, QueryHistory
from api.search.services import SearchService
from api.intelligence.cross_paper_insights import CrossPaperInsight

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of insight validation"""
    is_valid: bool
    confidence_score: float
    reasoning: str
    suggested_improvements: List[str]
    evidence_quality: float
    novelty_verified: bool


class InsightValidator:
    """Validates the quality and accuracy of generated insights"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name=settings.LLM_MODEL,
            temperature=0.1,  # Low temperature for validation
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.search_service = SearchService()
        
    def validate_insight(
        self,
        insight: CrossPaperInsight,
        check_sources: bool = True,
        check_novelty: bool = True
    ) -> ValidationResult:
        """Validate a single insight"""
        try:
            # Check evidence quality
            evidence_score = self._validate_evidence(insight)
            
            # Verify claims against sources
            source_verification = 1.0
            if check_sources:
                source_verification = self._verify_against_sources(insight)
            
            # Check novelty
            novelty_verified = True
            if check_novelty:
                novelty_verified = self._verify_novelty(insight)
            
            # LLM-based validation
            llm_validation = self._llm_validate(insight)
            
            # Calculate overall score
            confidence_score = (
                evidence_score * 0.3 +
                source_verification * 0.4 +
                llm_validation["score"] * 0.3
            )
            
            # Determine validity
            is_valid = (
                confidence_score >= 0.7 and
                evidence_score >= 0.6 and
                source_verification >= 0.6
            )
            
            return ValidationResult(
                is_valid=is_valid,
                confidence_score=confidence_score,
                reasoning=llm_validation["reasoning"],
                suggested_improvements=llm_validation["improvements"],
                evidence_quality=evidence_score,
                novelty_verified=novelty_verified
            )
            
        except Exception as e:
            logger.error(f"Error validating insight: {str(e)}")
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                reasoning=f"Validation error: {str(e)}",
                suggested_improvements=["Fix validation errors"],
                evidence_quality=0.0,
                novelty_verified=False
            )
    
    def validate_batch(
        self,
        insights: List[CrossPaperInsight],
        parallel: bool = True
    ) -> List[ValidationResult]:
        """Validate multiple insights"""
        results = []
        
        for insight in insights:
            # Check cache
            cache_key = f"insight_validation:{insight.title[:50]}"
            cached = cache.get(cache_key)
            
            if cached:
                results.append(cached)
            else:
                result = self.validate_insight(insight)
                results.append(result)
                cache.set(cache_key, result, timeout=3600)
        
        return results
    
    def _validate_evidence(self, insight: CrossPaperInsight) -> float:
        """Validate the quality of evidence"""
        score = 0.0
        
        # Check number of evidence snippets
        if len(insight.evidence_snippets) >= 2:
            score += 0.3
        
        # Check evidence length and quality
        avg_length = np.mean([len(e) for e in insight.evidence_snippets])
        if avg_length >= 50:
            score += 0.2
        
        # Check if evidence is specific (contains numbers, proteins, etc.)
        specific_terms = 0
        for evidence in insight.evidence_snippets:
            if any(char.isdigit() for char in evidence):
                specific_terms += 1
            if any(term in evidence.lower() for term in ["protein", "gene", "pathway", "p<", "n="]):
                specific_terms += 1
        
        if specific_terms >= len(insight.evidence_snippets):
            score += 0.3
        
        # Check paper involvement
        if len(insight.papers_involved) >= 2:
            score += 0.2
        
        return min(1.0, score)
    
    def _verify_against_sources(self, insight: CrossPaperInsight) -> float:
        """Verify claims against source papers"""
        try:
            # Get source papers
            papers = Document.objects.filter(doc_id__in=insight.papers_involved)
            if not papers:
                return 0.5  # Can't verify without sources
            
            verification_prompt = ChatPromptTemplate.from_template("""
            Verify this insight against the source papers:
            
            Insight: {insight_description}
            Evidence claimed: {evidence}
            
            Source paper excerpts:
            {paper_excerpts}
            
            Rate how well the sources support the insight (0-1) and explain.
            Return JSON with: score, supported_claims, unsupported_claims
            """)
            
            # Prepare paper excerpts
            paper_excerpts = []
            for paper in papers[:3]:  # Check up to 3 papers
                # Find relevant sections
                relevant_content = self._find_relevant_sections(
                    paper.content, insight.evidence_snippets
                )
                paper_excerpts.append(f"{paper.title}:\n{relevant_content}")
            
            response = self.llm.invoke(
                verification_prompt.format(
                    insight_description=insight.description,
                    evidence="\n".join(insight.evidence_snippets),
                    paper_excerpts="\n\n".join(paper_excerpts)
                )
            )
            
            result = self._parse_json_response(response.content)
            return result.get("score", 0.5)
            
        except Exception as e:
            logger.error(f"Error verifying sources: {str(e)}")
            return 0.5
    
    def _verify_novelty(self, insight: CrossPaperInsight) -> bool:
        """Verify the novelty of the insight"""
        try:
            # Search for similar existing insights
            similar_query = f"{insight.insight_type} {insight.title[:50]}"
            
            # Check query history for similar insights
            similar_queries = QueryHistory.objects.filter(
                query__icontains=similar_query[:30]
            ).count()
            
            # If many similar queries exist, insight might not be novel
            if similar_queries > 5:
                return False
            
            # Check if the specific connection has been made before
            # This is simplified - real implementation would check publications
            return True
            
        except Exception as e:
            logger.error(f"Error verifying novelty: {str(e)}")
            return True
    
    def _llm_validate(self, insight: CrossPaperInsight) -> Dict:
        """Use LLM to validate insight quality"""
        validation_prompt = ChatPromptTemplate.from_template("""
        Evaluate the quality of this research insight:
        
        Type: {insight_type}
        Title: {title}
        Description: {description}
        Evidence: {evidence}
        Impact: {impact}
        Actions: {actions}
        
        Assess:
        1. Is the insight logically sound?
        2. Is it actionable for researchers?
        3. Does the evidence support the claims?
        4. Is the potential impact realistic?
        
        Return JSON with:
        - score (0-1)
        - reasoning
        - improvements (list of suggestions)
        """)
        
        try:
            response = self.llm.invoke(
                validation_prompt.format(
                    insight_type=insight.insight_type,
                    title=insight.title,
                    description=insight.description,
                    evidence="\n".join(insight.evidence_snippets[:3]),
                    impact=insight.potential_impact,
                    actions="\n".join(insight.suggested_actions[:3])
                )
            )
            
            result = self._parse_json_response(response.content)
            return {
                "score": result.get("score", 0.5),
                "reasoning": result.get("reasoning", ""),
                "improvements": result.get("improvements", [])
            }
            
        except Exception as e:
            logger.error(f"LLM validation error: {str(e)}")
            return {
                "score": 0.5,
                "reasoning": "Validation error",
                "improvements": []
            }
    
    def _find_relevant_sections(
        self,
        content: str,
        evidence_snippets: List[str]
    ) -> str:
        """Find relevant sections in paper content"""
        relevant_sections = []
        content_lower = content.lower()
        
        for evidence in evidence_snippets:
            # Find key terms from evidence
            key_terms = [
                term for term in evidence.lower().split()
                if len(term) > 4 and term not in ["the", "and", "for", "with"]
            ][:5]
            
            # Find sentences containing key terms
            sentences = content.split(".")
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(term in sentence_lower for term in key_terms):
                    relevant_sections.append(sentence.strip())
                    if len(relevant_sections) >= 5:
                        break
        
        return ". ".join(relevant_sections[:5])
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response"""
        import re
        import json
        
        try:
            # Find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
        return {}


class InsightRanker:
    """Ranks insights by relevance and quality"""
    
    def __init__(self):
        self.validator = InsightValidator()
        
    def rank_insights(
        self,
        insights: List[CrossPaperInsight],
        user_query: Optional[str] = None,
        user_preferences: Optional[Dict] = None
    ) -> List[Tuple[CrossPaperInsight, float]]:
        """Rank insights by relevance and quality"""
        ranked_insights = []
        
        for insight in insights:
            # Calculate base score
            score = insight.confidence_score * insight.novelty_score
            
            # Adjust for user query relevance
            if user_query:
                relevance = self._calculate_query_relevance(insight, user_query)
                score *= (0.5 + 0.5 * relevance)
            
            # Adjust for user preferences
            if user_preferences:
                preference_score = self._calculate_preference_score(
                    insight, user_preferences
                )
                score *= (0.7 + 0.3 * preference_score)
            
            # Validate and adjust score
            validation = self.validator.validate_insight(insight, check_sources=False)
            if validation.is_valid:
                score *= validation.confidence_score
            else:
                score *= 0.5
            
            ranked_insights.append((insight, score))
        
        # Sort by score
        ranked_insights.sort(key=lambda x: x[1], reverse=True)
        
        return ranked_insights
    
    def _calculate_query_relevance(
        self,
        insight: CrossPaperInsight,
        query: str
    ) -> float:
        """Calculate relevance to user query"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        # Combine insight text
        insight_text = f"{insight.title} {insight.description} {' '.join(insight.evidence_snippets[:2])}"
        
        # Calculate similarity
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([query, insight_text])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        return similarity
    
    def _calculate_preference_score(
        self,
        insight: CrossPaperInsight,
        preferences: Dict
    ) -> float:
        """Calculate score based on user preferences"""
        score = 0.0
        
        # Check insight type preference
        preferred_types = preferences.get("preferred_insight_types", [])
        if insight.insight_type in preferred_types:
            score += 0.4
        
        # Check research area preference
        preferred_areas = preferences.get("research_areas", [])
        insight_text_lower = f"{insight.title} {insight.description}".lower()
        
        for area in preferred_areas:
            if area.lower() in insight_text_lower:
                score += 0.3
                break
        
        # Check impact level preference
        min_impact = preferences.get("min_impact_level", 0.5)
        if insight.confidence_score >= min_impact:
            score += 0.3
        
        return min(1.0, score)