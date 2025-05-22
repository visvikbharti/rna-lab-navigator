# RNA Lab Navigator Performance Testing Framework

## Overview

This comprehensive performance testing framework ensures the RNA Lab Navigator meets its critical KPI requirement of ≤5s median end-to-end latency while maintaining high reliability and cost efficiency.

## Quick Start

### 1. Test Current System Performance

```bash
# Test current system with sample data
python tests/test_current_performance.py

# Run comprehensive performance test suite
python tests/run_performance_tests.py --all

# Quick performance check
python tests/run_performance_tests.py --quick
```

### 2. Load Testing

```bash
# Install Locust for load testing
pip install locust

# Run load test with 20 users for 5 minutes
python tests/run_performance_tests.py --load-test --users 20 --duration 300

# Run Locust directly for more control
locust -f tests/load_testing/locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 300s --headless
```

### 3. Benchmark Testing

```bash
# Install pytest-benchmark
pip install pytest-benchmark

# Run benchmark tests
pytest tests/benchmark/ --benchmark-only --benchmark-sort=mean

# Compare benchmarks over time
pytest tests/benchmark/ --benchmark-only --benchmark-compare
```

## Framework Components

### 1. Performance Test Scripts

#### Core Tests (`tests/test_performance/`)
- **`test_rag_performance.py`**: Comprehensive RAG pipeline performance tests
  - End-to-end latency testing
  - Concurrent load testing
  - Memory usage monitoring
  - Component-specific performance validation

#### Benchmark Tests (`tests/benchmark/`)
- **`test_benchmark_rag.py`**: Automated benchmark tests using pytest-benchmark
  - Query endpoint benchmarks
  - Component-level benchmarks
  - Performance regression detection
  - Memory usage benchmarks

#### Load Testing (`tests/load_testing/`)
- **`locustfile.py`**: Locust-based load testing scenarios
  - Realistic user behavior simulation
  - Burst traffic testing
  - Slow connection simulation
  - KPI compliance monitoring

- **`stress_test.py`**: Async stress testing with detailed metrics
  - High concurrency testing
  - Performance degradation analysis
  - System breaking point identification

### 2. Performance Monitoring

#### Real-time Monitoring (`tests/performance_monitoring/`)
- **`performance_profiler.py`**: Comprehensive performance profiling
  - Real-time metrics collection
  - Bottleneck identification
  - Component performance analysis
  - Optimization recommendations

- **`middleware.py`**: Django middleware for request monitoring
  - Automatic request/response tracking
  - Database query profiling
  - RAG pipeline monitoring
  - Cache performance tracking

### 3. Test Automation

#### Test Runner (`tests/run_performance_tests.py`)
- Orchestrates all performance tests
- Generates comprehensive reports
- KPI compliance analysis
- Automated optimization recommendations

#### Current System Testing (`tests/test_current_performance.py`)
- Tests actual system with sample data
- Real-world performance validation
- Production readiness assessment

## Performance KPIs

The system must meet these requirements:

| Metric | Target | Critical |
|--------|--------|----------|
| Median end-to-end latency | ≤ 5 seconds | ✅ |
| P95 latency | ≤ 5 seconds | ✅ |
| Success rate | ≥ 95% | ✅ |
| Concurrent users | Support lab team (21 members) | ✅ |
| Monthly OpenAI cost | ≤ $30 | ✅ |

## Test Scenarios

### 1. Unit Performance Tests

```bash
# Run unit performance tests
pytest tests/test_performance/ -v

# Run specific test categories
pytest tests/test_performance/ -m "not slow"  # Quick tests only
pytest tests/test_performance/ -m "slow"      # Comprehensive tests only
```

**Test Coverage:**
- Query endpoint response times
- RAG pipeline component performance
- Database query optimization
- Memory usage patterns
- Concurrent request handling

### 2. Load Testing Scenarios

#### Basic Load Test
```bash
# 20 users, 3 minutes
locust -f tests/load_testing/locustfile.py --host=http://localhost:8000 -u 20 -r 2 -t 180s --headless
```

#### Stress Test
```bash
# 50 users, 5 minutes
python tests/load_testing/stress_test.py --host=http://localhost:8000 --users 50 --duration 300
```

#### Burst Traffic Test
```bash
# Simulate sudden traffic spikes
locust -f tests/load_testing/locustfile.py --host=http://localhost:8000 -u 100 -r 10 -t 120s --headless
```

### 3. Benchmark Testing

```bash
# Run all benchmarks
pytest tests/benchmark/ --benchmark-only

# Save benchmark results for comparison
pytest tests/benchmark/ --benchmark-only --benchmark-json=baseline.json

# Compare with previous benchmarks
pytest tests/benchmark/ --benchmark-only --benchmark-compare=baseline.json
```

## Monitoring and Profiling

### 1. Enable Performance Monitoring

Add to `settings.py`:

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
SLOW_REQUEST_THRESHOLD = 5.0      # Log requests slower than 5s
SLOW_QUERY_THRESHOLD = 0.1        # Log DB queries slower than 100ms
```

### 2. Real-time Performance Monitoring

```python
from tests.performance_monitoring.performance_profiler import get_profiler

# Get profiler instance
profiler = get_profiler()

# Check component performance
search_perf = profiler.get_component_performance('api.search', hours=24)
rag_perf = profiler.get_component_performance('api.rag', hours=24)

# Check system health
health = profiler.get_system_health(minutes=60)

# Identify bottlenecks
bottlenecks = profiler.identify_bottlenecks(hours=24)

# Generate optimization report
report = profiler.generate_optimization_report()
```

### 3. Using Performance Decorators

```python
from tests.performance_monitoring.performance_profiler import profile, measure

