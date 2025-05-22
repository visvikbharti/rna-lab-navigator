# RNA Lab Navigator Performance Optimization Guide

## Overview

This guide provides comprehensive strategies for optimizing the RNA Lab Navigator to meet the ≤5s latency KPI requirement. It covers performance monitoring, bottleneck identification, and specific optimization techniques for each component of the system.

## Performance KPIs

The system must meet these performance requirements:

- **Median end-to-end latency**: ≤ 5 seconds
- **P95 latency**: ≤ 5 seconds  
- **Success rate**: ≥ 95%
- **Throughput**: Handle multiple concurrent users efficiently
- **First-month OpenAI spend**: ≤ $30

## Performance Testing Framework

### 1. Running Performance Tests

```bash
# Run all performance tests
python tests/run_performance_tests.py --all

# Quick performance check
python tests/run_performance_tests.py --quick

# Load testing with specific parameters
python tests/run_performance_tests.py --load-test --users 50 --duration 300

# Benchmark testing only
python tests/run_performance_tests.py --benchmark-only
```

### 2. Continuous Monitoring

Enable performance monitoring middleware in `settings.py`:

```python
MIDDLEWARE = [
    # ... existing middleware ...
    'tests.performance_monitoring.middleware.PerformanceMonitoringMiddleware',
    'tests.performance_monitoring.middleware.RAGPerformanceMiddleware',
    'tests.performance_monitoring.middleware.DatabaseQueryProfilerMiddleware',
    'tests.performance_monitoring.middleware.CachePerformanceMiddleware',
]

# Performance settings
PERFORMANCE_DEBUG_HEADERS = True  # Development only
SLOW_REQUEST_THRESHOLD = 5.0  # Log requests slower than 5s
SLOW_QUERY_THRESHOLD = 0.1   # Log DB queries slower than 100ms
```

## Component-Specific Optimizations

### 1. Vector Search Optimization

**Current Performance Issues:**
- Vector search can take 1-3 seconds for complex queries
- HNSW index parameters may not be optimal
- Hybrid search alpha parameter needs tuning

**Optimization Strategies:**

#### A. Weaviate Configuration
```python
# Optimize HNSW parameters in Weaviate schema
"vectorIndexConfig": {
    "ef": 200,           # Higher for better recall
    "efConstruction": 128, # Lower for faster indexing
    "maxConnections": 32   # Balanced connectivity
}
```

#### B. Search Parameters
```python
# api/ingestion/embeddings_utils.py
def search_weaviate(query_text, limit=10, use_hybrid=True, alpha=0.75):
    # Optimize alpha based on query type
    if len(query_text.split()) <= 3:
        alpha = 0.8  # Favor vector search for short queries
    else:
        alpha = 0.7  # More balanced for long queries
```

#### C. Caching Strategy
```python
from django.core.cache import cache
import hashlib

def cached_vector_search(query_text, **kwargs):
    # Create cache key
    cache_key = f"search:{hashlib.md5(query_text.encode()).hexdigest()}"
    
    # Check cache first
    result = cache.get(cache_key)
    if result is not None:
        return result
    
    # Perform search
    result = search_weaviate(query_text, **kwargs)
    
    # Cache for 1 hour
    cache.set(cache_key, result, 3600)
    return result
```

### 2. RAG Pipeline Optimization

**Current Performance Issues:**
- Context enhancement can take 500ms-1s
- Reranking adds significant latency
- LLM API calls are the main bottleneck

**Optimization Strategies:**

#### A. Parallel Processing
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def parallel_rag_pipeline(query_text):
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Run these in parallel
        search_future = executor.submit(search_weaviate, query_text)
        embedding_future = executor.submit(generate_embedding, query_text)
        
        # Get results
        search_results = search_future.result()
        query_embedding = embedding_future.result()
        
        # Continue with enhanced processing
        enhanced_chunks = enhance_rag_context(query_text, search_results)
        return enhanced_chunks
```

#### B. Smart Reranking
```python
def selective_reranking(query_text, chunks, threshold=0.8):
    """Only rerank if initial relevance scores are low."""
    max_score = max(chunk.get('relevance_score', 0) for chunk in chunks)
    
    if max_score >= threshold:
        # High confidence results, skip reranking
        return sorted(chunks, key=lambda x: x.get('relevance_score', 0), reverse=True)
    else:
        # Low confidence, use reranking
        return rerank_chunks_for_rag(query_text, chunks)
