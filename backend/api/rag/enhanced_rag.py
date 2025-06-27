"""
Enhanced RAG Implementation for RNA Lab Navigator
================================================

This module implements the production-ready enhanced RAG system with:
- Conversation memory and context management
- Multi-stage reasoning with chain-of-thought
- Knowledge graph for entity relationships
- Intelligent auto-complete
- Continuous learning from feedback

Optimized for the RNA Biology Lab's specific needs.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import hashlib

import redis
import weaviate
from django.conf import settings
from django.core.cache import cache
from celery import shared_task
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from api.models import Document, QueryHistory
from api.llm.openai_embeddings import get_embeddings
import openai  # For direct OpenAI calls

logger = logging.getLogger(__name__)


class RAGAdapter:
    """Adapter to avoid circular imports with real_rag.py"""
    
    def process_query(self, query):
        """Process query using perform_rag_query"""
        from api.search.real_rag import perform_rag_query
        print(f"\n[RAG ADAPTER DEBUG] Processing query: {query}")
        result = perform_rag_query(query)
        print(f"[RAG ADAPTER DEBUG] Got {len(result.get('search_results', []))} search results")
        return result
    
    def _query_llm(self, prompt, context="", temperature=0.7):
        """Direct OpenAI query"""
        try:
            openai.api_key = settings.OPENAI_API_KEY
            response = openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": f"{context}\n\n{prompt}" if context else prompt}
                ],
                temperature=temperature,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM query error: {e}")
            return f"Error: {str(e)}"


# Configuration
CONVERSATION_CONTEXT_WINDOW = 5
MAX_CONVERSATION_HISTORY = 50
ENTITY_CACHE_TTL = 3600  # 1 hour
REASONING_CACHE_TTL = 300  # 5 minutes
MIN_CONFIDENCE_THRESHOLD = 0.45


@dataclass
class ConversationTurn:
    """Single conversation turn with metadata"""
    query: str
    response: str
    documents_used: List[str]
    confidence_score: float
    reasoning_steps: List[Dict[str, Any]]
    timestamp: datetime
    entities_mentioned: List[str] = field(default_factory=list)
    feedback: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query': self.query,
            'response': self.response,
            'documents_used': self.documents_used,
            'confidence_score': self.confidence_score,
            'reasoning_steps': self.reasoning_steps,
            'timestamp': self.timestamp.isoformat(),
            'entities_mentioned': self.entities_mentioned,
            'feedback': self.feedback
        }


class ConversationMemoryManager:
    """Manages conversation memory with Redis backend"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.embeddings_cache = {}
        
    def get_or_create_session(self, session_id: str, user_context: Dict = None) -> Dict[str, Any]:
        """Get or create a conversation session"""
        session_key = f"conversation:{session_id}"
        session_data = self.redis.get(session_key)
        
        if session_data:
            return json.loads(session_data)
        
        # Create new session
        new_session = {
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'user_context': user_context or {},
            'turns': [],
            'active_entities': []
        }
        
        self.redis.setex(
            session_key,
            timedelta(days=7),  # 7 day expiry
            json.dumps(new_session)
        )
        
        return new_session
        
    def add_turn(self, session_id: str, turn: ConversationTurn):
        """Add a turn to the conversation"""
        session_key = f"conversation:{session_id}"
        session_data = self.get_or_create_session(session_id)
        
        # Add turn
        session_data['turns'].append(turn.to_dict())
        
        # Update active entities
        session_data['active_entities'] = list(set(
            session_data['active_entities'] + turn.entities_mentioned
        ))[-20:]  # Keep last 20 entities
        
        # Trim old turns if needed
        if len(session_data['turns']) > MAX_CONVERSATION_HISTORY:
            session_data['turns'] = session_data['turns'][-MAX_CONVERSATION_HISTORY:]
        
        self.redis.setex(
            session_key,
            timedelta(days=7),
            json.dumps(session_data)
        )
        
    def get_relevant_context(self, session_id: str, current_query: str) -> str:
        """Extract relevant context from conversation history"""
        session_data = self.get_or_create_session(session_id)
        turns = session_data.get('turns', [])
        
        if not turns:
            return ""
        
        # Get embeddings for current query
        query_embedding = get_embeddings([current_query])[0]
        
        # Score recent turns by relevance
        context_parts = []
        recent_turns = turns[-10:]  # Last 10 turns
        
        for turn in recent_turns:
            turn_text = f"{turn['query']} {turn['response'][:200]}"
            turn_embedding = get_embeddings([turn_text])[0]
            
            similarity = cosine_similarity([query_embedding], [turn_embedding])[0][0]
            
            if similarity > 0.7:  # High relevance threshold
                context_parts.append({
                    'query': turn['query'],
                    'response_snippet': turn['response'][:200] + '...',
                    'similarity': similarity
                })
        
        # Sort by similarity and take top 3
        context_parts.sort(key=lambda x: x['similarity'], reverse=True)
        context_parts = context_parts[:3]
        
        # Format context
        if context_parts:
            formatted_context = "Previous relevant discussion:\n"
            for part in context_parts:
                formatted_context += f"Q: {part['query']}\nA: {part['response_snippet']}\n\n"
            return formatted_context
        
        return ""


