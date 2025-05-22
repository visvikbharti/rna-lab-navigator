"""
Performance tests for the RNA Lab Navigator RAG pipeline.
Tests response time, throughput, and resource usage under load to ensure ≤5s latency.

These tests validate the KPI requirements:
- Median end-to-end latency ≤ 5s
- System can handle multiple concurrent users
- Memory usage remains stable under load
- API endpoints meet performance requirements

Run with: pytest tests/test_performance/test_rag_performance.py -v -s --benchmark-only
"""

import pytest
import time
import threading
import statistics
from unittest.mock import patch
import psutil
import os
import json
import logging
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.test import override_settings
from django.core.cache import cache

from api.ingestion.embeddings_utils import search_weaviate
from api.rag.enhanced_rag import enhance_rag_context
from api.search.services import SearchService
from api.models import QueryHistory

# Setup logger for performance testing
logger = logging.getLogger(__name__)


@pytest.mark.django_db
@pytest.mark.slow
def test_query_response_time(authenticated_client, mock_openai, mock_weaviate):
    """Test response time of the query endpoint under normal conditions."""
    client, _ = authenticated_client
    url = reverse('query')
    
    query_data = {
        "question": "What is RNA?",
        "doc_type": "all"
    }
    
    # Warm-up request
    client.post(url, query_data, format='json')
    
    # Measure response time for multiple requests
    response_times = []
    num_requests = 10
    
    for _ in range(num_requests):
        start_time = time.time()
        response = client.post(url, query_data, format='json')
        end_time = time.time()
        
        assert response.status_code == 200
        response_times.append(end_time - start_time)
    
    # Calculate metrics
    avg_response_time = statistics.mean(response_times)
    p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
    
    # Log results
    print(f"Average response time: {avg_response_time:.4f}s")
    print(f"P95 response time: {p95_response_time:.4f}s")
    
    # Assert response time meets the ≤5s KPI requirement
    assert avg_response_time < 5.0, f"Average response time {avg_response_time:.4f}s exceeds 5s KPI requirement"
    assert p95_response_time < 5.0, f"P95 response time {p95_response_time:.4f}s exceeds 5s KPI requirement"
    
    # Additional detailed logging for performance analysis
    logger.info(f"Response time distribution: min={min(response_times):.4f}s, "
                f"median={statistics.median(response_times):.4f}s, "
                f"max={max(response_times):.4f}s")


@pytest.mark.django_db
@pytest.mark.slow
def test_query_throughput():
    """Test throughput of the query endpoint under load."""
    # Create multiple clients
    num_clients = 10
    clients = []
    users = []
    
    for i in range(num_clients):
        client = APIClient()
        user = User.objects.create_user(
            username=f"test_user_{i}", 
            password="test_password",
            email=f"test{i}@example.com"
        )
        client.force_authenticate(user=user)
        clients.append(client)
        users.append(user)
    
    url = reverse('query')
    query_data = {
        "question": "What is RNA?",
        "doc_type": "all"
    }
    
    # Define worker function for each thread
    def worker(client, results, user_id):
        start_time = time.time()
        
        try:
            response = client.post(url, query_data, format='json')
            success = response.status_code == 200
        except Exception:
            success = False
        
        end_time = time.time()
        results[user_id] = {
            'success': success,
            'time': end_time - start_time
        }
    
    # Run concurrent requests
    threads = []
    results = {}
    
    start_time = time.time()
    
    for i in range(num_clients):
        thread = threading.Thread(target=worker, args=(clients[i], results, i))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Calculate metrics
    success_count = sum(1 for r in results.values() if r['success'])
    success_rate = success_count / num_clients
    throughput = success_count / total_time
    
    # Calculate response time statistics for successful requests
    response_times = [r['time'] for r in results.values() if r['success']]
    if response_times:
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
    else:
        avg_response_time = float('inf')
        max_response_time = float('inf')
    
    # Log results
    print(f"Success rate: {success_rate:.2%}")
    print(f"Throughput: {throughput:.2f} requests/second")
    print(f"Average response time: {avg_response_time:.4f}s")
    print(f"Max response time: {max_response_time:.4f}s")
    
    # Assert metrics are within acceptable limits
    assert success_rate >= 0.9, f"Success rate {success_rate:.2%} is below 90%"
    assert throughput >= 0.5, f"Throughput {throughput:.2f} req/s is below 0.5 req/s threshold"
    assert avg_response_time < 10.0, f"Average response time {avg_response_time:.4f}s exceeds 10s threshold"


