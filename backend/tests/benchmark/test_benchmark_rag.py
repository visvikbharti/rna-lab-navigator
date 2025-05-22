"""
Automated performance benchmarking for RNA Lab Navigator using pytest-benchmark.

This module provides comprehensive benchmark tests for the RAG pipeline,
ensuring consistent performance monitoring and regression detection.

Install dependencies:
    pip install pytest-benchmark pytest-mock

Run benchmarks:
    pytest tests/benchmark/ --benchmark-only --benchmark-sort=mean
    pytest tests/benchmark/ --benchmark-only --benchmark-compare
    pytest tests/benchmark/ --benchmark-only --benchmark-json=benchmark_results.json
"""

import pytest
import time
import random
from unittest.mock import Mock, patch
from django.test import override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient

# Benchmark test data
BENCHMARK_QUERIES = [
    "What is RNA?",
    "How do you extract RNA from cells?",
    "What is the difference between DNA and RNA?",
    "Explain PCR protocol steps",
    "What are microRNAs?",
    "How does transcription work?",
    "What is qPCR?",
    "Describe western blot procedure",
]

COMPLEX_QUERIES = [
    "What is the relationship between RNA structure and function in ribozymes and how do post-transcriptional modifications affect RNA stability?",
    "Explain the mechanisms of RNA interference and its therapeutic applications in treating genetic diseases",
    "How do long non-coding RNAs regulate gene expression and what role do they play in cancer development?",
]

@pytest.fixture
def benchmark_client():
    """Fixture providing authenticated API client for benchmarks."""
    client = APIClient()
    user = User.objects.create_user(
        username="benchmark_user",
        password="test_password",
        email="benchmark@test.com"
    )
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def mock_dependencies():
    """Mock external dependencies for consistent benchmarking."""
    with patch('api.ingestion.embeddings_utils.search_weaviate') as mock_search, \
         patch('openai.Embedding.create') as mock_embed, \
         patch('openai.ChatCompletion.create') as mock_chat:
        
        # Mock search results
        mock_search.return_value = [
            {
                'content': 'RNA is a nucleic acid molecule...',
                'title': 'RNA Biology Basics',
                'doc_type': 'paper',
                'author': 'Smith et al.',
                'year': '2023',
                'relevance_score': 0.95
            },
            {
                'content': 'Transcription is the process...',
                'title': 'Gene Expression',
                'doc_type': 'paper',
                'author': 'Jones et al.',
                'year': '2022',
                'relevance_score': 0.88
            }
        ]
        
        # Mock embedding generation
        mock_embed.return_value = Mock(data=[Mock(embedding=[0.1] * 1536)])
        
        # Mock LLM response
        mock_chat.return_value = Mock(
            choices=[Mock(message=Mock(content="This is a test answer about RNA."))]
        )
        
        yield {
            'search': mock_search,
            'embed': mock_embed,
            'chat': mock_chat
        }


class TestQueryEndpointBenchmarks:
    """Benchmark tests for the main query endpoint."""
    
    @pytest.mark.benchmark(group="query_simple")
    def test_simple_query_performance(self, benchmark, benchmark_client, mock_dependencies):
        """Benchmark simple query performance."""
        client, user = benchmark_client
        
        def query_simple():
            response = client.post('/api/query/', {
                'question': random.choice(BENCHMARK_QUERIES),
                'doc_type': 'all'
            }, format='json')
            return response
        
        result = benchmark(query_simple)
        
        # Assertions
        assert result.status_code == 200
        
        # Performance assertions
        # These thresholds can be adjusted based on your requirements
        stats = benchmark.stats
        assert stats.mean < 5.0, f"Mean response time {stats.mean:.3f}s exceeds 5s KPI"
        assert stats.median < 5.0, f"Median response time {stats.median:.3f}s exceeds 5s KPI"
    
    @pytest.mark.benchmark(group="query_complex")
    def test_complex_query_performance(self, benchmark, benchmark_client, mock_dependencies):
        """Benchmark complex query performance."""
        client, user = benchmark_client
        
        def query_complex():
            response = client.post('/api/query/', {
                'question': random.choice(COMPLEX_QUERIES),
                'doc_type': 'all'
            }, format='json')
            return response
        
        result = benchmark(query_complex)
        
        # Assertions
        assert result.status_code == 200
        
        # Complex queries get slightly more lenient threshold
        stats = benchmark.stats
        assert stats.mean < 8.0, f"Mean response time {stats.mean:.3f}s exceeds 8s threshold"
        assert stats.median < 8.0, f"Median response time {stats.median:.3f}s exceeds 8s threshold"
    
    @pytest.mark.benchmark(group="query_doc_types")
    def test_doc_type_filtering_performance(self, benchmark, benchmark_client, mock_dependencies):
        """Benchmark query performance with different document type filters."""
        client, user = benchmark_client
        
        doc_types = ['all', 'paper', 'protocol', 'thesis']
        
        def query_with_filter():
            response = client.post('/api/query/', {
                'question': random.choice(BENCHMARK_QUERIES),
                'doc_type': random.choice(doc_types)
            }, format='json')
            return response
        
        result = benchmark(query_with_filter)
        
        assert result.status_code == 200
        stats = benchmark.stats
        assert stats.mean < 5.0, f"Filtered query mean time {stats.mean:.3f}s exceeds 5s KPI"