class SimpleKnowledgeGraph:
    """Simplified knowledge graph using Redis"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.entity_prefix = "kg:entity:"
        self.relation_prefix = "kg:relation:"
        
    def add_entity(self, entity: str, entity_type: str, document_id: str):
        """Add an entity to the knowledge graph"""
        entity_key = f"{self.entity_prefix}{entity.lower()}"
        
        entity_data = {
            'name': entity,
            'type': entity_type,
            'documents': [document_id],
            'created_at': datetime.now().isoformat()
        }
        
        # Check if exists
        existing = self.redis.get(entity_key)
        if existing:
            data = json.loads(existing)
            if document_id not in data['documents']:
                data['documents'].append(document_id)
            entity_data = data
        
        self.redis.setex(
            entity_key,
            timedelta(days=30),
            json.dumps(entity_data)
        )
        
    def add_relation(self, source: str, target: str, relation_type: str, strength: float = 1.0):
        """Add a relation between entities"""
        relation_key = f"{self.relation_prefix}{source.lower()}:{target.lower()}"
        
        relation_data = {
            'source': source,
            'target': target,
            'type': relation_type,
            'strength': strength,
            'created_at': datetime.now().isoformat()
        }
        
        self.redis.setex(
            relation_key,
            timedelta(days=30),
            json.dumps(relation_data)
        )
        
    def find_related_entities(self, entity: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Find entities related to the given entity"""
        related = []
        
        # Search for relations where entity is source or target
        pattern1 = f"{self.relation_prefix}{entity.lower()}:*"
        pattern2 = f"{self.relation_prefix}*:{entity.lower()}"
        
        for pattern in [pattern1, pattern2]:
            for key in self.redis.scan_iter(match=pattern, count=100):
                relation_data = json.loads(self.redis.get(key))
                
                # Get the other entity
                other_entity = relation_data['target'] if relation_data['source'].lower() == entity.lower() else relation_data['source']
                
                related.append({
                    'entity': other_entity,
                    'relation': relation_data['type'],
                    'strength': relation_data['strength']
                })
        
        # Sort by strength and return top results
        related.sort(key=lambda x: x['strength'], reverse=True)
        return related[:max_results]


