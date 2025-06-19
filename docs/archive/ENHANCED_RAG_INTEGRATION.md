# Enhanced RAG Integration Guide

## Overview

The RNA Lab Navigator now includes an enhanced RAG (Retrieval-Augmented Generation) system that provides:

1. **Multi-hop reasoning** for complex queries
2. **Conversation memory** for contextual understanding
3. **Knowledge graph integration** for better relationships
4. **Intelligent query routing** to appropriate models
5. **Reasoning traces** for transparency

## API Integration

### 1. Main Query Endpoint Enhancement

The main `/api/query/` endpoint now supports enhanced RAG features:

```json
POST /api/query/
{
  "query": "How does RNA interference differ from CRISPR?",
  "use_enhanced": true,      // Enable enhanced RAG (default: true)
  "session_id": "uuid-here", // For conversation continuity
  "use_multihop": false,     // Force multi-hop reasoning
  "doc_type": "paper"        // Filter by document type
}
```

**Enhanced Response Format:**
```json
{
  "answer": "RNA interference and CRISPR differ in several key ways...",
  "sources": [...],
  "confidence_score": 0.92,
  "reasoning_trace": [
    {
      "step_number": 1,
      "description": "Understanding RNA interference mechanism",
      "conclusion": "RNAi uses small RNA molecules...",
      "confidence": 0.95,
      "source_count": 3
    }
  ],
  "session_id": "uuid-here",
  "is_enhanced": true,
  "model_used": "gpt-4o"
}
```

### 2. Dedicated Enhanced RAG Endpoint

For direct access to enhanced features:

```json
POST /api/query/enhanced/
{
  "query": "What are the latest developments in RNA therapeutics?",
  "session_id": "uuid-here",
  "user_context": {
    "expertise_level": "expert",
    "focus_area": "therapeutics"
  }
}
```

### 3. Auto-complete Endpoint

Intelligent query suggestions based on context:

```json
POST /api/query/autocomplete/
{
  "partial_query": "How to design gRNA for",
  "session_id": "uuid-here",
  "limit": 5
}
```

**Response:**
```json
{
  "suggestions": [
    "How to design gRNA for CRISPR-Cas9",
    "How to design gRNA for specific targets",
    "How to design gRNA for minimal off-targets",
    "How to design gRNA for gene knockout",
    "How to design gRNA for base editing"
  ]
}
```

### 4. Conversation History Endpoint

Access and manage conversation context:

```json
GET /api/query/conversation/{session_id}/
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "history": [
    {
      "query": "What is RNA interference?",
      "answer": "RNA interference (RNAi) is...",
      "timestamp": "2025-01-26T10:00:00Z",
      "confidence_score": 0.89,
      "sources": [...]
    }
  ],
  "turn_count": 3
}
```

## Frontend Integration

### 1. Update Search Component

```javascript
// In EnhancedSearchInterface.jsx
const [sessionId] = useState(() => {
  // Persist session ID in localStorage
  const stored = localStorage.getItem('rag-session-id');
  if (stored) return stored;
  const newId = uuidv4();
  localStorage.setItem('rag-session-id', newId);
  return newId;
});

const handleSearch = async (query) => {
  const response = await fetch('/api/query/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      session_id: sessionId,
      use_enhanced: true
    })
  });
  
  const data = await response.json();
  
  // Display reasoning trace if available
  if (data.reasoning_trace) {
    setReasoningSteps(data.reasoning_trace);
  }
};
```

### 2. Display Reasoning Traces

```javascript
// ReasoningTraceDisplay component
{reasoningSteps && (
  <div className="reasoning-trace">
    <h3>How I found this answer:</h3>
    {reasoningSteps.map((step, idx) => (
      <div key={idx} className="reasoning-step">
        <span className="step-number">{step.step_number}</span>
        <p className="step-description">{step.description}</p>
        <p className="step-conclusion">{step.conclusion}</p>
        <div className="step-confidence">
          Confidence: {(step.confidence * 100).toFixed(0)}%
        </div>
      </div>
    ))}
  </div>
)}
```

### 3. Auto-complete Integration

```javascript
// In search input component
const [suggestions, setSuggestions] = useState([]);

const handleInputChange = async (value) => {
  if (value.length > 3) {
    const response = await fetch('/api/query/autocomplete/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        partial_query: value,
        session_id: sessionId
      })
    });
    
    const data = await response.json();
    setSuggestions(data.suggestions);
  }
};
```

## Configuration

### Backend Settings

Add to `settings.py`:

```python
# Enhanced RAG Configuration
ENHANCED_RAG_CONFIG = {
    'enable_multi_hop': True,
    'max_reasoning_steps': 5,
    'conversation_memory_ttl': 3600,  # 1 hour
    'knowledge_graph_enabled': True,
    'auto_complete_cache_ttl': 300,   # 5 minutes
}

# Model routing thresholds
MODEL_COMPLEXITY_THRESHOLDS = {
    'simple': 0.3,
    'moderate': 0.7,
    'complex': 1.0
}
```

## Performance Considerations

1. **Async Processing**: Enhanced RAG uses async processing for better performance
2. **Caching**: Results are cached at multiple levels
3. **Session Management**: Sessions expire after 1 hour of inactivity
4. **Rate Limiting**: Apply appropriate rate limits to prevent abuse

## Monitoring

Track these metrics:

1. **Response Time**: Enhanced vs standard RAG
2. **Confidence Scores**: Distribution and trends
3. **Multi-hop Usage**: How often complex reasoning is triggered
4. **Session Length**: Average conversation turns
5. **Cache Hit Rate**: For both queries and auto-complete

## Fallback Behavior

The system gracefully falls back to standard RAG when:

1. Enhanced RAG is unavailable
2. Query complexity doesn't warrant enhanced processing
3. Session context is corrupted
4. Rate limits are exceeded

## Testing

Test enhanced features:

```bash
# Test multi-hop reasoning
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare the efficiency of different RNA extraction methods for different tissue types",
    "use_enhanced": true
  }'

# Test conversation continuity
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What about for brain tissue specifically?",
    "session_id": "previous-session-id",
    "use_enhanced": true
  }'
```

## Future Enhancements

1. **Federated Learning**: Learn from usage patterns while preserving privacy
2. **Custom Knowledge Graphs**: Domain-specific relationship mappings
3. **Multi-modal Support**: Integrate figure analysis into reasoning
4. **Collaborative Sessions**: Share context between researchers
5. **Export Reasoning**: Generate reports with full reasoning traces