@pytest.mark.django_db
@pytest.mark.slow
def test_memory_usage():
    """Test memory usage during RAG query processing."""
    # Setup
    client = APIClient()
    user = User.objects.create_user(
        username="memory_test_user", 
        password="test_password",
        email="memory@example.com"
    )
    client.force_authenticate(user=user)
    
    url = reverse('query')
    query_data = {
        "question": "What is RNA?",
        "doc_type": "all"
    }
    
    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    
    # Run multiple queries
    num_queries = 5
    memory_usage = [initial_memory]
    
    for i in range(num_queries):
        # Run query
        response = client.post(url, query_data, format='json')
        assert response.status_code == 200
        
        # Measure memory after query
        current_memory = process.memory_info().rss / (1024 * 1024)
        memory_usage.append(current_memory)
    
    # Calculate memory growth
    memory_growth = memory_usage[-1] - memory_usage[0]
    avg_growth_per_query = memory_growth / num_queries
    
    # Log results
    print(f"Initial memory usage: {initial_memory:.2f} MB")
    print(f"Final memory usage: {memory_usage[-1]:.2f} MB")
    print(f"Total memory growth: {memory_growth:.2f} MB")
    print(f"Average growth per query: {avg_growth_per_query:.2f} MB")
    
    # Memory growth should be reasonable
    # This is a simplified test - in a real environment, you'd want to monitor 
    # for memory leaks over longer periods
    assert avg_growth_per_query < 5.0, f"Average memory growth per query {avg_growth_per_query:.2f} MB exceeds 5 MB threshold"


@pytest.mark.django_db
@pytest.mark.slow
def test_long_query_performance():
    """Test performance with long, complex queries."""
    client = APIClient()
    user = User.objects.create_user(
        username="complex_query_user", 
        password="test_password",
        email="complex@example.com"
    )
    client.force_authenticate(user=user)
    
    url = reverse('query')
    
    # A long, complex query
    long_query = {
        "question": """
        What is the relationship between RNA structure and function, particularly 
        focusing on the role of tertiary interactions in determining the catalytic 
        activities of ribozymes? Additionally, how do post-transcriptional modifications 
        affect RNA stability and recognition by proteins? Please provide specific 
        examples from recent research papers that demonstrate these structure-function 
        relationships in eukaryotic systems.
        """,
        "doc_type": "all"
    }
    
    # Measure response time
    start_time = time.time()
    response = client.post(url, long_query, format='json')
    end_time = time.time()
    
    assert response.status_code == 200
    
    response_time = end_time - start_time
    print(f"Long query response time: {response_time:.4f}s")
    
    # Even complex queries should complete within a reasonable time
    assert response_time < 15.0, f"Long query response time {response_time:.4f}s exceeds 15s threshold"


# New comprehensive performance tests

class PerformanceMetrics:
    """Helper class to track and analyze performance metrics."""
    
    def __init__(self):
        self.response_times = []
        self.memory_usage = []
        self.cpu_usage = []
        self.error_count = 0
        self.success_count = 0
    
    def add_measurement(self, response_time: float, memory_mb: float = None, 
                       cpu_percent: float = None, success: bool = True):
        """Add a performance measurement."""
        self.response_times.append(response_time)
        if memory_mb is not None:
            self.memory_usage.append(memory_mb)
        if cpu_percent is not None:
            self.cpu_usage.append(cpu_percent)
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        if not self.response_times:
            return {}
        
        stats = {
            'response_time': {
                'min': min(self.response_times),
                'max': max(self.response_times),
                'mean': statistics.mean(self.response_times),
                'median': statistics.median(self.response_times),
                'p95': statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else max(self.response_times),
                'p99': statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else max(self.response_times)
            },
            'success_rate': self.success_count / (self.success_count + self.error_count) if (self.success_count + self.error_count) > 0 else 0,
            'total_requests': self.success_count + self.error_count,
            'throughput': self.success_count / sum(self.response_times) if self.response_times else 0
        }
        
        if self.memory_usage:
            stats['memory'] = {
                'min': min(self.memory_usage),
                'max': max(self.memory_usage),
                'mean': statistics.mean(self.memory_usage),
                'growth': max(self.memory_usage) - min(self.memory_usage)
            }
        
        if self.cpu_usage:
            stats['cpu'] = {
                'min': min(self.cpu_usage),
                'max': max(self.cpu_usage),
                'mean': statistics.mean(self.cpu_usage)
            }
        
        return stats