class TestSearchEndpointBenchmarks:
    """Benchmark tests for the search endpoint."""
    
    @pytest.mark.benchmark(group="search")
    def test_search_performance(self, benchmark, benchmark_client, mock_dependencies):
        """Benchmark direct search endpoint performance."""
        client, user = benchmark_client
        
        def search_query():
            response = client.get('/api/search/', {
                'q': random.choice(BENCHMARK_QUERIES[:5]),  # Use shorter queries
                'limit': 10
            })
            return response
        
        result = benchmark(search_query)
        
        assert result.status_code == 200
        stats = benchmark.stats
        # Search should be faster than full RAG pipeline
        assert stats.mean < 2.0, f"Search mean time {stats.mean:.3f}s exceeds 2s threshold"


class TestRAGComponentBenchmarks:
    """Benchmark tests for individual RAG components."""
    
    @pytest.mark.benchmark(group="vector_search")
    def test_vector_search_performance(self, benchmark, mock_dependencies):
        """Benchmark vector search component."""
        from api.ingestion.embeddings_utils import search_weaviate
        
        def vector_search():
            return search_weaviate(
                query_text=random.choice(BENCHMARK_QUERIES),
                limit=10,
                use_hybrid=True,
                alpha=0.75
            )
        
        result = benchmark(vector_search)
        
        assert isinstance(result, list)
        stats = benchmark.stats
        # Vector search should be very fast
        assert stats.mean < 1.0, f"Vector search mean time {stats.mean:.3f}s exceeds 1s threshold"
    
    @pytest.mark.benchmark(group="rag_enhancement")
    def test_rag_enhancement_performance(self, benchmark):
        """Benchmark RAG context enhancement."""
        from api.rag.enhanced_rag import enhance_rag_context
        
        # Mock search results
        mock_chunks = [
            {
                'content': f'Content chunk {i}...',
                'title': f'Document {i}',
                'doc_type': 'paper',
                'author': f'Author {i}',
                'year': '2023',
                'relevance_score': 0.9 - (i * 0.1)
            }
            for i in range(10)
        ]
        
        def enhance_context():
            return enhance_rag_context(
                query=random.choice(BENCHMARK_QUERIES),
                chunks=mock_chunks,
                max_context_chunks=5
            )
        
        result = benchmark(enhance_context)
        
        assert isinstance(result, list)
        assert len(result) <= 5
        stats = benchmark.stats
        # Context enhancement should be fast
        assert stats.mean < 0.5, f"RAG enhancement mean time {stats.mean:.3f}s exceeds 0.5s threshold"
    
    @pytest.mark.benchmark(group="reranking")
    def test_reranking_performance(self, benchmark):
        """Benchmark search result reranking."""
        from api.search.reranking import rerank_search_results
        
        # Mock search results
        mock_results = [
            {
                'content': f'Search result {i}...',
                'title': f'Result {i}',
                'relevance_score': 0.9 - (i * 0.05)
            }
            for i in range(20)
        ]
        
        def rerank_results():
            return rerank_search_results(
                query_text=random.choice(BENCHMARK_QUERIES),
                results=mock_results,
                top_k=10
            )
        
        result, timing = benchmark(rerank_results)
        
        assert isinstance(result, list)
        assert len(result) <= 10
        stats = benchmark.stats
        # Reranking should be reasonably fast
        assert stats.mean < 2.0, f"Reranking mean time {stats.mean:.3f}s exceeds 2s threshold"


