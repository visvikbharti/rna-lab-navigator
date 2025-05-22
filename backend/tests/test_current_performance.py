#!/usr/bin/env python3
"""
Test current system performance with sample data.

This script tests the actual performance of the RNA Lab Navigator system
with the sample data to establish baseline metrics and identify bottlenecks.
"""

import os
import sys
import django
import time
import json
import statistics
import logging
from typing import Dict, List, Any
from pathlib import Path

# Setup Django
sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework.test import APIClient
from api.models import QueryHistory
from tests.performance_monitoring.performance_profiler import get_profiler

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CurrentPerformanceTester:
    """Test current system performance with real sample data."""
    
    def __init__(self):
        self.profiler = get_profiler()
        self.client = APIClient()
        self.user = None
        self.results = {
            'test_timestamp': time.time(),
            'baseline_queries': [],
            'component_performance': {},
            'system_health': {},
            'kpi_compliance': {},
            'bottlenecks': [],
            'recommendations': []
        }
        
        # Test queries that should work with sample data
        self.test_queries = [
            "What is RNA?",
            "How do you extract RNA from cells?",
            "What is PCR?",
            "Explain western blot procedure",
            "What is qPCR?",
            "What are microRNAs?",
            "How does transcription work?",
            "What is the difference between DNA and RNA?",
            "Describe gel electrophoresis",
            "What is RT-PCR?",
            "How to perform RNA sequencing?",
            "What is Northern blotting?",
            "Explain CRISPR technology",
            "What are ribosomes?",
            "How to isolate total RNA?"
        ]
    
    def setup_test_user(self):
        """Create test user for performance testing."""
        try:
            self.user = User.objects.create_user(
                username='perf_test_user',
                password='test_password',
                email='perftest@example.com'
            )
            self.client.force_authenticate(user=self.user)
            logger.info("Test user created and authenticated")
        except Exception as e:
            logger.error(f"Failed to setup test user: {str(e)}")
            raise
    
    def test_baseline_query_performance(self) -> Dict[str, Any]:
        """Test baseline query performance with sample data."""
        logger.info("Testing baseline query performance...")
        
        query_results = []
        
        for i, query in enumerate(self.test_queries):
            logger.info(f"Testing query {i+1}/{len(self.test_queries)}: {query[:50]}...")
            
            start_time = time.time()
            
            try:
                response = self.client.post('/api/query/', {
                    'question': query,
                    'doc_type': 'all'
                }, format='json')
                
                end_time = time.time()
                response_time = end_time - start_time
                
                success = response.status_code == 200
                response_data = response.json() if success else {}
                
                result = {
                    'query': query,
                    'response_time': response_time,
                    'success': success,
                    'status_code': response.status_code,
                    'confidence_score': response_data.get('confidence_score', 0),
                    'sources_count': len(response_data.get('sources', [])),
                    'answer_length': len(response_data.get('answer', ''))
                }
                
                if not success:
                    result['error'] = response_data.get('error', 'Unknown error')
                
                query_results.append(result)
                
                # Check KPI compliance
                if response_time > 5.0:
                    logger.warning(f"KPI violation: Query took {response_time:.2f}s")
                
                # Small delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Query failed: {str(e)}")
                query_results.append({
                    'query': query,
                    'response_time': 0,
                    'success': False,
                    'error': str(e)
                })
        
        self.results['baseline_queries'] = query_results
        return self._analyze_query_results(query_results)
    
    def _analyze_query_results(self, query_results: List[Dict]) -> Dict[str, Any]:
        """Analyze query results for performance metrics."""
        successful_queries = [q for q in query_results if q['success']]
        
        if not successful_queries:
            return {
                'error': 'No successful queries',
                'success_rate': 0,
                'total_queries': len(query_results)
            }
        
        response_times = [q['response_time'] for q in successful_queries]
        confidence_scores = [q['confidence_score'] for q in successful_queries if q['confidence_score'] > 0]
        
        analysis = {
            'total_queries': len(query_results),
            'successful_queries': len(successful_queries),
            'success_rate': len(successful_queries) / len(query_results),
            'response_times': {
                'mean': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'min': min(response_times),
                'max': max(response_times),
                'p95': statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
            },
            'kpi_compliance': {
                'median_under_5s': statistics.median(response_times) <= 5.0,
                'p95_under_5s': (statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)) <= 5.0,
                'success_rate_over_95': len(successful_queries) / len(query_results) >= 0.95
            }
        }
        
        if confidence_scores:
            analysis['confidence_scores'] = {
                'mean': statistics.mean(confidence_scores),
                'median': statistics.median(confidence_scores),
                'min': min(confidence_scores),
                'max': max(confidence_scores)
            }
        
        # Count KPI violations
        kpi_violations = sum(1 for t in response_times if t > 5.0)
        analysis['kpi_violations'] = {
            'count': kpi_violations,
            'rate': kpi_violations / len(response_times) if response_times else 0
        }
        
        return analysis
    
    def test_component_performance(self) -> Dict[str, Any]:
        """Test individual component performance."""
        logger.info("Testing component performance...")
        
        components = ['api.search', 'api.rag', 'api.ingestion', 'api.llm', 'django.post']
        component_perf = {}
        
        for component in components:
            perf_data = self.profiler.get_component_performance(component, hours=1)
            if perf_data and 'error' not in perf_data:
                component_perf[component] = perf_data
        
        self.results['component_performance'] = component_perf
        return component_perf
    
    def test_system_health(self) -> Dict[str, Any]:
        """Test system health metrics."""
        logger.info("Testing system health...")
        
        health_data = self.profiler.get_system_health(minutes=30)
        self.results['system_health'] = health_data
        return health_data
    
    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        logger.info("Identifying bottlenecks...")
        
        bottlenecks = self.profiler.identify_bottlenecks(hours=1)
        self.results['bottlenecks'] = bottlenecks
        return bottlenecks
    
    def test_database_performance(self) -> Dict[str, Any]:
        """Test database performance with real data."""
        logger.info("Testing database performance...")
        
        db_metrics = {}
        
        try:
            # Test query creation performance
            start_time = time.time()
            QueryHistory.objects.create(
                user=self.user,
                query_text="Performance test query",
                answer="Performance test answer",
                confidence_score=0.85,
                processing_time=1500,
                doc_type="test",
                sources=[{"title": "Test Source", "doc_type": "test"}]
            )
            db_metrics['create_time'] = time.time() - start_time
            
            # Test query retrieval performance
            start_time = time.time()
            recent_queries = list(QueryHistory.objects.filter(user=self.user).order_by('-created_at')[:10])
            db_metrics['retrieve_time'] = time.time() - start_time
            db_metrics['retrieved_count'] = len(recent_queries)
            
            # Test aggregation performance
            start_time = time.time()
            from django.db.models import Avg, Count
            stats = QueryHistory.objects.filter(user=self.user).aggregate(
                avg_confidence=Avg('confidence_score'),
                total_queries=Count('id')
            )
            db_metrics['aggregation_time'] = time.time() - start_time
            db_metrics['aggregation_results'] = stats
            
        except Exception as e:
            logger.error(f"Database performance test failed: {str(e)}")
            db_metrics['error'] = str(e)
        
        return db_metrics
    
    def test_sample_data_availability(self) -> Dict[str, Any]:
        """Test if sample data is available and accessible."""
        logger.info("Testing sample data availability...")
        
        sample_data_status = {
            'weaviate_accessible': False,
            'documents_indexed': 0,
            'vector_search_working': False,
            'search_response_time': 0
        }
        
        try:
            # Test vector search with sample data
            from api.ingestion.embeddings_utils import search_weaviate
            
            start_time = time.time()
            results = search_weaviate(
                query_text="RNA",
                limit=5,
                use_hybrid=True,
                alpha=0.75
            )
            search_time = time.time() - start_time
            
            sample_data_status.update({
                'weaviate_accessible': True,
                'documents_indexed': len(results),
                'vector_search_working': len(results) > 0,
                'search_response_time': search_time
            })
            
            logger.info(f"Found {len(results)} documents in Weaviate")
            
        except Exception as e:
            logger.error(f"Sample data test failed: {str(e)}")
            sample_data_status['error'] = str(e)
        
        return sample_data_status
    
    def generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Analyze query performance
        if 'baseline_queries' in self.results:
            query_analysis = self._analyze_query_results(self.results['baseline_queries'])
            
            if not query_analysis.get('kpi_compliance', {}).get('median_under_5s', True):
                recommendations.append({
                    'priority': 'high',
                    'category': 'latency',
                    'issue': f"Median response time {query_analysis['response_times']['median']:.2f}s exceeds 5s KPI",
                    'recommendations': [
                        'Implement query result caching',
                        'Optimize vector search parameters',
                        'Add LLM response caching',
                        'Implement parallel processing'
                    ]
                })
            
            if query_analysis.get('success_rate', 1.0) < 0.95:
                recommendations.append({
                    'priority': 'high',
                    'category': 'reliability',
                    'issue': f"Success rate {query_analysis['success_rate']:.1%} below 95%",
                    'recommendations': [
                        'Improve error handling',
                        'Add retry mechanisms',
                        'Implement circuit breakers',
                        'Check system dependencies'
                    ]
                })
        
        # Analyze system health
        if 'system_health' in self.results:
            health = self.results['system_health']
            
            if health.get('memory', {}).get('max_percent', 0) > 85:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'memory',
                    'issue': f"High memory usage: {health['memory']['max_percent']:.1f}%",
                    'recommendations': [
                        'Implement memory optimization',
                        'Review memory leaks',
                        'Optimize data structures',
                        'Consider vertical scaling'
                    ]
                })
            
            if health.get('cpu', {}).get('max_percent', 0) > 80:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'cpu',
                    'issue': f"High CPU usage: {health['cpu']['max_percent']:.1f}%",
                    'recommendations': [
                        'Implement async processing',
                        'Optimize algorithms',
                        'Add caching layers',
                        'Consider horizontal scaling'
                    ]
                })
        
        # Analyze bottlenecks
        for bottleneck in self.results.get('bottlenecks', []):
            if bottleneck['severity'] == 'high':
                recommendations.append({
                    'priority': 'high',
                    'category': 'bottleneck',
                    'issue': f"Bottleneck in {bottleneck.get('component', 'unknown')}: {bottleneck.get('type', 'unknown')}",
                    'recommendations': [
                        'Profile specific component',
                        'Implement targeted optimization',
                        'Add monitoring alerts',
                        'Consider architecture changes'
                    ]
                })
        
        self.results['recommendations'] = recommendations
        return recommendations
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Run complete performance test suite."""
        logger.info("Starting complete performance test...")
        
        try:
            # Setup
            self.setup_test_user()
            
            # Test sample data availability
            sample_data = self.test_sample_data_availability()
            self.results['sample_data'] = sample_data
            
            if not sample_data.get('vector_search_working', False):
                logger.warning("Sample data not available - some tests may fail")
            
            # Run performance tests
            query_analysis = self.test_baseline_query_performance()
            self.results['query_analysis'] = query_analysis
            
            component_perf = self.test_component_performance()
            system_health = self.test_system_health()
            bottlenecks = self.identify_bottlenecks()
            
            db_perf = self.test_database_performance()
            self.results['database_performance'] = db_perf
            
            # Generate recommendations
            recommendations = self.generate_recommendations()
            
            # Overall assessment
            self.results['overall_assessment'] = self._generate_overall_assessment()
            
            logger.info("Performance test completed successfully")
            
        except Exception as e:
            logger.error(f"Performance test failed: {str(e)}")
            self.results['error'] = str(e)
            raise
        
        return self.results
    
    def _generate_overall_assessment(self) -> Dict[str, Any]:
        """Generate overall performance assessment."""
        assessment = {
            'timestamp': time.time(),
            'kpi_compliance': False,
            'ready_for_production': False,
            'critical_issues': [],
            'optimization_needed': []
        }
        
        # Check KPI compliance
        if 'query_analysis' in self.results:
            kpi = self.results['query_analysis'].get('kpi_compliance', {})
            assessment['kpi_compliance'] = (
                kpi.get('median_under_5s', False) and
                kpi.get('success_rate_over_95', False)
            )
        
        # Check for critical issues
        high_priority_recs = [r for r in self.results.get('recommendations', []) if r.get('priority') == 'high']
        assessment['critical_issues'] = [r['issue'] for r in high_priority_recs]
        
        # Production readiness
        assessment['ready_for_production'] = (
            assessment['kpi_compliance'] and
            len(assessment['critical_issues']) == 0 and
            self.results.get('sample_data', {}).get('vector_search_working', False)
        )
        
        return assessment
    
    def save_results(self, filename: str = None):
        """Save test results to file."""
        if not filename:
            timestamp = int(time.time())
            filename = f"performance_test_results_{timestamp}.json"
        
        results_dir = Path(__file__).parent / "test_results"
        results_dir.mkdir(exist_ok=True)
        
        filepath = results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {filepath}")
        return filepath
    
    def print_summary(self):
        """Print a summary of test results."""
        print("\n" + "="*80)
        print("RNA LAB NAVIGATOR - PERFORMANCE TEST SUMMARY")
        print("="*80)
        
        # Overall assessment
        assessment = self.results.get('overall_assessment', {})
        kpi_status = "✅ PASSED" if assessment.get('kpi_compliance') else "❌ FAILED"
        prod_status = "✅ READY" if assessment.get('ready_for_production') else "❌ NOT READY"
        
        print(f"KPI Compliance: {kpi_status}")
        print(f"Production Ready: {prod_status}")
        
        # Query performance
        if 'query_analysis' in self.results:
            qa = self.results['query_analysis']
            print(f"\nQuery Performance:")
            print(f"  Success Rate: {qa.get('success_rate', 0):.1%}")
            print(f"  Median Response Time: {qa.get('response_times', {}).get('median', 0):.2f}s")
            print(f"  P95 Response Time: {qa.get('response_times', {}).get('p95', 0):.2f}s")
            print(f"  KPI Violations: {qa.get('kpi_violations', {}).get('count', 0)}")
        
        # Sample data status
        if 'sample_data' in self.results:
            sd = self.results['sample_data']
            print(f"\nSample Data:")
            print(f"  Weaviate Accessible: {'✅' if sd.get('weaviate_accessible') else '❌'}")
            print(f"  Documents Indexed: {sd.get('documents_indexed', 0)}")
            print(f"  Vector Search Working: {'✅' if sd.get('vector_search_working') else '❌'}")
        
        # Critical issues
        critical_issues = assessment.get('critical_issues', [])
        if critical_issues:
            print(f"\nCritical Issues:")
            for issue in critical_issues:
                print(f"  - {issue}")
        
        # Recommendations
        recommendations = self.results.get('recommendations', [])
        high_priority = [r for r in recommendations if r.get('priority') == 'high']
        if high_priority:
            print(f"\nHigh Priority Recommendations:")
            for rec in high_priority[:3]:  # Show top 3
                print(f"  - {rec.get('issue', 'Unknown issue')}")
        
        print("="*80)


def main():
    """Main function to run performance tests."""
    tester = CurrentPerformanceTester()
    
    try:
        # Run complete test
        results = tester.run_complete_test()
        
        # Print summary
        tester.print_summary()
        
        # Save results
        filepath = tester.save_results()
        print(f"\nDetailed results saved to: {filepath}")
        
        # Exit with appropriate code
        assessment = results.get('overall_assessment', {})
        if assessment.get('ready_for_production', False):
            print("\n🎉 System is ready for production!")
            sys.exit(0)
        else:
            print("\n⚠️  System needs optimization before production.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Performance test failed: {str(e)}")
        print(f"\n💥 Performance test failed: {str(e)}")
        sys.exit(2)


if __name__ == "__main__":
    main()