@pytest.mark.django_db
@pytest.mark.slow
def test_rag_pipeline_end_to_end_performance():
    """Test end-to-end RAG pipeline performance to ensure ≤5s latency KPI."""
    metrics = PerformanceMetrics()
    
    # Test various query types to simulate real usage
    test_queries = [
        "What is RNA?",
        "How do you extract RNA from cells?",
        "What is the difference between DNA and RNA?",
        "Explain PCR protocol steps",
        "What are the latest advances in CRISPR technology?",
        "How to perform western blot analysis?",
        "What is qPCR and how does it work?",
        "Describe RNA sequencing workflows"
    ]
    
    client = APIClient()
    user = User.objects.create_user(
        username="perf_test_user", 
        password="test_password",
        email="perf@example.com"
    )
    client.force_authenticate(user=user)
    url = reverse('query')
    
    process = psutil.Process(os.getpid())
    
    for query in test_queries:
        # Measure system resources before query
        memory_before = process.memory_info().rss / (1024 * 1024)
        cpu_before = process.cpu_percent()
        
        start_time = time.time()
        
        try:
            response = client.post(url, {
                "question": query,
                "doc_type": "all"
            }, format='json')
            success = response.status_code == 200
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            success = False
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Measure system resources after query
        memory_after = process.memory_info().rss / (1024 * 1024)
        cpu_after = process.cpu_percent()
        
        metrics.add_measurement(
            response_time=response_time,
            memory_mb=memory_after,
            cpu_percent=cpu_after,
            success=success
        )
        
        # Small delay between requests
        time.sleep(0.1)
    
    stats = metrics.get_stats()
    
    # Log comprehensive performance results
    print("\n=== RAG Pipeline Performance Results ===")
    print(f"Total requests: {stats['total_requests']}")
    print(f"Success rate: {stats['success_rate']:.2%}")
    print(f"Response times:")
    print(f"  - Mean: {stats['response_time']['mean']:.4f}s")
    print(f"  - Median: {stats['response_time']['median']:.4f}s")
    print(f"  - P95: {stats['response_time']['p95']:.4f}s")
    print(f"  - P99: {stats['response_time']['p99']:.4f}s")
    print(f"  - Min: {stats['response_time']['min']:.4f}s")
    print(f"  - Max: {stats['response_time']['max']:.4f}s")
    
    if 'memory' in stats:
        print(f"Memory usage:")
        print(f"  - Mean: {stats['memory']['mean']:.2f} MB")
        print(f"  - Growth: {stats['memory']['growth']:.2f} MB")
    
    # Assert KPI requirements
    assert stats['success_rate'] >= 0.95, f"Success rate {stats['success_rate']:.2%} below 95%"
    assert stats['response_time']['median'] <= 5.0, f"Median response time {stats['response_time']['median']:.4f}s exceeds 5s KPI"
    assert stats['response_time']['p95'] <= 5.0, f"P95 response time {stats['response_time']['p95']:.4f}s exceeds 5s KPI"