class ChainOfThoughtReasoner:
    """Implements chain-of-thought reasoning for complex queries"""
    
    def __init__(self, rag_pipeline):
        self.rag = rag_pipeline
        self.decomposition_prompt = """You are a research assistant helping to answer complex questions about RNA biology.

Given this question: {query}

Previous context: {context}

Break this down into 2-4 specific sub-questions that would help provide a comprehensive answer. Focus on:
1. Core concepts that need explanation
2. Specific techniques or protocols mentioned
3. Potential troubleshooting or optimization aspects
4. Connections to other lab work

Format:
1. [First sub-question]
2. [Second sub-question]
...

Sub-questions:"""

        self.synthesis_prompt = """You are a senior RNA biology researcher providing a comprehensive answer.

Original question: {query}

Sub-questions and findings:
{findings}

Lab context: This is for researchers in Dr. Chakraborty's RNA biology lab at CSIR-IGIB.

Synthesize a complete answer that:
1. Directly addresses the original question
2. Incorporates all relevant findings
3. Provides specific protocols/techniques when applicable
4. Mentions relevant lab resources or previous work
5. Includes appropriate citations [Author, Year]

Answer:"""

    async def reason(self, query: str, context: str = "") -> Dict[str, Any]:
        """Execute chain-of-thought reasoning"""
        reasoning_trace = []
        
        # Check cache first
        cache_key = f"reasoning:{hashlib.md5(f'{query}{context}'.encode()).hexdigest()}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Step 1: Decompose query
            decomposition = self._decompose_query(query, context)
            sub_questions = self._parse_sub_questions(decomposition)
            reasoning_trace.append({
                'step': 'decomposition',
                'output': sub_questions
            })
            
            # Step 2: Answer each sub-question
            sub_answers = []
            for sq in sub_questions:
                result = self.rag.process_query(sq)
                sub_answers.append({
                    'question': sq,
                    'answer': result.get('answer', ''),
                    'sources': result.get('sources', []),
                    'confidence': result.get('confidence_score', 0.5)
                })
                
            reasoning_trace.append({
                'step': 'sub_answers',
                'output': sub_answers
            })
            
            # Step 3: Synthesize final answer
            final_answer = self._synthesize_answer(query, sub_answers)
            reasoning_trace.append({
                'step': 'synthesis',
                'output': final_answer
            })
            
            # Calculate overall confidence
            confidence = np.mean([sa['confidence'] for sa in sub_answers])
            
            result = {
                'answer': final_answer,
                'reasoning_trace': reasoning_trace,
                'sub_questions': sub_questions,
                'confidence': confidence,
                'sources': self._collect_sources(sub_answers)
            }
            
            # Cache result
            cache.set(cache_key, result, REASONING_CACHE_TTL)
            
            return result
            
        except Exception as e:
            logger.error(f"Reasoning error: {e}")
            # Fallback to simple RAG
            return self.rag.process_query(query)
    
    def _decompose_query(self, query: str, context: str) -> str:
        """Decompose query into sub-questions"""
        prompt = self.decomposition_prompt.format(query=query, context=context)
        
        # Use the RAG pipeline's LLM
        response = self.rag._query_llm(prompt, "", temperature=0.1)
        return response
    
    def _parse_sub_questions(self, decomposition: str) -> List[str]:
        """Parse sub-questions from decomposition"""
        lines = decomposition.strip().split('\n')
        questions = []
        
        for line in lines:
            line = line.strip()
            if line and line[0].isdigit() and '.' in line:
                question = line.split('.', 1)[1].strip()
                if len(question) > 10:  # Filter out very short lines
                    questions.append(question)
        
        return questions[:4]  # Max 4 sub-questions
    
    def _synthesize_answer(self, query: str, sub_answers: List[Dict]) -> str:
        """Synthesize final answer from sub-answers"""
        # Format findings
        findings = []
        for sa in sub_answers:
            findings.append(f"Q: {sa['question']}")
            findings.append(f"Finding: {sa['answer'][:300]}...")
            findings.append(f"Confidence: {sa['confidence']:.2f}")
            findings.append("")
        
        prompt = self.synthesis_prompt.format(
            query=query,
            findings='\n'.join(findings)
        )
        
        # Use the RAG pipeline's LLM
        response = self.rag._query_llm(prompt, "", temperature=0.1)
        return response
    
    def _collect_sources(self, sub_answers: List[Dict]) -> List[str]:
        """Collect unique sources from all sub-answers"""
        all_sources = []
        for sa in sub_answers:
            all_sources.extend(sa.get('sources', []))
        
        # Deduplicate while preserving order
        seen = set()
        unique_sources = []
        for source in all_sources:
            if source not in seen:
                seen.add(source)
                unique_sources.append(source)
        
        return unique_sources


