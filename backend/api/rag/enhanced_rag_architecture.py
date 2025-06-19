"""
Enhanced RAG System Architecture
================================

This module implements an advanced RAG system that combines:
1. Conversation Memory with Context Management
2. Multi-stage Reasoning Pipeline
3. Knowledge Graph Integration
4. Intelligent Auto-complete
5. Continuous Learning from Feedback

The system is designed to feel like conversing with a senior researcher
who intimately knows the lab's work, protocols, and research history.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import networkx as nx
from collections import defaultdict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import redis
import json
import logging

from transformers import pipeline
from sentence_transformers import SentenceTransformer
import weaviate
from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation"""
    query: str
    response: str
    documents_used: List[str]
    confidence_score: float
    reasoning_steps: List[str]
    timestamp: datetime
    feedback: Optional[Dict[str, Any]] = None
    entities_mentioned: List[str] = field(default_factory=list)
    
    
@dataclass
class ConversationMemory:
    """Manages conversation context and history"""
    session_id: str
    turns: List[ConversationTurn] = field(default_factory=list)
    user_profile: Dict[str, Any] = field(default_factory=dict)
    research_context: Dict[str, Any] = field(default_factory=dict)
    active_entities: set = field(default_factory=set)
    
    def add_turn(self, turn: ConversationTurn):
        self.turns.append(turn)
        self.active_entities.update(turn.entities_mentioned)
        
    def get_context_window(self, n_turns: int = 5) -> List[ConversationTurn]:
        """Get recent conversation context"""
        return self.turns[-n_turns:] if len(self.turns) >= n_turns else self.turns
        
    def get_relevant_context(self, query: str, embedder) -> str:
        """Extract relevant context from conversation history"""
        if not self.turns:
            return ""
            
        # Embed current query
        query_embedding = embedder.encode([query])[0]
        
        # Score previous turns by relevance
        turn_scores = []
        for turn in self.turns[-10:]:  # Look at last 10 turns
            turn_text = f"{turn.query} {turn.response}"
            turn_embedding = embedder.encode([turn_text])[0]
            score = cosine_similarity([query_embedding], [turn_embedding])[0][0]
            turn_scores.append((score, turn))
            
        # Get top 3 most relevant turns
        turn_scores.sort(key=lambda x: x[0], reverse=True)
        relevant_turns = turn_scores[:3]
        
        context_parts = []
        for score, turn in relevant_turns:
            if score > 0.7:  # Only include highly relevant context
                context_parts.append(f"Previous: {turn.query}\nResponse: {turn.response[:200]}...")
                
        return "\n\n".join(context_parts)


class KnowledgeGraphManager:
    """Manages entity relationships and knowledge graph"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.entity_embeddings = {}
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
    def add_entities_from_document(self, doc_id: str, entities: List[Dict[str, Any]]):
        """Add entities and relationships from a document"""
        for entity in entities:
            # Add node with attributes
            self.graph.add_node(
                entity['name'],
                type=entity['type'],
                documents=[doc_id],
                mentions=1
            )
            
            # Add relationships
            for relation in entity.get('relations', []):
                self.graph.add_edge(
                    entity['name'],
                    relation['target'],
                    relationship=relation['type'],
                    strength=relation.get('strength', 1.0)
                )
                
    def find_related_entities(self, entity: str, max_depth: int = 2) -> List[Tuple[str, str, float]]:
        """Find entities related to the given entity"""
        if entity not in self.graph:
            return []
            
        related = []
        
        # BFS to find related entities
        visited = {entity}
        queue = [(entity, 0, 1.0)]
        
        while queue:
            current, depth, strength = queue.pop(0)
            
            if depth > max_depth:
                continue
                
            # Get neighbors
            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    edge_data = self.graph[current][neighbor]
                    new_strength = strength * edge_data.get('strength', 0.5)
                    
                    related.append((
                        neighbor,
                        edge_data.get('relationship', 'related_to'),
                        new_strength
                    ))
                    
                    queue.append((neighbor, depth + 1, new_strength))
                    
        # Sort by relevance strength
        related.sort(key=lambda x: x[2], reverse=True)
        return related[:10]  # Top 10 related entities
        
    def get_entity_context(self, entities: List[str]) -> Dict[str, Any]:
        """Get enriched context for a list of entities"""
        context = {
            'entities': {},
            'relationships': [],
            'relevant_docs': set()
        }
        
        for entity in entities:
            if entity in self.graph:
                node_data = self.graph.nodes[entity]
                context['entities'][entity] = {
                    'type': node_data.get('type'),
                    'documents': node_data.get('documents', [])
                }
                context['relevant_docs'].update(node_data.get('documents', []))
                
                # Get immediate relationships
                for target in self.graph.neighbors(entity):
                    edge_data = self.graph[entity][target]
                    context['relationships'].append({
                        'source': entity,
                        'target': target,
                        'type': edge_data.get('relationship')
                    })
                    
        return context


class ReasoningPipeline:
    """Multi-stage reasoning pipeline with chain-of-thought"""
    
    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client
        self.reasoning_models = {
            'decomposer': self._init_decomposer(),
            'analyzer': self._init_analyzer(),
            'synthesizer': self._init_synthesizer()
        }
        
    def _init_decomposer(self):
        """Initialize query decomposition prompt"""
        return """You are a research query analyzer. Break down complex queries into sub-questions.
        