@pytest.mark.django_db
@pytest.mark.slow
def test_concurrent_load_performance():
    """Test system performance under concurrent load."""
    num_concurrent_users = 20
    queries_per_user = 5
    
    # Create test users
    users = []
    clients = []
    for i in range(num_concurrent_users):
        user = User.objects.create_user(
            username=f"load_test_user_{i}",
            password="test_password",
            email=f"load{i}@example.com"
        )
        client = APIClient()
        client.force_authenticate(user=user)
        users.append(user)
        clients.append(client)
    
    url = reverse('query')
    test_queries = [
        "What is RNA structure?",
        "How to perform RNA extraction?",
        "What are microRNAs?",
        "Explain RNA interference mechanism",
        "What is RNA sequencing?"
    ]
    
    def user_session(client, user_id, results):
        """Simulate a user session with multiple queries."""
        session_metrics = PerformanceMetrics()
        
        for i in range(queries_per_user):
            query = test_queries[i % len(test_queries)]
            
            start_time = time.time()
            try:
                response = client.post(url, {
                    "question": query,
                    "doc_type": "all"
                }, format='json')
                success = response.status_code == 200
            except Exception:
                success = False
            
            end_time = time.time()
            response_time = end_time - start_time
            
            session_metrics.add_measurement(response_time, success=success)
            
            # Small delay between queries in session
            time.sleep(0.05)
        
        results[user_id] = session_metrics.get_stats()
    
    # Execute concurrent load test
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
        results = {}
        futures = []
        
        for i in range(num_concurrent_users):
            future = executor.submit(user_session, clients[i], i, results)
            futures.append(future)
        
        # Wait for all sessions to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"User session failed: {str(e)}")
    
    total_time = time.time() - start_time
    
    # Aggregate results
    all_response_times = []
    total_requests = 0
    successful_requests = 0
    
    for user_stats in results.values():
        if 'response_time' in user_stats:
            # This is a simplified aggregation - in reality you'd want more detailed metrics
            total_requests += user_stats['total_requests']
            successful_requests += int(user_stats['total_requests'] * user_stats['success_rate'])
    
    overall_success_rate = successful_requests / total_requests if total_requests > 0 else 0
    throughput = successful_requests / total_time
    
    # Log results
    print(f"\n=== Concurrent Load Test Results ===")
    print(f"Concurrent users: {num_concurrent_users}")
    print(f"Queries per user: {queries_per_user}")
    print(f"Total requests: {total_requests}")
    print(f"Successful requests: {successful_requests}")
    print(f"Overall success rate: {overall_success_rate:.2%}")
    print(f"Total test time: {total_time:.2f}s")
    print(f"Throughput: {throughput:.2f} req/s")
    
    # Assert performance requirements
    assert overall_success_rate >= 0.90, f"Success rate {overall_success_rate:.2%} below 90% under load"
    assert throughput >= 1.0, f"Throughput {throughput:.2f} req/s too low under load"


@pytest.mark.django_db 
@pytest.mark.slow
def test_vector_search_performance():
    """Test vector search component performance specifically."""
    
    # Test queries of varying complexity
    test_queries = [
        "RNA",  # Simple
        "RNA structure function",  # Medium
        "RNA polymerase transcription elongation mechanism eukaryotic cells"  # Complex
    ]
    
    metrics = PerformanceMetrics()
    
    for query in test_queries:
        start_time = time.time()
        
        try:
            # Test direct vector search (bypassing full RAG pipeline)
            results = search_weaviate(
                query_text=query,
                limit=10,
                use_hybrid=True,
                alpha=0.75
            )
            success = len(results) > 0
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            success = False
            results = []
        
        end_time = time.time()
        response_time = end_time - start_time
        
        metrics.add_measurement(response_time, success=success)
        
        print(f"Query: '{query}' -> {len(results)} results in {response_time:.4f}s")
    
    stats = metrics.get_stats()
    
    # Vector search should be very fast (sub-second)
    assert stats['response_time']['mean'] < 1.0, f"Vector search mean time {stats['response_time']['mean']:.4f}s too slow"
    assert stats['response_time']['p95'] < 2.0, f"Vector search P95 time {stats['response_time']['p95']:.4f}s too slow"
    assert stats['success_rate'] >= 0.95, f"Vector search success rate {stats['success_rate']:.2%} too low"


@pytest.mark.django_db
@pytest.mark.slow  
def test_rag_context_enhancement_performance():
    """Test RAG context enhancement performance."""
    
    # Mock some search results
    mock_chunks = [
        {
            'content': 'RNA is a nucleic acid...',
            'title': 'RNA Biology Basics',
            'doc_type': 'paper',
            'author': 'Smith et al',
            'year': '2023',
            'relevance_score': 0.95
        },
        {
            'content': 'Transcription involves...',
            'title': 'Gene Expression',
            'doc_type': 'paper', 
            'author': 'Jones et al',
            'year': '2022',
            'relevance_score': 0.88
        },
        {
            'content': 'PCR amplification...',
            'title': 'Molecular Techniques',
            'doc_type': 'protocol',
            'author': 'Lab Manual',
            'year': '2023',
            'relevance_score': 0.82
        }
    ] * 10  # Simulate larger result set
    
    query = "What is RNA and how is it transcribed?"
    
    metrics = PerformanceMetrics()
    
    # Test multiple runs
    for _ in range(10):
        start_time = time.time()
        
        try:
            enhanced_chunks = enhance_rag_context(
                query=query,
                chunks=mock_chunks,
                max_context_chunks=5
            )
            success = len(enhanced_chunks) > 0
        except Exception as e:
            logger.error(f"RAG enhancement failed: {str(e)}")
            success = False
        
        end_time = time.time()
        response_time = end_time - start_time
        
        metrics.add_measurement(response_time, success=success)
    
    stats = metrics.get_stats()
    
    print(f"RAG Enhancement Performance:")
    print(f"  Mean time: {stats['response_time']['mean']:.4f}s")
    print(f"  P95 time: {stats['response_time']['p95']:.4f}s")
    print(f"  Success rate: {stats['success_rate']:.2%}")
    
    # RAG enhancement should be fast
    assert stats['response_time']['mean'] < 0.5, f"RAG enhancement mean time {stats['response_time']['mean']:.4f}s too slow"
    assert stats['success_rate'] >= 0.95, f"RAG enhancement success rate {stats['success_rate']:.2%} too low"