class SmartAutoComplete:
    """Intelligent auto-complete for research queries"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix_key = "autocomplete:prefixes"
        self.pattern_key = "autocomplete:patterns"
        
        # Common research query starters
        self.common_starters = [
            "How do I",
            "What is the protocol for",
            "What's the best way to",
            "How to troubleshoot",
            "What concentration should I use for",
            "How long should I",
            "What temperature for",
            "Can I use",
            "What's the difference between",
            "Why is my",
            "How to optimize"
        ]
        
    def add_query(self, query: str, entities: List[str]):
        """Learn from a new query"""
        # Add to query history
        self.redis.lpush("query_history", query)
        self.redis.ltrim("query_history", 0, 999)  # Keep last 1000
        
        # Extract and store patterns
        words = query.lower().split()
        for i in range(len(words) - 1):
            prefix = ' '.join(words[:i+1])
            continuation = ' '.join(words[i+1:i+3])
            
            if len(prefix) > 3 and len(continuation) > 0:
                pattern_key = f"{self.pattern_key}:{prefix}"
                self.redis.hincrby(pattern_key, continuation, 1)
                self.redis.expire(pattern_key, timedelta(days=30))
        
        # Store entity associations
        for entity in entities:
            entity_key = f"autocomplete:entity:{entity.lower()}"
            self.redis.sadd(entity_key, query)
            self.redis.expire(entity_key, timedelta(days=30))
            
    def get_suggestions(self, partial: str, session_context: Dict = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Get auto-complete suggestions"""
        suggestions = []
        partial_lower = partial.lower()
        
        # 1. Common starter completions
        for starter in self.common_starters:
            if starter.lower().startswith(partial_lower) and len(partial) < len(starter):
                suggestions.append({
                    'text': starter,
                    'type': 'common',
                    'confidence': 0.9
                })
        
        # 2. Pattern-based completions
        pattern_key = f"{self.pattern_key}:{partial_lower}"
        patterns = self.redis.hgetall(pattern_key)
        
        for continuation, count in patterns.items():
            count = int(count)
            suggestions.append({
                'text': f"{partial} {continuation.decode() if isinstance(continuation, bytes) else continuation}",
                'type': 'pattern',
                'confidence': min(count / 10, 0.95)
            })
        
        # 3. Recent query completions
        recent_queries = self.redis.lrange("query_history", 0, 100)
        for query in recent_queries:
            query_str = query.decode() if isinstance(query, bytes) else query
            if query_str.lower().startswith(partial_lower) and len(query_str) > len(partial):
                suggestions.append({
                    'text': query_str,
                    'type': 'history',
                    'confidence': 0.8
                })
        
        # 4. Entity-based completions from session
        if session_context and 'active_entities' in session_context:
            for entity in session_context['active_entities']:
                if partial_lower in entity.lower():
                    # Find queries containing this entity
                    entity_key = f"autocomplete:entity:{entity.lower()}"
                    entity_queries = self.redis.smembers(entity_key)
                    
                    for eq in entity_queries[:3]:
                        eq_str = eq.decode() if isinstance(eq, bytes) else eq
                        if eq_str.lower().startswith(partial_lower):
                            suggestions.append({
                                'text': eq_str,
                                'type': 'entity',
                                'confidence': 0.85
                            })
        
        # Deduplicate and sort
        seen = set()
        unique_suggestions = []
        for sug in suggestions:
            if sug['text'] not in seen:
                seen.add(sug['text'])
                unique_suggestions.append(sug)
        
        unique_suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        return unique_suggestions[:limit]