```

#### C. LLM Response Caching
```python
def cached_llm_response(messages, **kwargs):
    # Create deterministic cache key
    content = json.dumps(messages, sort_keys=True)
    cache_key = f"llm:{hashlib.md5(content.encode()).hexdigest()}"
    
    # Check cache
    cached_response = cache.get(cache_key)
    if cached_response:
        return cached_response
    
    # Call LLM
    response = openai.ChatCompletion.create(messages=messages, **kwargs)
    
    # Cache for 24 hours
    cache.set(cache_key, response, 86400)
    return response
```

### 3. Database Optimization

**Current Performance Issues:**
- Query history queries can be slow
- Analytics queries lack proper indexing
- N+1 query problems in some views

**Optimization Strategies:**

#### A. Database Indexes
```sql
-- Add these indexes for better performance
CREATE INDEX idx_query_history_user_created ON api_queryhistory(user_id, created_at DESC);
CREATE INDEX idx_query_history_confidence ON api_queryhistory(confidence_score);
CREATE INDEX idx_analytics_timestamp ON api_searchanalytics(created_at);
CREATE INDEX idx_feedback_rating ON api_feedback(rating, created_at);
```

#### B. Query Optimization
```python
# Use select_related and prefetch_related
def get_user_query_history(user, limit=10):
    return QueryHistory.objects.select_related('user').filter(
        user=user
    ).order_by('-created_at')[:limit]

# Use database aggregation instead of Python loops
def get_average_confidence_score(user):
    return QueryHistory.objects.filter(user=user).aggregate(
        avg_score=Avg('confidence_score')
    )['avg_score']
```

#### C. Connection Pooling
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        },
        'CONN_MAX_AGE': 600,  # 10 minutes
    }
}
```

### 4. Caching Strategy

**Multi-Level Caching Approach:**

#### A. Redis Configuration
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'rna_lab',
        'TIMEOUT': 3600,  # 1 hour default
    }
}
```

#### B. Cache Keys Strategy
```python
# Cache key patterns
CACHE_KEYS = {
    'search_results': 'search:query:{query_hash}:doc_type:{doc_type}',
    'llm_response': 'llm:messages:{messages_hash}',
    'user_analytics': 'analytics:user:{user_id}:period:{period}',
    'document_chunks': 'chunks:doc:{doc_id}',
}
```

#### C. Cache Warming
```python
from celery import shared_task

@shared_task
def warm_cache_for_common_queries():
    """Pre-cache responses for common queries."""
    common_queries = [
        "What is RNA?",
        "How to extract RNA?",
        "PCR protocol steps",
        "Western blot procedure",
    ]
    
    for query in common_queries:
        # Pre-generate and cache responses
        cached_vector_search(query)
        cached_llm_response([{"role": "user", "content": query}])
```

## System Architecture Optimizations

### 1. Async Processing

Convert synchronous operations to async where possible:

```python
# views.py
from django.http import JsonResponse
from asgiref.sync import sync_to_async
import asyncio

async def async_query_view(request):
    query_data = json.loads(request.body)
    question = query_data['question']
    
    # Run search and LLM calls in parallel
    search_task = asyncio.create_task(async_search(question))
    
    # Get search results
    search_results = await search_task
    
    # Generate response
    response = await async_generate_response(question, search_results)
    
    return JsonResponse(response)
```

### 2. Connection Pooling

#### A. Database Connection Pooling
```python
# Use pgbouncer for PostgreSQL
# /etc/pgbouncer/pgbouncer.ini
[databases]
rna_lab = host=localhost port=5432 dbname=rna_lab

[pgbouncer]
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
```

#### B. HTTP Connection Pooling
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create a session with connection pooling
session = requests.Session()
retry_strategy = Retry(total=3, backoff_factor=1)
adapter = HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=retry_strategy
)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

### 3. Load Balancing and Scaling

#### A. Horizontal Scaling with Celery
```python
# celery.py
from celery import Celery

app = Celery('rna_backend')

@app.task(bind=True)
def process_query_async(self, query_data):
    """Process query asynchronously to handle load spikes."""
    try:
        result = perform_rag_query(query_data)
        return result
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60, max_retries=3)
```

#### B. Rate Limiting
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='10/m', method='POST')
def query_view(request):
    """Limit users to 10 queries per minute."""
    # ... query processing ...
```

## Monitoring and Alerting

### 1. Performance Metrics Dashboard

Create a real-time dashboard to monitor:

