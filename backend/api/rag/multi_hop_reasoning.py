"""
Multi-Hop Reasoning Engine for RNA Lab Navigator
Breaks down complex queries into reasoning steps and validates across sources
"""

import json
import asyncio
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import openai
from django.conf import settings

from ..search.real_rag import search_documents, generate_answer_with_llm
from ..models import QueryHistory


@dataclass
class SubQuery:
    """Represents a sub-question derived from a complex query"""
    id: int
    question: str
    query_type: str  # 'definition', 'comparison', 'property', 'application'
    priority: int
    dependencies: List[int] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class Evidence:
    """Evidence gathered for a sub-query"""
    sub_query_id: int
    documents: List[Dict]
    answer: str
    confidence: float
    sources: List[Dict]
    contradictions: List[Dict] = None
    
    def __post_init__(self):
        if self.contradictions is None:
            self.contradictions = []


@dataclass
class ReasoningStep:
    """A step in the reasoning chain"""
    step_number: int
    description: str
    evidence: Evidence
    conclusion: str
    confidence: float


@dataclass
class EnhancedAnswer:
    """Enhanced answer with reasoning trace"""
    answer: str
    reasoning_trace: List[ReasoningStep]
    overall_confidence: float
    sources: List[Dict]
    knowledge_gaps: List[str]
    follow_up_questions: List[str]


class QueryDecomposer:
    """Breaks down complex queries into sub-questions"""
    
    def decompose(self, query: str) -> List[SubQuery]:
        """
        Decompose a complex query into sub-questions using GPT-4
        """
        prompt = f"""
        You are a research assistant helping to break down complex scientific queries.
        
        Break down this research query into simpler sub-questions that need to be answered:
        Query: "{query}"
        
        For each sub-question, identify:
        1. The question itself
        2. The type: 'definition' (What is X?), 'comparison' (X vs Y), 'property' (characteristics of X), or 'application' (How is X used?)
        3. Priority (1-5, where 1 is highest)
        4. Dependencies (which other sub-questions must be answered first)
        
        Return as JSON array with format:
        [
            {{
                "id": 1,
                "question": "What is FnCas9?",
                "query_type": "definition",
                "priority": 1,
                "dependencies": []
            }},
            ...
        ]
        
        Focus on creating 3-7 targeted sub-questions that together fully address the main query.
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a scientific research assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            sub_queries_data = json.loads(response.choices[0].message.content)
            
            # Handle both dict with 'questions' key and direct array
            if isinstance(sub_queries_data, dict) and 'questions' in sub_queries_data:
                sub_queries_data = sub_queries_data['questions']
            elif isinstance(sub_queries_data, dict):
                # If it's a dict but not the expected format, extract values
                sub_queries_data = list(sub_queries_data.values())
            
            sub_queries = []
            for sq in sub_queries_data:
                sub_queries.append(SubQuery(
                    id=sq.get('id', len(sub_queries) + 1),
                    question=sq['question'],
                    query_type=sq.get('query_type', 'definition'),
                    priority=sq.get('priority', 3),
                    dependencies=sq.get('dependencies', [])
                ))
            
            return sorted(sub_queries, key=lambda x: x.priority)
            
        except Exception as e:
            print(f"Error decomposing query: {e}")
            # Fallback to simple decomposition
            return [SubQuery(
                id=1,
                question=query,
                query_type='general',
                priority=1,
                dependencies=[]
            )]


class EvidenceGatherer:
    """Gathers and validates evidence for sub-queries"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def gather_evidence(self, sub_queries: List[SubQuery], doc_type: str = "all") -> Dict[int, Evidence]:
        """
        Gather evidence for all sub-queries in parallel
        """
        evidence_map = {}
        
        # Group queries by dependencies
        independent_queries = [sq for sq in sub_queries if not sq.dependencies]
        dependent_queries = [sq for sq in sub_queries if sq.dependencies]
        
        # First, process independent queries in parallel
        futures = {
            self.executor.submit(self._search_for_evidence, sq, doc_type): sq 
            for sq in independent_queries
        }
        
        for future in as_completed(futures):
            sub_query = futures[future]
            try:
                evidence = future.result()
                evidence_map[sub_query.id] = evidence
            except Exception as e:
                print(f"Error gathering evidence for {sub_query.question}: {e}")
                evidence_map[sub_query.id] = Evidence(
                    sub_query_id=sub_query.id,
                    documents=[],
                    answer="Unable to gather evidence",
                    confidence=0.0,
                    sources=[]
                )
        
        # Then process dependent queries
        for sq in dependent_queries:
            # Wait for dependencies
            deps_ready = all(dep_id in evidence_map for dep_id in sq.dependencies)
            if deps_ready:
                evidence = self._search_for_evidence(sq, doc_type, evidence_map)
                evidence_map[sq.id] = evidence
        
        return evidence_map
    
    def _search_for_evidence(self, sub_query: SubQuery, doc_type: str, 
                           prior_evidence: Dict[int, Evidence] = None) -> Evidence:
        """
        Search for evidence for a single sub-query
        """
        # Search for relevant documents
        search_results = search_documents(sub_query.question, doc_type, top_k=5)
        
        # Generate answer using the search results
        if search_results:
            answer_data = generate_answer_with_llm(sub_query.question, search_results)
            
            # Extract unique sources
            sources = []
            seen_sources = set()
            for result in search_results[:3]:
                source_key = f"{result['title']}_{result['author']}"
                if source_key not in seen_sources:
                    seen_sources.add(source_key)
                    sources.append({
                        'title': result['title'],
                        'author': result['author'],
                        'year': result['year'],
                        'type': result['type']
                    })
            
            return Evidence(
                sub_query_id=sub_query.id,
                documents=search_results,
                answer=answer_data['answer'],
                confidence=answer_data['confidence_score'],
                sources=sources
            )
        else:
            return Evidence(
                sub_query_id=sub_query.id,
                documents=[],
                answer="No relevant information found in the documents.",
                confidence=0.1,
                sources=[]
            )
    
    def cross_validate_evidence(self, evidence_map: Dict[int, Evidence]) -> Dict[int, Evidence]:
        """
        Cross-validate evidence across different sub-queries to find contradictions
        """
        # For each piece of evidence, check if it contradicts others
        for id1, ev1 in evidence_map.items():
            for id2, ev2 in evidence_map.items():
                if id1 != id2:
                    # Check for contradictions using GPT
                    contradiction = self._check_contradiction(ev1.answer, ev2.answer)
                    if contradiction:
                        ev1.contradictions.append({
                            'with_query_id': id2,
                            'description': contradiction
                        })
        
        return evidence_map
    
    def _check_contradiction(self, answer1: str, answer2: str) -> Optional[str]:
        """
        Check if two answers contradict each other
        """
        # Simple implementation - in production, use GPT for semantic analysis
        # For now, return None (no contradiction)
        return None


