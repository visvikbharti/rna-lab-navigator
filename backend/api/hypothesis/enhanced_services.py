"""
Enhanced Hypothesis Mode Services
Integrates with Enhanced RAG for advanced reasoning and knowledge synthesis
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from django.conf import settings
from openai import OpenAI

from api.models import Document, QueryHistory
from api.rag.enhanced_rag import get_enhanced_rag_pipeline
from api.search.real_rag import search_documents
from .services import HypothesisService
from .prompts import HYPOTHESIS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


@dataclass
class HypothesisContext:
    """Context for hypothesis exploration"""
    research_area: str
    lab_expertise: List[str]
    available_equipment: List[str]
    previous_experiments: List[Dict]
    constraints: Dict[str, any]


class EnhancedHypothesisService:
    """Enhanced service for hypothesis exploration with reasoning and knowledge synthesis"""
    
    def __init__(self):
        self.base_service = HypothesisService()
        self.enhanced_rag = get_enhanced_rag_pipeline()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
    async def explore_hypothesis_with_reasoning(
        self,
        question: str,
        session_id: str,
        user_context: Optional[Dict] = None,
        hypothesis_context: Optional[HypothesisContext] = None
    ) -> Dict:
        """
        Explore a hypothesis using enhanced RAG with chain-of-thought reasoning
        
        Args:
            question: The hypothesis or "what if" question
            session_id: Session ID for conversation memory
            user_context: User context including expertise level
            hypothesis_context: Specific context for hypothesis exploration
            
        Returns:
            Dict containing detailed analysis with reasoning trace
        """
        try:
            # Step 1: Use enhanced RAG to decompose the hypothesis question
            enhanced_query = self._prepare_hypothesis_query(question, hypothesis_context)
            
            rag_result = await self.enhanced_rag.process_query(
                query=enhanced_query,
                session_id=session_id,
                user_context=user_context
            )
            
            # Step 2: Extract key concepts and related research
            concepts = self._extract_research_concepts(question, rag_result['entities'])
            related_research = await self._find_related_research(concepts, session_id)
            
            # Step 3: Perform multi-stage hypothesis analysis
            analysis_stages = await self._multi_stage_analysis(
                question=question,
                rag_context=rag_result['answer'],
                related_research=related_research,
                hypothesis_context=hypothesis_context
            )
            
            # Step 4: Generate experimental design suggestions
            experimental_design = await self._generate_experimental_design(
                hypothesis=question,
                analysis=analysis_stages,
                lab_context=hypothesis_context
            )
            
            # Step 5: Identify knowledge gaps and future directions
            knowledge_synthesis = await self._synthesize_knowledge_gaps(
                hypothesis=question,
                current_knowledge=rag_result['answer'],
                related_work=related_research
            )
            
            # Step 6: Calculate comprehensive confidence scores
            confidence_analysis = self._calculate_enhanced_confidence(
                rag_confidence=rag_result['confidence'],
                analysis_depth=len(analysis_stages),
                evidence_count=len(related_research),
                experimental_feasibility=experimental_design.get('feasibility_score', 0.5)
            )
            
            # Compile comprehensive result
            result = {
                'success': True,
                'question': question,
                'reasoning_trace': rag_result.get('reasoning_trace', []),
                'analysis': {
                    'summary': analysis_stages.get('synthesis', ''),
                    'scientific_basis': analysis_stages.get('scientific_basis', ''),
                    'feasibility': analysis_stages.get('feasibility', ''),
                    'innovation_assessment': analysis_stages.get('innovation', ''),
                    'risk_analysis': analysis_stages.get('risks', '')
                },
                'experimental_design': experimental_design,
                'related_research': related_research[:5],  # Top 5 related papers
                'knowledge_synthesis': knowledge_synthesis,
                'confidence_analysis': confidence_analysis,
                'extracted_concepts': concepts,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Update knowledge graph with hypothesis exploration
            await self._update_knowledge_graph(question, concepts, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced hypothesis exploration: {str(e)}")
            # Fallback to basic hypothesis service
            return self.base_service.explore_hypothesis(question)
    
    def _prepare_hypothesis_query(self, question: str, context: Optional[HypothesisContext]) -> str:
        """Prepare enhanced query with hypothesis context"""
        enhanced_query = f"Research hypothesis: {question}"
        
        if context:
            if context.research_area:
                enhanced_query += f"\nResearch area: {context.research_area}"
            if context.lab_expertise:
                enhanced_query += f"\nLab expertise: {', '.join(context.lab_expertise)}"
            if context.constraints:
                enhanced_query += f"\nConstraints: {json.dumps(context.constraints)}"
        
        return enhanced_query
    
    def _extract_research_concepts(self, question: str, entities: List[str]) -> List[Dict]:
        """Extract key research concepts from hypothesis"""
        concepts = []
        
        # Start with detected entities
        for entity in entities:
            concepts.append({
                'concept': entity,
                'type': 'entity',
                'relevance': 1.0
            })
        
        # Add hypothesis-specific concept extraction
        hypothesis_keywords = [
            'mechanism', 'pathway', 'interaction', 'regulation',
            'expression', 'modification', 'function', 'structure'
        ]
        
        question_lower = question.lower()
        for keyword in hypothesis_keywords:
            if keyword in question_lower:
                concepts.append({
                    'concept': keyword,
                    'type': 'hypothesis_keyword',
                    'relevance': 0.8
                })
        
        return concepts
    
    async def _find_related_research(self, concepts: List[Dict], session_id: str) -> List[Dict]:
        """Find research related to the hypothesis concepts"""
        related_papers = []
        
        # Search for papers related to each concept
        for concept in concepts[:3]:  # Top 3 concepts
            search_results = search_documents(
                query=f"{concept['concept']} mechanism study",
                doc_type='paper',
                top_k=3
            )
            
            for result in search_results:
                # Enhance with relevance scoring
                result['concept_relevance'] = concept['relevance']
                result['matched_concept'] = concept['concept']
                related_papers.append(result)
        
        # Deduplicate and sort by relevance
        seen_ids = set()
        unique_papers = []
        for paper in sorted(related_papers, key=lambda x: x.get('score', 0) * x.get('concept_relevance', 1), reverse=True):
            if paper['id'] not in seen_ids:
                seen_ids.add(paper['id'])
                unique_papers.append(paper)
        
        return unique_papers
    
    async def _multi_stage_analysis(
        self,
        question: str,
        rag_context: str,
        related_research: List[Dict],
        hypothesis_context: Optional[HypothesisContext]
    ) -> Dict:
        """Perform multi-stage analysis of the hypothesis"""
        
        # Format related research context
        research_context = "\n".join([
            f"[{r.get('title', 'Unknown')}]: {r.get('snippet', '')[:200]}..."
            for r in related_research[:3]
        ])
        
        # Stage 1: Scientific basis analysis
        scientific_prompt = f"""
        Analyze the scientific basis for this hypothesis:
        {question}
        
        Current knowledge from lab documents:
        {rag_context}
        
        Related research:
        {research_context}
        
        Provide:
        1. Theoretical foundation
        2. Supporting evidence from literature
        3. Potential molecular mechanisms
        4. Knowledge gaps
        """
        
        scientific_analysis = await self._query_llm_async(scientific_prompt)
        
        # Stage 2: Feasibility assessment
        feasibility_prompt = f"""
        Assess the experimental feasibility of testing this hypothesis:
        {question}
        
        Lab context:
        - Expertise areas: {hypothesis_context.lab_expertise if hypothesis_context else 'RNA biology, CRISPR'}
        - Available equipment: {hypothesis_context.available_equipment if hypothesis_context else 'Standard molecular biology lab'}
        
        Consider:
        1. Technical requirements
        2. Time and resource estimates
        3. Required expertise
        4. Potential bottlenecks
        """
        
        feasibility_analysis = await self._query_llm_async(feasibility_prompt)
        
        # Stage 3: Innovation assessment
        innovation_prompt = f"""
        Evaluate the innovation potential of this hypothesis:
        {question}
        
        Context: {rag_context}
        
        Assess:
        1. Novelty compared to existing research
        2. Potential impact on the field
        3. Translational potential
        4. Intellectual property considerations
        """
        
        innovation_analysis = await self._query_llm_async(innovation_prompt)
        
        # Stage 4: Risk analysis
        risk_prompt = f"""
        Identify risks and challenges for this hypothesis:
        {question}
        
        Consider:
        1. Technical risks
        2. Biological variability
        3. Reproducibility concerns
        4. Ethical considerations
        5. Alternative explanations
        """
        
        risk_analysis = await self._query_llm_async(risk_prompt)
        
        # Synthesize all analyses
        synthesis_prompt = f"""
        Synthesize a comprehensive assessment of this hypothesis:
        {question}
        
        Scientific basis summary: {scientific_analysis[:500]}
        Feasibility summary: {feasibility_analysis[:500]}
        Innovation summary: {innovation_analysis[:500]}
        Risk summary: {risk_analysis[:500]}
        
        Provide a balanced, actionable recommendation.
        """
        
        synthesis = await self._query_llm_async(synthesis_prompt)
        
        return {
            'scientific_basis': scientific_analysis,
            'feasibility': feasibility_analysis,
            'innovation': innovation_analysis,
            'risks': risk_analysis,
            'synthesis': synthesis
        }
    
    async def _generate_experimental_design(
        self,
        hypothesis: str,
        analysis: Dict,
        lab_context: Optional[HypothesisContext]
    ) -> Dict:
        """Generate detailed experimental design suggestions"""
        
        design_prompt = f"""
        Design experiments to test this hypothesis:
        {hypothesis}
        
        Based on analysis:
        {analysis.get('synthesis', '')[:1000]}
        
        Lab capabilities:
        - Expertise: {lab_context.lab_expertise if lab_context else 'RNA biology, molecular techniques'}
        - Equipment: {lab_context.available_equipment if lab_context else 'Standard molecular biology equipment'}
        
        Provide:
        1. Primary experiment design
        2. Control experiments
        3. Expected outcomes
        4. Data analysis plan
        5. Timeline estimate
        6. Alternative approaches
        """
        
        experimental_plan = await self._query_llm_async(design_prompt)
        
        # Parse experimental design
        design_components = self._parse_experimental_design(experimental_plan)
        
        # Calculate feasibility score
        feasibility_score = self._calculate_feasibility_score(design_components, lab_context)
        
        return {
            'primary_design': design_components.get('primary', ''),
            'controls': design_components.get('controls', []),
            'expected_outcomes': design_components.get('outcomes', ''),
            'analysis_plan': design_components.get('analysis', ''),
            'timeline': design_components.get('timeline', ''),
            'alternatives': design_components.get('alternatives', []),
            'feasibility_score': feasibility_score,
            'raw_plan': experimental_plan
        }
    
    async def _synthesize_knowledge_gaps(
        self,
        hypothesis: str,
        current_knowledge: str,
        related_work: List[Dict]
    ) -> Dict:
        """Identify knowledge gaps and future research directions"""
        
        gap_prompt = f"""
        Identify knowledge gaps related to this hypothesis:
        {hypothesis}
        
        Current understanding:
        {current_knowledge[:1000]}
        
        Related work shows:
        {self._summarize_related_work(related_work)}
        
        Identify:
        1. Critical knowledge gaps
        2. Technical limitations to address
        3. Future research directions
        4. Potential collaborations needed
        5. Resources required for advancement
        """
        
        gap_analysis = await self._query_llm_async(gap_prompt)
        
        return {
            'knowledge_gaps': self._extract_gaps(gap_analysis),
            'future_directions': self._extract_directions(gap_analysis),
            'collaboration_opportunities': self._extract_collaborations(gap_analysis),
            'resource_needs': self._extract_resources(gap_analysis),
            'full_analysis': gap_analysis
        }
    
    def _calculate_enhanced_confidence(
        self,
        rag_confidence: float,
        analysis_depth: int,
        evidence_count: int,
        experimental_feasibility: float
    ) -> Dict:
        """Calculate comprehensive confidence scores"""
        
        # Weight different factors
        weights = {
            'rag_confidence': 0.3,
            'analysis_depth': 0.2,
            'evidence_support': 0.3,
            'experimental_feasibility': 0.2
        }
        
        # Normalize scores
        normalized_scores = {
            'rag_confidence': rag_confidence,
            'analysis_depth': min(analysis_depth / 5, 1.0),  # Max 5 stages
            'evidence_support': min(evidence_count / 10, 1.0),  # Max 10 papers
            'experimental_feasibility': experimental_feasibility
        }
        
        # Calculate weighted overall score
        overall = sum(
            normalized_scores[key] * weights[key]
            for key in weights
        )
        
        return {
            'overall': overall,
            'components': normalized_scores,
            'interpretation': self._interpret_confidence(overall),
            'recommendations': self._confidence_recommendations(normalized_scores)
        }
    
    async def _update_knowledge_graph(self, hypothesis: str, concepts: List[Dict], result: Dict):
        """Update the knowledge graph with hypothesis exploration results"""
        try:
            kg = self.enhanced_rag.knowledge_graph
            
            # Add hypothesis as an entity
            kg.add_entity(
                entity=f"Hypothesis: {hypothesis[:100]}",
                entity_type="hypothesis",
                document_id=f"hypothesis_{datetime.now().timestamp()}"
            )
            
            # Add relationships between hypothesis and concepts
            for concept in concepts:
                kg.add_relation(
                    source=f"Hypothesis: {hypothesis[:100]}",
                    target=concept['concept'],
                    relation_type="explores",
                    strength=concept['relevance']
                )
            
            # Add relationships to related research
            for paper in result.get('related_research', [])[:3]:
                kg.add_relation(
                    source=f"Hypothesis: {hypothesis[:100]}",
                    target=paper.get('title', 'Unknown'),
                    relation_type="supported_by",
                    strength=paper.get('score', 0.5)
                )
                
        except Exception as e:
            logger.error(f"Error updating knowledge graph: {e}")
    
    async def _query_llm_async(self, prompt: str, temperature: float = 0.7) -> str:
        """Async wrapper for LLM queries"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": HYPOTHESIS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=1500
        )
        return response.choices[0].message.content
    
    def _parse_experimental_design(self, design_text: str) -> Dict:
        """Parse experimental design into components"""
        components = {
            'primary': '',
            'controls': [],
            'outcomes': '',
            'analysis': '',
            'timeline': '',
            'alternatives': []
        }
        
        lines = design_text.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'primary' in line_lower and 'experiment' in line_lower:
                current_section = 'primary'
            elif 'control' in line_lower:
                current_section = 'controls'
            elif 'outcome' in line_lower or 'expect' in line_lower:
                current_section = 'outcomes'
            elif 'analysis' in line_lower or 'data' in line_lower:
                current_section = 'analysis'
            elif 'timeline' in line_lower or 'time' in line_lower:
                current_section = 'timeline'
            elif 'alternative' in line_lower:
                current_section = 'alternatives'
            elif current_section and line.strip():
                if current_section in ['controls', 'alternatives']:
                    if line.strip().startswith(('-', '•', '*', '1', '2', '3')):
                        components[current_section].append(line.strip())
                else:
                    components[current_section] += line + '\n'
        
        return components
    
    def _calculate_feasibility_score(self, design: Dict, lab_context: Optional[HypothesisContext]) -> float:
        """Calculate experimental feasibility score"""
        score = 0.5  # Base score
        
        # Adjust based on design completeness
        if design.get('primary'):
            score += 0.1
        if design.get('controls'):
            score += 0.1
        if design.get('timeline'):
            score += 0.1
        if design.get('analysis'):
            score += 0.1
        
        # Adjust based on lab context
        if lab_context:
            if lab_context.available_equipment:
                score += 0.05
            if lab_context.lab_expertise:
                score += 0.05
        
        return min(score, 0.95)
    
    def _summarize_related_work(self, papers: List[Dict]) -> str:
        """Summarize related research papers"""
        summaries = []
        for paper in papers[:3]:
            summaries.append(
                f"- {paper.get('title', 'Unknown')}: {paper.get('snippet', '')[:100]}..."
            )
        return "\n".join(summaries)
    
    def _extract_gaps(self, analysis: str) -> List[str]:
        """Extract knowledge gaps from analysis"""
        gaps = []
        lines = analysis.split('\n')
        in_gaps_section = False
        
        for line in lines:
            if 'gap' in line.lower() or 'unknown' in line.lower() or 'unclear' in line.lower():
                in_gaps_section = True
            elif in_gaps_section and line.strip().startswith(('-', '•', '*', '1', '2')):
                gaps.append(line.strip())
            elif in_gaps_section and not line.strip():
                in_gaps_section = False
        
        return gaps[:5]  # Top 5 gaps
    
    def _extract_directions(self, analysis: str) -> List[str]:
        """Extract future research directions"""
        directions = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['future', 'direction', 'next step', 'follow-up']):
                directions.append(line.strip())
        
        return directions[:5]
    
    def _extract_collaborations(self, analysis: str) -> List[str]:
        """Extract collaboration opportunities"""
        collaborations = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['collaborat', 'partner', 'expertise needed']):
                collaborations.append(line.strip())
        
        return collaborations[:3]
    
    def _extract_resources(self, analysis: str) -> List[str]:
        """Extract resource needs"""
        resources = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['resource', 'require', 'need', 'equipment']):
                resources.append(line.strip())
        
        return resources[:5]
    
    def _interpret_confidence(self, score: float) -> str:
        """Interpret confidence score"""
        if score >= 0.8:
            return "High confidence - Strong evidence and feasible approach"
        elif score >= 0.6:
            return "Moderate confidence - Good foundation but some uncertainties"
        elif score >= 0.4:
            return "Low confidence - Limited evidence or challenging feasibility"
        else:
            return "Very low confidence - Significant gaps or obstacles"
    
    def _confidence_recommendations(self, scores: Dict) -> List[str]:
        """Generate recommendations based on confidence components"""
        recommendations = []
        
        if scores['rag_confidence'] < 0.6:
            recommendations.append("Gather more background literature and lab data")
        if scores['analysis_depth'] < 0.6:
            recommendations.append("Conduct deeper preliminary analysis")
        if scores['evidence_support'] < 0.6:
            recommendations.append("Search for more supporting evidence")
        if scores['experimental_feasibility'] < 0.6:
            recommendations.append("Refine experimental approach or seek additional resources")
        
        return recommendations


# Singleton instance
_enhanced_hypothesis_service = None

def get_enhanced_hypothesis_service() -> EnhancedHypothesisService:
    """Get singleton instance of enhanced hypothesis service"""
    global _enhanced_hypothesis_service
    if _enhanced_hypothesis_service is None:
        _enhanced_hypothesis_service = EnhancedHypothesisService()
    return _enhanced_hypothesis_service