# Decorator for function profiling
@profile('my_component')
def my_function():
    # Function implementation
    pass

# Context manager for operation profiling
with measure('my_component', 'complex_operation'):
    # Complex operation
    pass
```

## Performance Analysis

### 1. Interpreting Test Results

#### Response Time Analysis
- **Mean**: Average response time - should be < 3s
- **Median**: 50th percentile - should be ≤ 5s (KPI requirement)
- **P95**: 95th percentile - should be ≤ 5s (KPI requirement)
- **P99**: 99th percentile - should be < 8s

#### Success Rate Analysis
- **Target**: ≥ 95% success rate
- **Error Types**: Network, timeout, server errors
- **Failure Patterns**: Identify systematic issues

#### Throughput Analysis
- **Requests/Second**: System capacity
- **Concurrent Users**: Maximum supported load
- **Scalability**: Performance under increasing load

### 2. Bottleneck Identification

Common bottlenecks and solutions:

#### Vector Search Bottlenecks
- **Symptoms**: Search takes > 2s
- **Solutions**: Optimize HNSW parameters, implement caching

#### LLM API Bottlenecks
- **Symptoms**: High latency, API rate limits
- **Solutions**: Response caching, parallel processing, model optimization

#### Database Bottlenecks
- **Symptoms**: Slow query logs, high DB time
- **Solutions**: Add indexes, optimize queries, connection pooling

#### Memory/CPU Bottlenecks
- **Symptoms**: High resource usage, degraded performance
- **Solutions**: Optimize algorithms, implement caching, scale resources

## Optimization Strategies

### 1. Immediate Optimizations (< 1 day)

```python
# 1. Enable caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'TIMEOUT': 3600,
    }
}

# 2. Optimize database queries
# Add indexes for common queries
CREATE INDEX idx_query_history_user_created ON api_queryhistory(user_id, created_at DESC);

# 3. Implement query result caching
from django.core.cache import cache

def cached_query_response(query_text):
    cache_key = f"query:{hash(query_text)}"
    result = cache.get(cache_key)
    if not result:
        result = perform_rag_query(query_text)
        cache.set(cache_key, result, 3600)
    return result
```

### 2. Short-term Optimizations (< 1 week)

- Implement parallel processing for RAG components
- Add LLM response caching
- Optimize vector search parameters
- Implement connection pooling

### 3. Long-term Optimizations (< 1 month)

- Implement horizontal scaling with load balancers
- Add advanced caching strategies
- Optimize system architecture
- Implement proactive scaling

## CI/CD Integration

### 1. GitHub Actions Performance Testing

Create `.github/workflows/performance.yml`:

```yaml
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
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-benchmark locust
      
      - name: Start services
        run: |
          docker-compose up -d postgres redis weaviate
          
      - name: Run performance tests
        run: |
          python tests/run_performance_tests.py --quick
          
      - name: Check KPI compliance
        run: |
          python tests/check_kpi_compliance.py
```

### 2. Performance Regression Detection

```bash
# Baseline establishment
pytest tests/benchmark/ --benchmark-only --benchmark-json=baseline.json

# Performance regression check
pytest tests/benchmark/ --benchmark-only --benchmark-compare=baseline.json --benchmark-compare-fail=mean:5%
```

## Troubleshooting

### Common Issues

#### 1. High Response Times
```bash
# Check component performance
python tests/test_current_performance.py

# Identify bottlenecks
python -c "
from tests.performance_monitoring.performance_profiler import get_profiler
profiler = get_profiler()
bottlenecks = profiler.identify_bottlenecks()
for b in bottlenecks:
    print(f'{b[\"type\"]}: {b[\"component\"]} - {b[\"severity\"]}')
"
```

#### 2. Load Test Failures
```bash
# Check system resources during load test
python tests/load_testing/stress_test.py --host=http://localhost:8000 --users 10 --duration 60

# Review load test logs
tail -f locust.log
```

#### 3. Memory Leaks
```bash
# Monitor memory usage
python -c "
import psutil
import time
process = psutil.Process()
for i in range(60):
    print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
    time.sleep(1)
"
```

## Performance Optimization Checklist

### Pre-deployment
- [ ] All performance tests pass
- [ ] KPI compliance verified (≤5s median latency)
- [ ] Load testing completed successfully
- [ ] Memory usage is stable
- [ ] No critical bottlenecks identified
- [ ] OpenAI cost projections within budget

### Post-deployment
- [ ] Performance monitoring enabled
- [ ] Alerting configured
- [ ] Regular performance reviews scheduled
- [ ] Optimization roadmap created
- [ ] Team trained on performance tools

## Best Practices

### 1. Regular Testing
- Run performance tests on every major change
- Establish performance baselines
- Monitor trends over time
- Set up automated alerts

### 2. Proactive Optimization
- Monitor performance metrics continuously
- Identify bottlenecks before they impact users
- Implement caching strategies
- Optimize based on real usage patterns

### 3. Documentation
- Document performance requirements
- Track optimization efforts
- Share performance insights with team
- Maintain optimization guidelines

## Support and Resources

- **Performance Guide**: `docs/PERFORMANCE_OPTIMIZATION_GUIDE.md`
- **Architecture docs**: `docs/developer_facing_design_dossier.md`
- **Issue Tracker**: GitHub Issues with `performance` label
- **Team Contact**: Performance optimization team

## Contributing

When adding new features:

1. Include performance tests for new components
2. Ensure KPI compliance is maintained
3. Add appropriate monitoring and profiling
4. Update documentation as needed
5. Consider performance impact in design decisions

---

This performance testing framework ensures the RNA Lab Navigator meets its ambitious ≤5s latency goal while maintaining high reliability and cost efficiency. Regular use of these tools will help maintain optimal performance as the system evolves.