class FeedbackLearningSystem:
    """Learn from user feedback to improve responses"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
    def record_feedback(self, session_id: str, turn_index: int, feedback: Dict[str, Any]):
        """Record feedback for a conversation turn"""
        feedback_key = f"feedback:{session_id}:{turn_index}"
        
        feedback_data = {
            'session_id': session_id,
            'turn_index': turn_index,
            'rating': feedback.get('rating', 0),
            'helpful': feedback.get('helpful', False),
            'issues': feedback.get('issues', []),
            'timestamp': datetime.now().isoformat()
        }
        
        self.redis.setex(
            feedback_key,
            timedelta(days=90),  # Keep for 90 days
            json.dumps(feedback_data)
        )
        
        # Update aggregated metrics
        if feedback_data['rating'] >= 4:
            self.redis.hincrby("feedback:metrics", "positive", 1)
        elif feedback_data['rating'] <= 2:
            self.redis.hincrby("feedback:metrics", "negative", 1)
            
            # Store negative patterns for analysis
            for issue in feedback_data['issues']:
                self.redis.hincrby("feedback:issues", issue, 1)
                
    def get_feedback_insights(self) -> Dict[str, Any]:
        """Get insights from feedback data"""
        metrics = self.redis.hgetall("feedback:metrics")
        issues = self.redis.hgetall("feedback:issues")
        
        # Calculate satisfaction rate
        positive = int(metrics.get(b'positive', 0))
        negative = int(metrics.get(b'negative', 0))
        total = positive + negative
        
        satisfaction_rate = (positive / total * 100) if total > 0 else 0
        
        # Get top issues
        issue_counts = []
        for issue, count in issues.items():
            issue_str = issue.decode() if isinstance(issue, bytes) else issue
            issue_counts.append((issue_str, int(count)))
        
        issue_counts.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'satisfaction_rate': satisfaction_rate,
            'total_feedback': total,
            'positive_feedback': positive,
            'negative_feedback': negative,
            'top_issues': issue_counts[:5]
        }


class EnhancedRAGPipeline:
    """Main enhanced RAG pipeline orchestrator"""
    
    def __init__(self):
        # Initialize Redis
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=1,  # Use separate DB for enhanced features
            decode_responses=False
        )
        
        # Initialize components
        self.rag_adapter = RAGAdapter()
        self.memory_manager = ConversationMemoryManager(self.redis)
        self.knowledge_graph = SimpleKnowledgeGraph(self.redis)
        self.reasoner = ChainOfThoughtReasoner(self.rag_adapter)
        self.auto_complete = SmartAutoComplete(self.redis)
        self.feedback_system = FeedbackLearningSystem(self.redis)
        
    async def process_query(self, query: str, session_id: str, 
                          user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process query with enhanced pipeline"""
        
        try:
            # Get session and context
            session = self.memory_manager.get_or_create_session(session_id, user_context)
            conversation_context = self.memory_manager.get_relevant_context(session_id, query)
            
            # Determine if we need complex reasoning
            needs_reasoning = self._needs_complex_reasoning(query)
            
            if needs_reasoning:
                # Use chain-of-thought reasoning
                result = await self.reasoner.reason(query, conversation_context)
                answer = result['answer']
                confidence = result['confidence']
                sources = result['sources']
                reasoning_trace = result['reasoning_trace']
            else:
                # Use standard RAG with context
                enhanced_query = self._enhance_query_with_context(query, conversation_context)
                result = self.rag_adapter.process_query(enhanced_query)
                answer = result.get('answer', '')
                confidence = result.get('confidence_score', 0.5)
                sources = result.get('sources', [])
                reasoning_trace = []
            
            # Extract entities
            entities = self._extract_entities(query + " " + answer)
            
            # Update knowledge graph
            for entity in entities:
                self.knowledge_graph.add_entity(entity, 'extracted', session_id)
            
            # Create conversation turn
            turn = ConversationTurn(
                query=query,
                response=answer,
                documents_used=sources,
                confidence_score=confidence,
                reasoning_steps=reasoning_trace,
                timestamp=datetime.now(),
                entities_mentioned=entities
            )
            
            # Store turn
            self.memory_manager.add_turn(session_id, turn)
            
            # Update auto-complete
            self.auto_complete.add_query(query, entities)
            
            # Get suggestions for next query
            suggestions = self.auto_complete.get_suggestions("", session)
            
            return {
                'answer': answer,
                'confidence': confidence,
                'sources': sources,
                'reasoning_trace': reasoning_trace,
                'entities': entities,
                'suggestions': suggestions,
                'session_id': session_id
            }
            
        except Exception as e:
            logger.error(f"Enhanced RAG error: {e}")
            # Fallback to basic RAG
            return self.rag_adapter.process_query(query)
    
    def get_autocomplete_suggestions(self, partial_query: str, session_id: str) -> List[Dict[str, Any]]:
        """Get auto-complete suggestions"""
        session = self.memory_manager.get_or_create_session(session_id)
        return self.auto_complete.get_suggestions(partial_query, session)
    
    def record_feedback(self, session_id: str, turn_index: int, feedback: Dict[str, Any]):
        """Record user feedback"""
        self.feedback_system.record_feedback(session_id, turn_index, feedback)
        
        # Log to QueryHistory for analysis
        try:
            session = self.memory_manager.get_or_create_session(session_id)
            if turn_index < len(session['turns']):
                turn = session['turns'][turn_index]
                QueryHistory.objects.filter(
                    query=turn['query'],
                    timestamp__gte=turn['timestamp']
                ).update(
                    feedback_rating=feedback.get('rating'),
                    feedback_text=json.dumps(feedback)
                )
        except Exception as e:
            logger.error(f"Error updating QueryHistory: {e}")
    
    def _needs_complex_reasoning(self, query: str) -> bool:
        """Determine if query needs complex reasoning"""
        complexity_indicators = [
            'compare', 'difference between', 'pros and cons',
            'troubleshoot', 'optimize', 'best practice',
            'step by step', 'detailed', 'comprehensive',
            'why', 'how does', 'explain'
        ]
        
        query_lower = query.lower()
        
        # Check for multiple questions
        if query.count('?') > 1:
            return True
        
        # Check for complexity indicators
        for indicator in complexity_indicators:
            if indicator in query_lower:
                return True
        
        # Check query length (long queries often need decomposition)
        if len(query.split()) > 15:
            return True
        
        return False
    
    def _enhance_query_with_context(self, query: str, context: str) -> str:
        """Enhance query with conversation context"""
        if not context:
            return query
        
        enhanced = f"{context}\n\nCurrent question: {query}"
        return enhanced
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text (simplified version)"""
        import re
        
        entities = []
        
        # Common RNA biology terms
        rna_terms = [
            'RNA', 'DNA', 'CRISPR', 'Cas9', 'Cas13', 'gRNA', 'sgRNA',
            'PCR', 'qPCR', 'RT-PCR', 'Western blot', 'Northern blot',
            'transfection', 'transformation', 'lentivirus', 'plasmid',
            'TRIzol', 'RNase', 'DNase', 'reverse transcriptase'
        ]
        
        text_lower = text.lower()
        for term in rna_terms:
            if term.lower() in text_lower:
                entities.append(term)
        
        # Extract capitalized phrases (likely entities)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(capitalized)
        
        # Deduplicate
        return list(set(entities))


# Celery tasks for background processing
@shared_task
def update_knowledge_graph_from_document(document_id: int):
    """Extract entities from document and update knowledge graph"""
    try:
        doc = Document.objects.get(id=document_id)
        pipeline = EnhancedRAGPipeline()
        
        # Extract entities from document
        entities = pipeline._extract_entities(doc.content)
        
        # Add to knowledge graph
        for entity in entities:
            pipeline.knowledge_graph.add_entity(
                entity,
                'document',
                str(document_id)
            )
        
        logger.info(f"Updated knowledge graph with {len(entities)} entities from document {document_id}")
        
    except Exception as e:
        logger.error(f"Error updating knowledge graph: {e}")


@shared_task
def analyze_feedback_patterns():
    """Analyze feedback patterns for insights"""
    try:
        pipeline = EnhancedRAGPipeline()
        insights = pipeline.feedback_system.get_feedback_insights()
        
        # Log insights
        logger.info(f"Feedback insights: {json.dumps(insights, indent=2)}")
        
        # Could send alerts if satisfaction drops
        if insights['satisfaction_rate'] < 70 and insights['total_feedback'] > 50:
            logger.warning(f"Low satisfaction rate: {insights['satisfaction_rate']:.1f}%")
            
    except Exception as e:
        logger.error(f"Error analyzing feedback: {e}")


# Initialize singleton instance
_enhanced_rag_instance = None

def get_enhanced_rag_pipeline() -> EnhancedRAGPipeline:
    """Get singleton instance of enhanced RAG pipeline"""
    global _enhanced_rag_instance
    if _enhanced_rag_instance is None:
        _enhanced_rag_instance = EnhancedRAGPipeline()
    return _enhanced_rag_instance