- Request latency percentiles (P50, P95, P99)
- Throughput (requests per second)
- Error rates
- Cache hit rates
- Database query performance
- System resource usage

### 2. Automated Alerts

Set up alerts for:

```python
# Performance thresholds
ALERT_THRESHOLDS = {
    'p95_latency': 5.0,      # seconds
    'error_rate': 0.05,      # 5%
    'cache_miss_rate': 0.3,  # 30%
    'memory_usage': 0.85,    # 85%
    'cpu_usage': 0.80,       # 80%
}
```

### 3. Performance Testing CI/CD

```yaml
# .github/workflows/performance.yml
name: Performance Tests
on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Performance Tests
        run: |
          python tests/run_performance_tests.py --quick
      - name: Check KPI Compliance
        run: |
          python tests/check_kpi_compliance.py
```

## Cost Optimization for OpenAI API

### 1. Smart Model Selection

```python
def select_optimal_model(query_complexity):
    """Select the most cost-effective model based on query complexity."""
    if query_complexity < 0.3:
        return "gpt-3.5-turbo"  # Cheaper for simple queries
    else:
        return "gpt-4"  # Better quality for complex queries

def calculate_query_complexity(query_text):
    """Calculate query complexity score."""
    factors = {
        'length': len(query_text.split()) / 50,  # Normalize by typical length
        'technical_terms': count_technical_terms(query_text) / 10,
        'question_complexity': analyze_question_type(query_text)
    }
    return min(sum(factors.values()) / len(factors), 1.0)
```

### 2. Token Usage Optimization

```python
def optimize_prompt_tokens(context_chunks, max_tokens=3000):
    """Optimize prompt to stay within token limits."""
    prompt_tokens = count_tokens(base_prompt)
    available_tokens = max_tokens - prompt_tokens - 500  # Reserve for response
    
    # Prioritize and truncate context
    optimized_context = []
    current_tokens = 0
    
    for chunk in sorted(context_chunks, key=lambda x: x['relevance_score'], reverse=True):
        chunk_tokens = count_tokens(chunk['content'])
        if current_tokens + chunk_tokens <= available_tokens:
            optimized_context.append(chunk)
            current_tokens += chunk_tokens
        else:
            break
    
    return optimized_context
```

### 3. Response Caching

Implement aggressive caching for OpenAI responses:

```python
CACHE_TIMEOUT_BY_QUERY_TYPE = {
    'factual': 86400 * 7,    # 7 days for factual questions
    'protocol': 86400 * 3,   # 3 days for protocols
    'recent': 86400,         # 1 day for recent research
    'specific': 86400 * 30,  # 30 days for very specific questions
}
```

## Performance Optimization Checklist

### Before Deployment

- [ ] Run full performance test suite
- [ ] Verify P95 latency ≤ 5s
- [ ] Confirm success rate ≥ 95%
- [ ] Test under expected load
- [ ] Validate cache hit rates
- [ ] Check database query performance
- [ ] Verify OpenAI API cost projections

### Production Monitoring

- [ ] Set up performance dashboards
- [ ] Configure alerting thresholds
- [ ] Monitor KPI compliance
- [ ] Track cost metrics
- [ ] Review slow query logs
- [ ] Monitor cache performance
- [ ] Check error rates

### Regular Optimization

- [ ] Weekly performance reviews
- [ ] Monthly cost analysis
- [ ] Quarterly architecture review
- [ ] Continuous profiling
- [ ] Cache strategy optimization
- [ ] Database performance tuning
- [ ] Load testing with production data

## Troubleshooting Common Performance Issues

### Issue: High Response Times

**Diagnosis:**
1. Check if it's a specific component (search, LLM, database)
2. Review recent changes
3. Analyze system resource usage

**Solutions:**
- Increase cache timeouts
- Optimize database queries
- Scale vector search resources
- Implement request queuing

### Issue: High OpenAI Costs

**Diagnosis:**
1. Analyze token usage patterns
2. Check cache miss rates
3. Review model selection logic

**Solutions:**
- Implement more aggressive caching
- Optimize prompt templates
- Use cheaper models for simple queries
- Implement result deduplication

### Issue: Database Bottlenecks

**Diagnosis:**
1. Check slow query logs
2. Analyze query patterns
3. Review index usage

**Solutions:**
- Add missing indexes
- Optimize query patterns
- Implement read replicas
- Use database connection pooling

This guide provides a comprehensive framework for optimizing the RNA Lab Navigator to meet and exceed the ≤5s latency KPI while maintaining cost efficiency and system reliability.