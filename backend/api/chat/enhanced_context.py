"""
Enhanced conversation context management for better coherence.
"""
import re
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

# Check if spacy is available (optional dependency)
SPACY_AVAILABLE = False
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except:
    # Spacy is optional - we'll use simple text processing
    pass


class EnhancedContextBuilder:
    """Advanced context building with better coherence."""
    
    # Expanded reference words that indicate context dependency
    REFERENCE_WORDS = {
        'pronouns': ['it', 'this', 'that', 'those', 'these', 'they', 'them', 'its', 'their'],
        'connectors': ['also', 'more', 'additionally', 'furthermore', 'however', 'but', 
                      'besides', 'moreover', 'similarly', 'likewise'],
        'references': ['the same', 'such', 'above', 'previous', 'earlier', 'mentioned',
                      'discussed', 'related', 'similar', 'following'],
        'questions': ['what about', 'how about', 'and regarding', 'with respect to'],
        'comparisons': ['compare', 'contrast', 'difference', 'versus', 'vs', 'better', 'worse'],
        'continuations': ['continue', 'go on', 'tell me more', 'explain further', 'elaborate']
    }
    
    # Topic keywords for maintaining subject continuity
    TOPIC_KEYWORDS = {
        'rna': ['rna', 'ribonucleic', 'mrna', 'trna', 'rrna', 'extraction', 'purification'],
        'crispr': ['crispr', 'cas9', 'cas12', 'fncas9', 'guide', 'grna', 'sgrna', 'editing'],
        'disease': ['disease', 'mlc', 'patient', 'clinical', 'therapy', 'treatment', 'diagnosis'],
        'protocol': ['protocol', 'method', 'procedure', 'step', 'technique', 'experiment'],
        'thesis': ['thesis', 'research', 'study', 'findings', 'results', 'conclusion']
    }
    
    def __init__(self, context_window: int = 10):
        self.context_window = context_window
        self.topic_history = defaultdict(int)
    
    def build_enhanced_context(self, recent_messages: List[Any], current_query: str) -> Dict[str, Any]:
        """Build enhanced context with better coherence."""
        
        if not recent_messages:
            return {
                'query': current_query,
                'context': '',
                'detected_topics': [],
                'needs_clarification': False,
                'conversation_summary': None
            }
        
        # Extract conversation elements
        conversation_data = self._extract_conversation_data(recent_messages)
        
        # Detect current query intent and references
        query_analysis = self._analyze_query(current_query, conversation_data)
        
        # Resolve pronouns and references
        resolved_query = self._resolve_references(current_query, conversation_data, query_analysis)
        
        # Build contextual query
        contextual_query = self._build_contextual_query(
            resolved_query, 
            conversation_data, 
            query_analysis
        )
        
        # Generate conversation summary if needed
        summary = None
        if len(recent_messages) > 6:
            summary = self._generate_conversation_summary(conversation_data)
        
        return {
            'query': contextual_query,
            'context': conversation_data['full_context'],
            'detected_topics': query_analysis['topics'],
            'needs_clarification': query_analysis['ambiguous'],
            'conversation_summary': summary,
            'resolved_references': query_analysis.get('resolved_refs', {}),
            'conversation_topics': list(self.topic_history.keys())
        }
    
    def _extract_conversation_data(self, messages: List[Any]) -> Dict[str, Any]:
        """Extract structured data from conversation history."""
        data = {
            'user_queries': [],
            'assistant_responses': [],
            'topics': defaultdict(int),
            'entities': set(),
            'full_context': '',
            'last_topic': None,
            'last_entities': []
        }
        
        context_parts = []
        
        for msg in messages[-self.context_window:]:
            if msg.role == 'user':
                data['user_queries'].append(msg.content)
                context_parts.append(f"User: {msg.content}")
                # Track topics
                for topic, keywords in self.TOPIC_KEYWORDS.items():
                    if any(kw in msg.content.lower() for kw in keywords):
                        data['topics'][topic] += 1
                        self.topic_history[topic] += 1
            else:
                # Extract key information from assistant responses
                response_summary = self._summarize_response(msg.content)
                data['assistant_responses'].append(response_summary)
                context_parts.append(f"Assistant: {response_summary}")
                
                # Extract entities from metadata if available
                if hasattr(msg, 'metadata') and msg.metadata:
                    entities = msg.metadata.get('entities', [])
                    data['entities'].update(entities)
        
        # Identify last discussed topic and entities
        if data['assistant_responses']:
            last_response = messages[-1].content if messages[-1].role == 'assistant' else ''
            data['last_topic'] = self._identify_main_topic(last_response)
            data['last_entities'] = self._extract_entities(last_response)
        
        data['full_context'] = '\n'.join(context_parts[-6:])  # Last 3 exchanges
        
        return data
    
    def _analyze_query(self, query: str, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the current query for context dependencies."""
        query_lower = query.lower()
        analysis = {
            'has_references': False,
            'reference_types': [],
            'topics': [],
            'ambiguous': False,
            'needs_previous_context': False,
            'comparative': False,
            'continuation': False
        }
        
        # Check for reference words
        for ref_type, words in self.REFERENCE_WORDS.items():
            if any(word in query_lower for word in words):
                analysis['has_references'] = True
                analysis['reference_types'].append(ref_type)
        
        # Check for topics
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                analysis['topics'].append(topic)
        
        # Check if query is too short or ambiguous
        if len(query.split()) < 4 and analysis['has_references']:
            analysis['ambiguous'] = True
            analysis['needs_previous_context'] = True
        
        # Check for comparative queries
        if any(word in query_lower for word in self.REFERENCE_WORDS['comparisons']):
            analysis['comparative'] = True
        
        # Check for continuation requests
        if any(phrase in query_lower for phrase in self.REFERENCE_WORDS['continuations']):
            analysis['continuation'] = True
        
        return analysis
    
    def _resolve_references(self, query: str, conversation_data: Dict[str, Any], 
                          query_analysis: Dict[str, Any]) -> str:
        """Resolve pronouns and references to their antecedents."""
        if not query_analysis['has_references']:
            return query
        
        resolved_query = query
        resolved_refs = {}
        
        # Simple pronoun resolution
        if 'pronouns' in query_analysis['reference_types']:
            # Replace "it" with the last discussed topic or entity
            if conversation_data['last_topic']:
                for pronoun in ['it', 'this', 'that']:
                    if f' {pronoun} ' in f' {query.lower()} ':
                        resolved_query = re.sub(
                            rf'\b{pronoun}\b', 
                            conversation_data['last_topic'], 
                            resolved_query, 
                            flags=re.IGNORECASE
                        )
                        resolved_refs[pronoun] = conversation_data['last_topic']
            
            # Replace "they/them" with last entities
            if conversation_data['last_entities'] and len(conversation_data['last_entities']) > 1:
                for pronoun in ['they', 'them']:
                    if pronoun in query.lower():
                        entities_str = ' and '.join(conversation_data['last_entities'][:2])
                        resolved_query = resolved_query.replace(pronoun, entities_str)
                        resolved_refs[pronoun] = entities_str
        
        query_analysis['resolved_refs'] = resolved_refs
        return resolved_query
    
    def _build_contextual_query(self, resolved_query: str, conversation_data: Dict[str, Any],
                               query_analysis: Dict[str, Any]) -> str:
        """Build the final contextual query."""
        
        # For continuation requests, provide strong context
        if query_analysis['continuation']:
            last_topic = conversation_data['last_topic'] or "the previous topic"
            return f"Continuing our discussion about {last_topic}: {resolved_query}"
        
        # For comparative queries, include comparison context
        if query_analysis['comparative'] and conversation_data['assistant_responses']:
            last_item = self._extract_main_subject(conversation_data['assistant_responses'][-1])
            return f"Compare with {last_item}: {resolved_query}"
        
        # For ambiguous queries with references, add context
        if query_analysis['ambiguous'] and query_analysis['needs_previous_context']:
            if conversation_data['user_queries']:
                last_query_topic = self._extract_main_subject(conversation_data['user_queries'][-1])
                return f"Regarding {last_query_topic}, {resolved_query}"
        
        # For queries with unresolved references, add topic context
        if query_analysis['has_references'] and not query_analysis.get('resolved_refs'):
            topics = conversation_data['topics']
            if topics:
                main_topic = max(topics.items(), key=lambda x: x[1])[0]
                return f"In the context of {main_topic}: {resolved_query}"
        
        return resolved_query
    
    def _summarize_response(self, response: str, max_length: int = 200) -> str:
        """Create a concise summary of an assistant response."""
        # Extract first paragraph or key sentences
        sentences = response.split('. ')
        
        # Prioritize sentences with key information
        key_sentences = []
        for sent in sentences[:5]:  # Look at first 5 sentences
            if any(kw in sent.lower() for kw in ['is', 'are', 'involves', 'uses', 'shows']):
                key_sentences.append(sent)
        
        summary = '. '.join(key_sentences[:2]) if key_sentences else sentences[0]
        
        if len(summary) > max_length:
            summary = summary[:max_length] + '...'
        
        return summary
    
    def _identify_main_topic(self, text: str) -> str:
        """Identify the main topic discussed in the text."""
        text_lower = text.lower()
        
        # Count topic occurrences
        topic_counts = {}
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            if count > 0:
                topic_counts[topic] = count
        
        if topic_counts:
            return max(topic_counts.items(), key=lambda x: x[1])[0]
        
        # Fallback: extract first noun phrase
        if SPACY_AVAILABLE:
            doc = nlp(text[:500])  # Analyze first 500 chars
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) > 1:
                    return chunk.text
        
        # Simple fallback: first capitalized phrase
        words = text.split()
        for i, word in enumerate(words):
            if word[0].isupper() and i > 0:
                return ' '.join(words[i:i+3])
        
        return "the previous topic"
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text."""
        entities = []
        
        if SPACY_AVAILABLE:
            doc = nlp(text[:1000])  # Analyze first 1000 chars
            entities = [ent.text for ent in doc.ents if ent.label_ in ['PERSON', 'ORG', 'PRODUCT']]
        else:
            # Simple extraction: capitalized words
            words = text.split()
            for word in words:
                if word[0].isupper() and len(word) > 3:
                    entities.append(word)
        
        return list(set(entities))[:5]  # Return top 5 unique entities
    
    def _extract_main_subject(self, text: str) -> str:
        """Extract the main subject from a text."""
        # Simple approach: find first noun phrase after common verbs
        patterns = [
            r'about ([^,\.]+)',
            r'regarding ([^,\.]+)',
            r'is ([^,\.]+)',
            r'are ([^,\.]+)',
            r'involves ([^,\.]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback to main topic
        return self._identify_main_topic(text)
    
    def _generate_conversation_summary(self, conversation_data: Dict[str, Any]) -> str:
        """Generate a summary of the conversation for long chats."""
        topics_discussed = list(conversation_data['topics'].keys())
        num_exchanges = len(conversation_data['user_queries'])
        
        summary_parts = [
            f"Over the last {num_exchanges} exchanges, we discussed:"
        ]
        
        # Add main topics
        if topics_discussed:
            summary_parts.append(f"Topics: {', '.join(topics_discussed)}")
        
        # Add key entities
        if conversation_data['entities']:
            key_entities = list(conversation_data['entities'])[:5]
            summary_parts.append(f"Key items: {', '.join(key_entities)}")
        
        return ' '.join(summary_parts)