class TestDatabaseBenchmarks:
    """Benchmark tests for database operations."""
    
    @pytest.mark.benchmark(group="database")
    def test_query_history_creation(self, benchmark, benchmark_client):
        """Benchmark query history record creation."""
        from api.models import QueryHistory
        client, user = benchmark_client
        
        def create_query_history():
            return QueryHistory.objects.create(
                user=user,
                query_text="Test query",
                answer="Test answer",
                confidence_score=0.85,
                processing_time=1500,
                doc_type="paper",
                sources=[{"title": "Test Source", "doc_type": "paper"}]
            )
        
        result = benchmark(create_query_history)
        
        assert result.id is not None
        stats = benchmark.stats
        # Database operations should be fast
        assert stats.mean < 0.1, f"DB creation mean time {stats.mean:.3f}s exceeds 0.1s threshold"
    
    @pytest.mark.benchmark(group="database")
    def test_query_history_retrieval(self, benchmark, benchmark_client):
        """Benchmark query history retrieval."""
        from api.models import QueryHistory
        client, user = benchmark_client
        
        # Create test data
        for i in range(100):
            QueryHistory.objects.create(
                user=user,
                query_text=f"Test query {i}",
                answer=f"Test answer {i}",
                confidence_score=0.8 + (i % 20) * 0.01,
                processing_time=1000 + (i % 500),
                doc_type="paper",
                sources=[{"title": f"Source {i}", "doc_type": "paper"}]
            )
        
        def retrieve_query_history():
            return list(QueryHistory.objects.filter(user=user).order_by('-created_at')[:10])
        
        result = benchmark(retrieve_query_history)
        
        assert len(result) == 10
        stats = benchmark.stats
        assert stats.mean < 0.05, f"DB retrieval mean time {stats.mean:.3f}s exceeds 0.05s threshold"


class TestConcurrencyBenchmarks:
    """Benchmark tests for concurrent operations."""
    
    @pytest.mark.benchmark(group="concurrent")
    def test_concurrent_simple_queries(self, benchmark, benchmark_client, mock_dependencies):
        """Benchmark system under simulated concurrent load."""
        import threading
        import queue
        
        client, user = benchmark_client
        
        def concurrent_queries():
            results = queue.Queue()
            threads = []
            
            def worker():
                try:
                    response = client.post('/api/query/', {
                        'question': random.choice(BENCHMARK_QUERIES),
                        'doc_type': 'all'
                    }, format='json')
                    results.put(response.status_code)
                except Exception as e:
                    results.put(str(e))
            
            # Start 5 concurrent requests
            for _ in range(5):
                thread = threading.Thread(target=worker)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Collect results
            statuses = []
            while not results.empty():
                statuses.append(results.get())
            
            return statuses
        
        result = benchmark(concurrent_queries)
        
        # All requests should succeed
        assert all(status == 200 for status in result if isinstance(status, int))
        stats = benchmark.stats
        # Concurrent operations should complete within reasonable time
        assert stats.mean < 10.0, f"Concurrent queries mean time {stats.mean:.3f}s exceeds 10s threshold"


class TestMemoryBenchmarks:
    """Benchmark tests for memory performance."""
    
    @pytest.mark.benchmark(group="memory")
    def test_memory_usage_query(self, benchmark, benchmark_client, mock_dependencies):
        """Benchmark memory usage during query processing."""
        import psutil
        import os
        
        client, user = benchmark_client
        process = psutil.Process(os.getpid())
        
        def memory_tracked_query():
            # Measure memory before
            memory_before = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Perform query
            response = client.post('/api/query/', {
                'question': random.choice(BENCHMARK_QUERIES),
                'doc_type': 'all'
            }, format='json')
            
            # Measure memory after
            memory_after = process.memory_info().rss / (1024 * 1024)  # MB
            
            return {
                'response': response,
                'memory_delta': memory_after - memory_before
            }
        
        result = benchmark(memory_tracked_query)
        
        assert result['response'].status_code == 200
        # Memory growth should be reasonable (less than 10MB per query)
        assert result['memory_delta'] < 10.0, f"Memory delta {result['memory_delta']:.2f}MB too high"