class ReasoningChainBuilder:
    """Builds a logical reasoning chain from evidence"""
    
    def build_chain(self, query: str, sub_queries: List[SubQuery], 
                    evidence_map: Dict[int, Evidence]) -> List[ReasoningStep]:
        """
        Build a reasoning chain that leads to the final answer
        """
        reasoning_steps = []
        
        for i, sub_query in enumerate(sub_queries):
            if sub_query.id in evidence_map:
                evidence = evidence_map[sub_query.id]
                
                # Create reasoning step
                step = ReasoningStep(
                    step_number=i + 1,
                    description=f"To answer '{sub_query.question}'",
                    evidence=evidence,
                    conclusion=self._extract_conclusion(evidence),
                    confidence=evidence.confidence
                )
                reasoning_steps.append(step)
        
        return reasoning_steps
    
    def _extract_conclusion(self, evidence: Evidence) -> str:
        """
        Extract the key conclusion from evidence
        """
        # Simple extraction - take first sentence or key finding
        sentences = evidence.answer.split('.')
        return sentences[0] + '.' if sentences else evidence.answer


class AnswerSynthesizer:
    """Synthesizes final answer from reasoning chain"""
    
    def synthesize(self, query: str, reasoning_chain: List[ReasoningStep], 
                   sub_queries: List[SubQuery]) -> EnhancedAnswer:
        """
        Synthesize a comprehensive answer from the reasoning chain
        """
        # Build context from reasoning chain
        context = self._build_context(reasoning_chain)
        
        # Generate final answer using GPT-4
        prompt = f"""
        Based on the following step-by-step analysis, provide a comprehensive answer to the question: "{query}"
        
        Analysis steps:
        {context}
        
        Requirements:
        1. Synthesize information from all steps into a coherent answer
        2. Highlight any uncertainties or contradictions
        3. Be specific and cite evidence where appropriate
        4. Keep the answer focused and well-structured
        
        Format:
        - Start with a direct answer to the main question
        - Provide supporting details from the analysis
        - Note any caveats or limitations
        - Suggest areas for further investigation if relevant
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a scientific research assistant providing evidence-based answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            final_answer = response.choices[0].message.content
            
            # Calculate overall confidence
            confidences = [step.confidence for step in reasoning_chain if step.confidence > 0]
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0.5
            
            # Collect all sources
            all_sources = []
            seen_sources = set()
            for step in reasoning_chain:
                for source in step.evidence.sources:
                    source_key = f"{source['title']}_{source['author']}"
                    if source_key not in seen_sources:
                        seen_sources.add(source_key)
                        all_sources.append(source)
            
            # Identify knowledge gaps
            knowledge_gaps = self._identify_knowledge_gaps(reasoning_chain)
            
            # Generate follow-up questions
            follow_up_questions = self._generate_follow_ups(query, reasoning_chain)
            
            return EnhancedAnswer(
                answer=final_answer,
                reasoning_trace=reasoning_chain,
                overall_confidence=overall_confidence,
                sources=all_sources,
                knowledge_gaps=knowledge_gaps,
                follow_up_questions=follow_up_questions
            )
            
        except Exception as e:
            print(f"Error synthesizing answer: {e}")
            # Fallback to simple concatenation
            simple_answer = "\n\n".join([step.evidence.answer for step in reasoning_chain])
            
            return EnhancedAnswer(
                answer=simple_answer,
                reasoning_trace=reasoning_chain,
                overall_confidence=0.5,
                sources=[],
                knowledge_gaps=["Error in synthesis"],
                follow_up_questions=[]
            )
    
    def _build_context(self, reasoning_chain: List[ReasoningStep]) -> str:
        """Build context string from reasoning chain"""
        context_parts = []
        for step in reasoning_chain:
            context_parts.append(
                f"Step {step.step_number}: {step.description}\n"
                f"Finding: {step.conclusion}\n"
                f"Confidence: {step.confidence:.0%}\n"
                f"Sources: {len(step.evidence.sources)} documents\n"
            )
        return "\n".join(context_parts)
    
    def _identify_knowledge_gaps(self, reasoning_chain: List[ReasoningStep]) -> List[str]:
        """Identify what information is missing or uncertain"""
        gaps = []
        for step in reasoning_chain:
            if step.confidence < 0.5:
                gaps.append(f"Low confidence for: {step.description}")
            if not step.evidence.sources:
                gaps.append(f"No sources found for: {step.description}")
        return gaps
    
    def _generate_follow_ups(self, query: str, reasoning_chain: List[ReasoningStep]) -> List[str]:
        """Generate relevant follow-up questions"""
        follow_ups = []
        
        # Add follow-ups for low confidence areas
        for step in reasoning_chain:
            if step.confidence < 0.7:
                follow_ups.append(f"Can you provide more details about {step.description.lower()}?")
        
        # Limit to 3 follow-ups
        return follow_ups[:3]


class MultiHopReasoningEngine:
    """Main engine that orchestrates multi-hop reasoning"""
    
    def __init__(self):
        self.decomposer = QueryDecomposer()
        self.evidence_gatherer = EvidenceGatherer()
        self.chain_builder = ReasoningChainBuilder()
        self.synthesizer = AnswerSynthesizer()
    
    async def process_query(self, query: str, doc_type: str = "all") -> EnhancedAnswer:
        """
        Process a complex query through multi-hop reasoning
        """
        print(f"[Multi-Hop] Processing query: {query}")
        
        # Step 1: Decompose query
        sub_queries = self.decomposer.decompose(query)
        print(f"[Multi-Hop] Decomposed into {len(sub_queries)} sub-queries")
        
        # Step 2: Gather evidence
        evidence_map = self.evidence_gatherer.gather_evidence(sub_queries, doc_type)
        print(f"[Multi-Hop] Gathered evidence for {len(evidence_map)} sub-queries")
        
        # Step 3: Cross-validate evidence
        validated_evidence = self.evidence_gatherer.cross_validate_evidence(evidence_map)
        
        # Step 4: Build reasoning chain
        reasoning_chain = self.chain_builder.build_chain(query, sub_queries, validated_evidence)
        print(f"[Multi-Hop] Built reasoning chain with {len(reasoning_chain)} steps")
        
        # Step 5: Synthesize final answer
        enhanced_answer = self.synthesizer.synthesize(query, reasoning_chain, sub_queries)
        print(f"[Multi-Hop] Synthesized answer with confidence: {enhanced_answer.overall_confidence:.0%}")
        
        return enhanced_answer
    
    def process_query_sync(self, query: str, doc_type: str = "all") -> EnhancedAnswer:
        """
        Synchronous version of process_query for compatibility
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.process_query(query, doc_type))
        finally:
            loop.close()


# Global instance
multi_hop_engine = MultiHopReasoningEngine()