@pytest.mark.django_db
@pytest.mark.slow
def test_database_query_performance():
    """Test database query performance for analytics and history."""
    
    # Create some test data
    client = APIClient()
    user = User.objects.create_user(
        username="db_test_user",
        password="test_password", 
        email="db@example.com"
    )
    client.force_authenticate(user=user)
    
    # Create query history entries
    for i in range(100):
        QueryHistory.objects.create(
            user=user,
            query_text=f"Test query {i}",
            answer=f"Test answer {i}",
            confidence_score=0.8 + (i % 20) * 0.01,
            processing_time=100 + (i % 50),
            doc_type="paper",
            sources=[{"title": f"Source {i}", "doc_type": "paper"}]
        )
    
    metrics = PerformanceMetrics()
    
    # Test various database queries
    db_operations = [
        lambda: QueryHistory.objects.filter(user=user).count(),
        lambda: QueryHistory.objects.filter(confidence_score__gte=0.8).count(),
        lambda: list(QueryHistory.objects.filter(user=user).order_by('-created_at')[:10]),
        lambda: QueryHistory.objects.filter(user=user).values('query_text').distinct().count(),
    ]
    
    for operation in db_operations:
        start_time = time.time()
        
        try:
            result = operation()
            success = True
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            success = False
        
        end_time = time.time()
        response_time = end_time - start_time
        
        metrics.add_measurement(response_time, success=success)
    
    stats = metrics.get_stats()
    
    print(f"Database Query Performance:")
    print(f"  Mean time: {stats['response_time']['mean']:.4f}s")
    print(f"  Max time: {stats['response_time']['max']:.4f}s")
    print(f"  Success rate: {stats['success_rate']:.2%}")
    
    # Database queries should be very fast
    assert stats['response_time']['mean'] < 0.1, f"Database query mean time {stats['response_time']['mean']:.4f}s too slow"
    assert stats['success_rate'] >= 0.95, f"Database query success rate {stats['success_rate']:.2%} too low"


@pytest.mark.django_db
@pytest.mark.slow
def test_cache_performance():
    """Test caching performance and effectiveness."""
    
    client = APIClient()
    user = User.objects.create_user(
        username="cache_test_user",
        password="test_password",
        email="cache@example.com"
    )
    client.force_authenticate(user=user)
    
    url = reverse('query')
    query_data = {
        "question": "What is RNA?",
        "doc_type": "all"
    }
    
    # Clear cache
    cache.clear()
    
    # First request (cache miss)
    start_time = time.time()
    response1 = client.post(url, query_data, format='json')
    cache_miss_time = time.time() - start_time
    
    # Second request (should be faster if cached)
    start_time = time.time()
    response2 = client.post(url, query_data, format='json')
    cache_hit_time = time.time() - start_time
    
    print(f"Cache Performance:")
    print(f"  Cache miss time: {cache_miss_time:.4f}s")
    print(f"  Cache hit time: {cache_hit_time:.4f}s")
    print(f"  Speed improvement: {(cache_miss_time - cache_hit_time) / cache_miss_time * 100:.1f}%")
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Cache hit should be faster than cache miss (if caching is implemented)
    # Note: This test assumes caching is implemented in the system
    if cache_hit_time < cache_miss_time:
        improvement = (cache_miss_time - cache_hit_time) / cache_miss_time
        assert improvement > 0.1, f"Cache improvement {improvement:.2%} too small"