# Performance regression tests
class TestPerformanceRegression:
    """Tests to detect performance regressions."""
    
    @pytest.mark.benchmark(group="regression")
    def test_baseline_query_performance(self, benchmark, benchmark_client, mock_dependencies):
        """Establish baseline performance for regression testing."""
        client, user = benchmark_client
        
        def baseline_query():
            return client.post('/api/query/', {
                'question': "What is RNA?",  # Fixed query for consistency
                'doc_type': 'all'
            }, format='json')
        
        result = benchmark(baseline_query)
        
        assert result.status_code == 200
        stats = benchmark.stats
        
        # Store baseline metrics for comparison
        benchmark.extra_info['baseline_mean'] = stats.mean
        benchmark.extra_info['baseline_median'] = stats.median
        benchmark.extra_info['baseline_p95'] = getattr(stats, 'p95', stats.max)
        
        # Baseline should meet KPI
        assert stats.mean < 5.0, f"Baseline mean {stats.mean:.3f}s exceeds 5s KPI"


# Utility functions for benchmark analysis
def analyze_benchmark_results(benchmark_json_file: str):
    """
    Analyze benchmark results and generate performance report.
    
    Usage:
        pytest tests/benchmark/ --benchmark-json=results.json
        python -c "from tests.benchmark.test_benchmark_rag import analyze_benchmark_results; analyze_benchmark_results('results.json')"
    """
    import json
    
    with open(benchmark_json_file, 'r') as f:
        data = json.load(f)
    
    print("\n" + "="*60)
    print("RNA LAB NAVIGATOR - BENCHMARK ANALYSIS")
    print("="*60)
    
    benchmarks = data.get('benchmarks', [])
    
    # Group by benchmark groups
    groups = {}
    for bench in benchmarks:
        group = bench.get('group', 'unknown')
        if group not in groups:
            groups[group] = []
        groups[group].append(bench)
    
    # Analyze each group
    kpi_violations = []
    
    for group_name, group_benchmarks in groups.items():
        print(f"\n{group_name.upper()} Performance:")
        print("-" * 40)
        
        for bench in group_benchmarks:
            name = bench['name']
            stats = bench['stats']
            mean = stats['mean']
            median = stats['median']
            
            # Check KPI compliance
            kpi_threshold = 5.0
            if 'complex' in name or 'concurrent' in name:
                kpi_threshold = 8.0
            elif 'search' in name or 'vector' in name:
                kpi_threshold = 2.0
            elif 'database' in name or 'enhancement' in name:
                kpi_threshold = 0.5
            
            kpi_compliant = mean <= kpi_threshold
            if not kpi_compliant:
                kpi_violations.append({
                    'test': name,
                    'mean': mean,
                    'threshold': kpi_threshold
                })
            
            status = "✓" if kpi_compliant else "✗"
            print(f"  {status} {name}")
            print(f"    Mean: {mean:.4f}s (threshold: {kpi_threshold}s)")
            print(f"    Median: {median:.4f}s")
            print(f"    Min: {stats['min']:.4f}s")
            print(f"    Max: {stats['max']:.4f}s")
    
    # Overall assessment
    print(f"\n" + "="*60)
    print("OVERALL ASSESSMENT:")
    
    if not kpi_violations:
        print("✅ ALL BENCHMARKS PASSED")
        print("System meets all performance requirements.")
    else:
        print(f"❌ {len(kpi_violations)} BENCHMARK(S) FAILED")
        print("The following tests exceed performance thresholds:")
        for violation in kpi_violations:
            print(f"  - {violation['test']}: {violation['mean']:.4f}s > {violation['threshold']}s")
    
    print("="*60)


if __name__ == "__main__":
    print("RNA Lab Navigator Benchmark Tests")
    print("Run with: pytest tests/benchmark/ --benchmark-only")