Query: {query}
Context: {context}

Decompose this into 2-4 specific sub-questions that would help answer the main query.
Consider the research context and what information would be most valuable.

Output format:
1. [First sub-question]
2. [Second sub-question]
...

Sub-questions:"""

    def _init_analyzer(self):
        """Initialize analysis prompt"""
        return """You are analyzing research information to answer a specific question.

Question: {question}
Retrieved Information:
{information}

Analyze this information and extract:
1. Key findings relevant to the question
2. Experimental methods mentioned
3. Limitations or caveats
4. Connections to other work in the lab

Analysis:"""

    def _init_synthesizer(self):
        """Initialize synthesis prompt"""
        return """You are a senior researcher synthesizing information to provide a comprehensive answer.

Original Query: {query}
Sub-questions and Analyses:
{analyses}

Lab Context:
{lab_context}

Synthesize a comprehensive answer that:
1. Directly addresses the original query
2. Incorporates findings from all sub-questions
3. Highlights connections to lab's previous work
4. Suggests next steps or considerations
5. Maintains scientific accuracy and appropriate uncertainty

Final Answer:"""

    async def reason(self, query: str, context: Dict[str, Any], 
                    retriever, knowledge_graph: KnowledgeGraphManager) -> Dict[str, Any]:
        """Execute multi-stage reasoning pipeline"""
        
        reasoning_trace = []
        
        # Stage 1: Query Decomposition
        decomposition_prompt = self.reasoning_models['decomposer'].format(
            query=query,
            context=json.dumps(context.get('conversation_context', {}))
        )
        
        decomposition_response = await self._llm_call(decomposition_prompt)
        sub_questions = self._parse_sub_questions(decomposition_response)
        reasoning_trace.append({
            'stage': 'decomposition',
            'output': sub_questions
        })
        
        # Stage 2: Parallel Information Retrieval and Analysis
        analyses = await asyncio.gather(*[
            self._analyze_sub_question(sq, retriever, knowledge_graph)
            for sq in sub_questions
        ])
        
        reasoning_trace.append({
            'stage': 'analysis',
            'output': analyses
        })
        
        # Stage 3: Synthesis
        synthesis_prompt = self.reasoning_models['synthesizer'].format(
            query=query,
            analyses=self._format_analyses(sub_questions, analyses),
            lab_context=json.dumps(context.get('lab_context', {}))
        )
        
        final_answer = await self._llm_call(synthesis_prompt)
        reasoning_trace.append({
            'stage': 'synthesis',
            'output': final_answer
        })
        
        return {
            'answer': final_answer,
            'reasoning_trace': reasoning_trace,
            'sub_questions': sub_questions,
            'confidence': self._calculate_confidence(analyses)
        }
        
    async def _analyze_sub_question(self, question: str, retriever, 
                                   knowledge_graph: KnowledgeGraphManager) -> Dict[str, Any]:
        """Analyze a single sub-question"""
        # Retrieve relevant documents
        results = await retriever.search(question, top_k=5)
        
        # Extract entities and get graph context
        entities = self._extract_entities(question)
        graph_context = knowledge_graph.get_entity_context(entities)
        
        # Analyze with LLM
        analysis_prompt = self.reasoning_models['analyzer'].format(
            question=question,
            information=self._format_retrieval_results(results, graph_context)
        )
        
        analysis = await self._llm_call(analysis_prompt)
        
        return {
            'question': question,
            'analysis': analysis,
            'sources': [r['id'] for r in results],
            'entities': entities,
            'confidence': self._score_analysis(analysis, results)
        }
        
    async def _llm_call(self, prompt: str) -> str:
        """Make LLM API call"""
        response = self.llm.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return response.choices[0].message.content
        
    def _parse_sub_questions(self, response: str) -> List[str]:
        """Parse sub-questions from decomposition response"""
        lines = response.strip().split('\n')
        questions = []
        for line in lines:
            if line.strip() and line[0].isdigit():
                # Remove numbering
                question = line.split('.', 1)[1].strip()
                questions.append(question)
        return questions
        
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text (simplified - use NER in production)"""
        # This is a placeholder - implement proper NER
        import re
        # Look for capitalized words/phrases
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return list(set(entities))
        
    def _format_retrieval_results(self, results: List[Dict], 
                                 graph_context: Dict[str, Any]) -> str:
        """Format retrieval results for analysis"""
        formatted = []
        
        for i, result in enumerate(results, 1):
            formatted.append(f"Source {i} ({result['metadata']['title']}):")
            formatted.append(f"Relevance: {result['score']:.2f}")
            formatted.append(f"Content: {result['content']}")
            formatted.append("")
            
        # Add graph context
        if graph_context['relationships']:
            formatted.append("Related Entities and Relationships:")
            for rel in graph_context['relationships'][:5]:
                formatted.append(f"- {rel['source']} {rel['type']} {rel['target']}")
                
        return "\n".join(formatted)
        
    def _format_analyses(self, questions: List[str], 
                        analyses: List[Dict[str, Any]]) -> str:
        """Format sub-question analyses for synthesis"""
        formatted = []
        
        for q, a in zip(questions, analyses):
            formatted.append(f"Sub-question: {q}")
            formatted.append(f"Analysis: {a['analysis']}")
            formatted.append(f"Confidence: {a['confidence']:.2f}")
            formatted.append(f"Sources: {', '.join(a['sources'][:3])}")
            formatted.append("")
            
        return "\n".join(formatted)
        
    def _calculate_confidence(self, analyses: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score"""
        if not analyses:
            return 0.0
            
        confidences = [a['confidence'] for a in analyses]
        # Weighted average - lower confidence pulls down more
        return np.average(confidences, weights=[c**2 for c in confidences])
        
    def _score_analysis(self, analysis: str, results: List[Dict]) -> float:
        """Score the quality of an analysis"""
        # Factors: retrieval scores, analysis length, citation presence
        base_score = np.mean([r['score'] for r in results]) if results else 0.5
        
        # Boost for detailed analysis
        length_factor = min(len(analysis) / 500, 1.0)
        
        # Check for citations/references
        citation_factor = 1.0 if any(r['metadata']['title'] in analysis for r in results) else 0.8
        
        return base_score * length_factor * citation_factor


class IntelligentAutoComplete:
    """Context-aware auto-complete for research queries"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.query_patterns = defaultdict(int)
        self.entity_trie = {}
        self.common_prefixes = self._load_common_prefixes()
        
    def _load_common_prefixes(self) -> List[str]:
        """Load common query prefixes for RNA research"""
        return [
            "How do I",
            "What is the protocol for",
            "Where can I find",
            "What are the steps for",
            "How to troubleshoot",
            "What is the difference between",
            "When should I use",
            "What concentration of",
            "How long does",
            "What temperature for",
            "Can I use",
            "Is it normal that",
            "Why does my",
            "What causes",
            "How to optimize"
        ]
        
    def add_query(self, query: str, entities: List[str]):
        """Add a query to learn patterns"""
        # Update query patterns
        words = query.lower().split()
        for i in range(len(words) - 1):
            prefix = " ".join(words[:i+1])
            continuation = " ".join(words[i+1:i+3])
            self.query_patterns[f"{prefix}|{continuation}"] += 1
            
        # Update entity trie
        for entity in entities:
            self._add_to_trie(entity.lower())
            
        # Store in Redis for persistence
        self.redis.hincrby('query_patterns', query.lower(), 1)
        
    def _add_to_trie(self, word: str):
        """Add word to trie structure"""
        node = self.entity_trie
        for char in word:
            if char not in node:
                node[char] = {}
            node = node[char]
        node['$'] = True  # End marker
        
    def get_suggestions(self, partial_query: str, 
                       context: ConversationMemory,
                       n_suggestions: int = 5) -> List[Dict[str, Any]]:
        """Get intelligent suggestions based on partial query and context"""
        
        suggestions = []
        partial_lower = partial_query.lower()
        
        # 1. Context-aware completions from conversation
        if context.turns:
            recent_entities = list(context.active_entities)
            for entity in recent_entities:
                if entity.lower().startswith(partial_lower):
                    suggestions.append({
                        'text': f"{partial_query}{entity[len(partial_lower):]}",
                        'type': 'entity',
                        'confidence': 0.9
                    })
                    
        # 2. Pattern-based completions
        pattern_suggestions = self._get_pattern_suggestions(partial_lower)
        suggestions.extend(pattern_suggestions)
        
        # 3. Common prefix completions
        for prefix in self.common_prefixes:
            if prefix.lower().startswith(partial_lower):
                suggestions.append({
                    'text': prefix,
                    'type': 'common',
                    'confidence': 0.7
                })
                
        # 4. Entity completions from trie
        entity_completions = self._get_trie_completions(partial_lower)
        suggestions.extend([{
            'text': comp,
            'type': 'entity',
            'confidence': 0.8
        } for comp in entity_completions])
        
        # Deduplicate and sort by confidence
        seen = set()
        unique_suggestions = []
        for sug in suggestions:
            if sug['text'] not in seen:
                seen.add(sug['text'])
                unique_suggestions.append(sug)
                
        unique_suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        return unique_suggestions[:n_suggestions]
        
    def _get_pattern_suggestions(self, partial: str) -> List[Dict[str, Any]]:
        """Get suggestions based on learned patterns"""
        suggestions = []
        
        for pattern, count in self.query_patterns.items():
            prefix, continuation = pattern.split('|')
            if prefix == partial:
                suggestions.append({
                    'text': f"{partial} {continuation}",
                    'type': 'pattern',
                    'confidence': min(count / 10, 0.95)
                })
                
        return sorted(suggestions, key=lambda x: x['confidence'], reverse=True)[:3]
        
    def _get_trie_completions(self, prefix: str) -> List[str]:
        """Get word completions from trie"""
        node = self.entity_trie
        
        # Navigate to prefix
        for char in prefix:
            if char not in node:
                return []
            node = node[char]
            
        # Collect all completions
        completions = []
        self._collect_completions(node, prefix, completions)
        return completions[:5]
        
    def _collect_completions(self, node: Dict, prefix: str, completions: List[str]):
        """Recursively collect completions from trie"""
        if '$' in node:
            completions.append(prefix)
            
        for char, child_node in node.items():
            if char != '$':
                self._collect_completions(child_node, prefix + char, completions)


class FeedbackLearner:
    """Learn from user feedback to improve responses"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.feedback_cache = defaultdict(list)
        self.response_patterns = {}
        
    def record_feedback(self, query: str, response: str, 
                       feedback: Dict[str, Any], metadata: Dict[str, Any]):
        """Record user feedback for learning"""
        
        feedback_record = {
            'query': query,
            'response': response,
            'feedback': feedback,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in Redis
        feedback_key = f"feedback:{datetime.now().strftime('%Y%m%d')}:{query[:50]}"
        self.redis.hset(feedback_key, mapping={
            'data': json.dumps(feedback_record),
            'score': feedback.get('rating', 0)
        })
        
        # Update patterns
        if feedback.get('rating', 0) >= 4:
            self._learn_positive_pattern(query, response, metadata)
        elif feedback.get('rating', 0) <= 2:
            self._learn_negative_pattern(query, response, feedback)
            
    def _learn_positive_pattern(self, query: str, response: str, 
                               metadata: Dict[str, Any]):
        """Learn from positive feedback"""
        # Extract successful patterns
        query_type = self._classify_query(query)
        
        pattern = {
            'query_type': query_type,
            'sources_used': metadata.get('sources', []),
            'reasoning_steps': metadata.get('reasoning_steps', []),
            'response_structure': self._analyze_response_structure(response)
        }
        
        pattern_key = f"positive_pattern:{query_type}"
        self.redis.lpush(pattern_key, json.dumps(pattern))
        
    def _learn_negative_pattern(self, query: str, response: str, 
                               feedback: Dict[str, Any]):
        """Learn from negative feedback"""
        issues = feedback.get('issues', [])
        
        for issue in issues:
            issue_key = f"negative_pattern:{issue}"
            pattern = {
                'query': query,
                'response_snippet': response[:200],
                'issue': issue,
                'timestamp': datetime.now().isoformat()
            }
            self.redis.lpush(issue_key, json.dumps(pattern))
            
    def get_improvement_suggestions(self, query: str, 
                                   draft_response: str) -> List[Dict[str, Any]]:
        """Get suggestions to improve response based on past feedback"""
        
        suggestions = []
        query_type = self._classify_query(query)
        
        # Check positive patterns
        positive_patterns = self._get_patterns(f"positive_pattern:{query_type}", 10)
        if positive_patterns:
            common_elements = self._extract_common_elements(positive_patterns)
            
            if not all(elem in draft_response for elem in common_elements):
                suggestions.append({
                    'type': 'missing_elements',
                    'suggestion': f"Consider including: {', '.join(common_elements)}",
                    'confidence': 0.8
                })
                
        # Check negative patterns
        negative_patterns = self._get_patterns("negative_pattern:*", 20)
        for pattern in negative_patterns:
            if self._matches_negative_pattern(draft_response, pattern):
                suggestions.append({
                    'type': 'avoid_pattern',
                    'suggestion': f"Avoid: {pattern['issue']}",
                    'confidence': 0.9
                })
                
        return suggestions
        
    def _classify_query(self, query: str) -> str:
        """Classify query type"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['protocol', 'procedure', 'steps']):
            return 'protocol'
        elif any(word in query_lower for word in ['troubleshoot', 'problem', 'issue']):
            return 'troubleshooting'
        elif any(word in query_lower for word in ['compare', 'difference', 'versus']):
            return 'comparison'
        elif any(word in query_lower for word in ['explain', 'what is', 'define']):
            return 'explanation'
        else:
            return 'general'
            
    def _analyze_response_structure(self, response: str) -> Dict[str, bool]:
        """Analyze structure of successful responses"""
        return {
            'has_citations': '[' in response and ']' in response,
            'has_steps': any(f"{i}." in response for i in range(1, 10)),
            'has_warnings': any(word in response.lower() for word in ['caution', 'note', 'important']),
            'has_tips': any(word in response.lower() for word in ['tip', 'recommend', 'suggest']),
            'length_category': 'short' if len(response) < 500 else 'medium' if len(response) < 1500 else 'long'
        }
        
    def _get_patterns(self, pattern_key: str, limit: int) -> List[Dict]:
        """Retrieve patterns from Redis"""
        if '*' in pattern_key:
            # Get all keys matching pattern
            keys = self.redis.keys(pattern_key)
            patterns = []
            for key in keys[:limit]:
                items = self.redis.lrange(key, 0, limit)
                patterns.extend([json.loads(item) for item in items])
            return patterns
        else:
            items = self.redis.lrange(pattern_key, 0, limit)
            return [json.loads(item) for item in items]
            
    def _extract_common_elements(self, patterns: List[Dict]) -> List[str]:
        """Extract common elements from successful patterns"""
        common = []
        
        # Check response structures
        structure_counts = defaultdict(int)
        for pattern in patterns:
            for key, value in pattern.get('response_structure', {}).items():
                if value:
                    structure_counts[key] += 1
                    
        # Elements present in >70% of successful responses
        threshold = len(patterns) * 0.7
        for element, count in structure_counts.items():
            if count >= threshold:
                common.append(element)
                
        return common
        
    def _matches_negative_pattern(self, response: str, pattern: Dict) -> bool:
        """Check if response matches a negative pattern"""
        issue = pattern.get('issue', '')
        
        if issue == 'too_vague':
            return len(response) < 200 and response.count('.') < 3
        elif issue == 'no_citations':
            return '[' not in response
        elif issue == 'too_technical':
            technical_terms = ['phosphorylation', 'transfection', 'oligonucleotide']
            term_count = sum(1 for term in technical_terms if term in response.lower())
            return term_count > 5 and 'simply put' not in response.lower()
        
        return False


class EnhancedRAGOrchestrator:
    """Main orchestrator that combines all enhanced components"""
    
    def __init__(self, weaviate_client, openai_client, redis_client):
        self.weaviate = weaviate_client
        self.openai = openai_client
        self.redis = redis_client
        
        # Initialize components
        self.memory_manager = {}  # session_id -> ConversationMemory
        self.knowledge_graph = KnowledgeGraphManager()
        self.reasoning_pipeline = ReasoningPipeline(openai_client)
        self.auto_complete = IntelligentAutoComplete(redis_client)
        self.feedback_learner = FeedbackLearner(redis_client)
        
        # Load knowledge graph from existing data
        self._initialize_knowledge_graph()
        
    async def process_query(self, query: str, session_id: str, 
                           user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process a query with full enhanced pipeline"""
        
        # Get or create conversation memory
        if session_id not in self.memory_manager:
            self.memory_manager[session_id] = ConversationMemory(
                session_id=session_id,
                user_profile=user_context or {}
            )
        
        memory = self.memory_manager[session_id]
        
        # Extract conversation context
        conversation_context = memory.get_relevant_context(query, self.embedder)
        
        # Build context for reasoning
        context = {
            'conversation_context': conversation_context,
            'user_profile': memory.user_profile,
            'research_context': memory.research_context,
            'active_entities': list(memory.active_entities),
            'lab_context': self._get_lab_context()
        }
        
        # Execute reasoning pipeline
        reasoning_result = await self.reasoning_pipeline.reason(
            query, context, self, self.knowledge_graph
        )
        
        # Get improvement suggestions from feedback learner
        improvements = self.feedback_learner.get_improvement_suggestions(
            query, reasoning_result['answer']
        )
        
        # Apply improvements if high confidence
        final_answer = self._apply_improvements(
            reasoning_result['answer'], improvements
        )
        
        # Extract entities for knowledge graph
        entities = self._extract_comprehensive_entities(query, final_answer)
        
        # Create conversation turn
        turn = ConversationTurn(
            query=query,
            response=final_answer,
            documents_used=self._extract_document_ids(reasoning_result),
            confidence_score=reasoning_result['confidence'],
            reasoning_steps=reasoning_result['reasoning_trace'],
            timestamp=datetime.now(),
            entities_mentioned=entities
        )
        
        # Update memory
        memory.add_turn(turn)
        
        # Update auto-complete
        self.auto_complete.add_query(query, entities)
        
        return {
            'answer': final_answer,
            'confidence': reasoning_result['confidence'],
            'reasoning_trace': reasoning_result['reasoning_trace'],
            'sub_questions': reasoning_result['sub_questions'],
            'sources': turn.documents_used,
            'entities': entities,
            'suggestions': self.auto_complete.get_suggestions(query[:20], memory),
            'session_id': session_id
        }
        
    async def search(self, query: str, top_k: int = 5, 
                    filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Enhanced search with knowledge graph boosting"""
        
        # Extract entities from query
        query_entities = self._extract_entities(query)
        
        # Get related entities from knowledge graph
        all_related = []
        for entity in query_entities:
            related = self.knowledge_graph.find_related_entities(entity)
            all_related.extend(related)
            
        # Build enhanced query
        enhanced_query = self._build_enhanced_query(query, all_related)
        
        # Perform hybrid search
        results = self.weaviate.query.get(
            "Document",
            ["content", "title", "authors", "doc_type", "year", "file_path"]
        ).with_hybrid(
            query=enhanced_query,
            alpha=0.7  # Balance between vector and keyword search
        ).with_limit(top_k * 2)  # Get more for re-ranking
        
        # Apply filters if provided
        if filters:
            results = results.with_where(filters)
            
        results = results.do()
        
        # Re-rank based on entity relevance
        ranked_results = self._rerank_by_entities(
            results.get('data', {}).get('Get', {}).get('Document', []),
            query_entities,
            all_related
        )
        
        return ranked_results[:top_k]
        
    def record_feedback(self, session_id: str, turn_index: int, 
                       feedback: Dict[str, Any]):
        """Record feedback for a specific turn"""
        
        if session_id not in self.memory_manager:
            logger.warning(f"Session {session_id} not found")
            return
            
        memory = self.memory_manager[session_id]
        if turn_index >= len(memory.turns):
            logger.warning(f"Turn {turn_index} not found in session {session_id}")
            return
            
        turn = memory.turns[turn_index]
        turn.feedback = feedback
        
        # Learn from feedback
        self.feedback_learner.record_feedback(
            turn.query,
            turn.response,
            feedback,
            {
                'sources': turn.documents_used,
                'reasoning_steps': turn.reasoning_steps,
                'confidence': turn.confidence_score
            }
        )
        
    def get_auto_complete_suggestions(self, partial_query: str, 
                                     session_id: str) -> List[Dict[str, Any]]:
        """Get auto-complete suggestions"""
        
        memory = self.memory_manager.get(session_id, ConversationMemory(session_id))
        return self.auto_complete.get_suggestions(partial_query, memory)
        
    def _initialize_knowledge_graph(self):
        """Initialize knowledge graph from existing documents"""
        # This would load from your document store
        # For now, we'll add some example entities
        
        example_entities = [
            {
                'name': 'CRISPR',
                'type': 'technique',
                'relations': [
                    {'target': 'Cas9', 'type': 'uses', 'strength': 0.9},
                    {'target': 'gRNA', 'type': 'requires', 'strength': 0.95}
                ]
            },
            {
                'name': 'RNA extraction',
                'type': 'protocol',
                'relations': [
                    {'target': 'TRIzol', 'type': 'uses_reagent', 'strength': 0.8},
                    {'target': 'RNase-free water', 'type': 'requires', 'strength': 0.9}
                ]
            }
        ]
        
        for entity in example_entities:
            self.knowledge_graph.add_entities_from_document('init', [entity])
            
    def _get_lab_context(self) -> Dict[str, Any]:
        """Get current lab context"""
        return {
            'lab_name': 'RNA Biology Lab - Dr. Debojyoti Chakraborty',
            'institution': 'CSIR-IGIB',
            'focus_areas': ['RNA biology', 'CRISPR', 'Gene regulation'],
            'common_techniques': ['RNA-seq', 'CRISPR screening', 'Western blot'],
            'recent_projects': []  # Would be populated from database
        }
        
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities using NER (simplified version)"""
        # In production, use a proper NER model
        import re
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Add known technical terms
        technical_terms = ['CRISPR', 'RNA', 'DNA', 'PCR', 'qPCR']
        for term in technical_terms:
            if term.lower() in text.lower():
                entities.append(term)
                
        return list(set(entities))
        
    def _extract_comprehensive_entities(self, query: str, response: str) -> List[str]:
        """Extract entities from both query and response"""
        all_entities = self._extract_entities(query)
        all_entities.extend(self._extract_entities(response))
        return list(set(all_entities))
        
    def _build_enhanced_query(self, query: str, 
                             related_entities: List[Tuple[str, str, float]]) -> str:
        """Build enhanced query with related entities"""
        
        # Add high-confidence related entities
        enhancements = []
        for entity, relation, strength in related_entities:
            if strength > 0.7:
                enhancements.append(entity)
                
        if enhancements:
            enhanced = f"{query} {' '.join(enhancements[:3])}"
            return enhanced
        return query
        
    def _rerank_by_entities(self, results: List[Dict], 
                           query_entities: List[str],
                           related_entities: List[Tuple]) -> List[Dict[str, Any]]:
        """Re-rank results based on entity relevance"""
        
        scored_results = []
        
        for result in results:
            content = result.get('content', '')
            title = result.get('title', '')
            
            # Base score from search
            score = result.get('_additional', {}).get('score', 0.5)
            
            # Boost for query entities
            for entity in query_entities:
                if entity.lower() in content.lower():
                    score += 0.1
                if entity.lower() in title.lower():
                    score += 0.15
                    
            # Boost for related entities
            for entity, _, strength in related_entities:
                if entity.lower() in content.lower():
                    score += 0.05 * strength
                    
            scored_results.append({
                **result,
                'score': min(score, 1.0)
            })
            
        # Sort by score
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        return scored_results
        
    def _extract_document_ids(self, reasoning_result: Dict) -> List[str]:
        """Extract document IDs from reasoning result"""
        doc_ids = []
        
        for analysis in reasoning_result.get('analyses', []):
            doc_ids.extend(analysis.get('sources', []))
            
        return list(set(doc_ids))
        
    def _apply_improvements(self, answer: str, 
                           improvements: List[Dict[str, Any]]) -> str:
        """Apply high-confidence improvements to answer"""
        
        improved_answer = answer
        
        for improvement in improvements:
            if improvement['confidence'] > 0.85:
                if improvement['type'] == 'missing_elements':
                    # Add missing elements
                    if 'citations' in improvement['suggestion'] and '[' not in improved_answer:
                        improved_answer += "\n\n[Note: Specific citations from lab documents would be added here]"
                    
                    if 'steps' in improvement['suggestion'] and not any(f"{i}." in improved_answer for i in range(1, 10)):
                        # Reformat as steps if applicable
                        sentences = improved_answer.split('. ')
                        if len(sentences) > 2:
                            step_format = []
                            for i, sent in enumerate(sentences, 1):
                                if sent.strip():
                                    step_format.append(f"{i}. {sent.strip()}.")
                            improved_answer = '\n'.join(step_format)
                            
        return improved_answer


# Usage Example
async def main():
    """Example usage of the enhanced RAG system"""
    
    # Initialize clients
    weaviate_client = weaviate.Client("http://localhost:8080")
    openai_client = OpenAI(api_key="your-key")
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    # Create orchestrator
    rag = EnhancedRAGOrchestrator(weaviate_client, openai_client, redis_client)
    
    # Example conversation
    session_id = "user123_session456"
    
    # First query
    result1 = await rag.process_query(
        "What's the best protocol for RNA extraction from mouse brain tissue?",
        session_id,
        user_context={'role': 'PhD student', 'experience': 'intermediate'}
    )
    
    print(f"Answer: {result1['answer']}")
    print(f"Confidence: {result1['confidence']}")
    print(f"Sub-questions explored: {result1['sub_questions']}")
    
    # Follow-up query (uses conversation context)
    result2 = await rag.process_query(
        "What about troubleshooting low yield issues?",
        session_id
    )
    
    print(f"\nFollow-up Answer: {result2['answer']}")
    
    # Get auto-complete suggestions
    suggestions = rag.get_auto_complete_suggestions("How to optimize", session_id)
    print(f"\nAuto-complete suggestions: {suggestions}")
    
    # Record feedback
    rag.record_feedback(session_id, 0, {
        'rating': 5,
        'helpful': True,
        'issues': []
    })
    

if __name__ == "__main__":
    asyncio.run(main())