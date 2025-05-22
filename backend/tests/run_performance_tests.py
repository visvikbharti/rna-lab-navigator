#!/usr/bin/env python3
"""
Comprehensive performance testing runner for RNA Lab Navigator.

This script orchestrates various performance tests, load tests, and benchmarks
to provide a complete performance assessment of the system.

Usage:
    python tests/run_performance_tests.py --all
    python tests/run_performance_tests.py --quick
    python tests/run_performance_tests.py --load-test --users 20 --duration 300
    python tests/run_performance_tests.py --benchmark-only
"""

import argparse
import subprocess
import sys
import json
import time
import logging
import os
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceTestRunner:
    """Main class for running performance tests."""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.results_dir = self.base_dir / "test_results" / "performance"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'unit_tests': {},
            'load_tests': {},
            'benchmarks': {},
            'recommendations': []
        }
    
    def run_unit_performance_tests(self) -> bool:
        """Run pytest performance tests."""
        logger.info("Running unit performance tests...")
        
        try:
            # Run the performance tests
            cmd = [
                'python', '-m', 'pytest',
                'tests/test_performance/',
                '-v',
                '--tb=short',
                '--json-report',
                f'--json-report-file={self.results_dir}/unit_performance.json'
            ]
            
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True)
            
            # Parse results
            if result.returncode == 0:
                logger.info("✅ Unit performance tests passed")
                self.test_results['unit_tests']['status'] = 'passed'
            else:
                logger.warning("⚠️  Some unit performance tests failed")
                self.test_results['unit_tests']['status'] = 'failed'
                self.test_results['unit_tests']['output'] = result.stdout
                self.test_results['unit_tests']['errors'] = result.stderr
            
            # Load detailed results if available
            unit_results_file = self.results_dir / "unit_performance.json"
            if unit_results_file.exists():
                with open(unit_results_file, 'r') as f:
                    unit_data = json.load(f)
                    self.test_results['unit_tests']['details'] = unit_data
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to run unit performance tests: {str(e)}")
            self.test_results['unit_tests']['status'] = 'error'
            self.test_results['unit_tests']['error'] = str(e)
            return False
    
    def run_benchmark_tests(self) -> bool:
        """Run pytest benchmark tests."""
        logger.info("Running benchmark tests...")
        
        try:
            benchmark_file = self.results_dir / "benchmarks.json"
            
            cmd = [
                'python', '-m', 'pytest',
                'tests/benchmark/',
                '--benchmark-only',
                '--benchmark-sort=mean',
                f'--benchmark-json={benchmark_file}',
                '-v'
            ]
            
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Benchmark tests completed successfully")
                self.test_results['benchmarks']['status'] = 'passed'
            else:
                logger.warning("⚠️  Some benchmark tests failed")
                self.test_results['benchmarks']['status'] = 'failed'
                self.test_results['benchmarks']['output'] = result.stdout
                self.test_results['benchmarks']['errors'] = result.stderr
            
            # Load benchmark results
            if benchmark_file.exists():
                with open(benchmark_file, 'r') as f:
                    benchmark_data = json.load(f)
                    self.test_results['benchmarks']['details'] = benchmark_data
                    
                    # Analyze benchmark results
                    self._analyze_benchmarks(benchmark_data)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to run benchmark tests: {str(e)}")
            self.test_results['benchmarks']['status'] = 'error'
            self.test_results['benchmarks']['error'] = str(e)
            return False
    
    def run_load_test(self, users: int = 20, duration: int = 180, host: str = "http://localhost:8000") -> bool:
        """Run Locust load test."""
        logger.info(f"Running load test: {users} users, {duration}s duration")
        
        try:
            # Check if locust is available
            result = subprocess.run(['locust', '--version'], capture_output=True)
            if result.returncode != 0:
                logger.error("Locust not found. Install with: pip install locust")
                return False
            
            # Run locust load test
            locust_file = self.base_dir / "tests" / "load_testing" / "locustfile.py"
            results_file = self.results_dir / "load_test_results.json"
            
            cmd = [
                'locust',
                '-f', str(locust_file),
                '--host', host,
                '--users', str(users),
                '--spawn-rate', str(max(1, users // 10)),
                '--run-time', f"{duration}s",
                '--headless',
                '--csv', str(self.results_dir / "load_test"),
                '--html', str(self.results_dir / "load_test_report.html")
            ]
            
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Load test completed successfully")
                self.test_results['load_tests']['status'] = 'passed'
            else:
                logger.warning("⚠️  Load test encountered issues")
                self.test_results['load_tests']['status'] = 'failed'
            
            self.test_results['load_tests']['output'] = result.stdout
            self.test_results['load_tests']['errors'] = result.stderr
            self.test_results['load_tests']['config'] = {
                'users': users,
                'duration': duration,
                'host': host
            }
            
            # Parse CSV results if available
            self._parse_load_test_results()
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to run load test: {str(e)}")
            self.test_results['load_tests']['status'] = 'error'
            self.test_results['load_tests']['error'] = str(e)
            return False
    
    def run_stress_test(self, users: int = 50, duration: int = 300, host: str = "http://localhost:8000") -> bool:
        """Run custom async stress test."""
        logger.info(f"Running stress test: {users} users, {duration}s duration")
        
        try:
            stress_script = self.base_dir / "tests" / "load_testing" / "stress_test.py"
            results_file = self.results_dir / "stress_test_results.json"
            
            cmd = [
                'python', str(stress_script),
                '--host', host,
                '--users', str(users),
                '--duration', str(duration),
                '--output', str(results_file)
            ]
            
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Stress test passed")
                self.test_results['load_tests']['stress_status'] = 'passed'
            else:
                logger.warning("⚠️  Stress test failed or found issues")
                self.test_results['load_tests']['stress_status'] = 'failed'
            
            self.test_results['load_tests']['stress_output'] = result.stdout
            self.test_results['load_tests']['stress_errors'] = result.stderr
            
            # Load stress test results
            if results_file.exists():
                with open(results_file, 'r') as f:
                    stress_data = json.load(f)
                    self.test_results['load_tests']['stress_details'] = stress_data
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to run stress test: {str(e)}")
            self.test_results['load_tests']['stress_status'] = 'error'
            self.test_results['load_tests']['stress_error'] = str(e)
            return False
    
    def _parse_load_test_results(self):
        """Parse Locust CSV results."""
        try:
            stats_file = self.results_dir / "load_test_stats.csv"
            if not stats_file.exists():
                return
            
            import csv
            with open(stats_file, 'r') as f:
                reader = csv.DictReader(f)
                stats = list(reader)
            
            # Extract key metrics
            if stats:
                total_row = next((row for row in stats if row['Name'] == 'Aggregated'), stats[-1])
                
                self.test_results['load_tests']['metrics'] = {
                    'total_requests': int(total_row.get('Request Count', 0)),
                    'failure_count': int(total_row.get('Failure Count', 0)),
                    'median_response_time': float(total_row.get('Median Response Time', 0)),
                    'average_response_time': float(total_row.get('Average Response Time', 0)),
                    'min_response_time': float(total_row.get('Min Response Time', 0)),
                    'max_response_time': float(total_row.get('Max Response Time', 0)),
                    'requests_per_second': float(total_row.get('Requests/s', 0))
                }
                
        except Exception as e:
            logger.warning(f"Could not parse load test results: {str(e)}")
    
    def _analyze_benchmarks(self, benchmark_data: Dict):
        """Analyze benchmark results for KPI compliance."""
        benchmarks = benchmark_data.get('benchmarks', [])
        
        kpi_violations = []
        performance_summary = {
            'total_tests': len(benchmarks),
            'passed': 0,
            'failed': 0,
            'kpi_compliant': 0
        }
        
        for bench in benchmarks:
            name = bench['name']
            stats = bench['stats']
            mean_time = stats['mean']
            
            # Determine KPI threshold based on test type
            kpi_threshold = 5.0  # Default 5s KPI
            if 'complex' in name.lower() or 'concurrent' in name.lower():
                kpi_threshold = 8.0
            elif 'search' in name.lower() or 'vector' in name.lower():
                kpi_threshold = 2.0
            elif 'database' in name.lower() or 'enhancement' in name.lower():
                kpi_threshold = 0.5
            
            kpi_compliant = mean_time <= kpi_threshold
            
            if kpi_compliant:
                performance_summary['kpi_compliant'] += 1
                performance_summary['passed'] += 1
            else:
                performance_summary['failed'] += 1
                kpi_violations.append({
                    'test': name,
                    'mean_time': mean_time,
                    'threshold': kpi_threshold,
                    'violation_percent': ((mean_time - kpi_threshold) / kpi_threshold) * 100
                })
        
        self.test_results['benchmarks']['kpi_violations'] = kpi_violations
        self.test_results['benchmarks']['performance_summary'] = performance_summary
    
    def generate_recommendations(self):
        """Generate optimization recommendations based on test results."""
        recommendations = []
        
        # Analyze benchmark results
        if 'kpi_violations' in self.test_results['benchmarks']:
            violations = self.test_results['benchmarks']['kpi_violations']
            
            for violation in violations:
                test_name = violation['test']
                violation_percent = violation['violation_percent']
                
                if 'query' in test_name.lower():
                    if violation_percent > 50:
                        recommendations.append({
                            'priority': 'high',
                            'category': 'query_optimization',
                            'description': f"Query performance severely degraded: {test_name}",
                            'suggestions': [
                                'Implement query result caching',
                                'Optimize vector search parameters',
                                'Review LLM response caching',
                                'Consider query preprocessing optimization'
                            ]
                        })
                    else:
                        recommendations.append({
                            'priority': 'medium',
                            'category': 'query_optimization',
                            'description': f"Query performance needs improvement: {test_name}",
                            'suggestions': [
                                'Fine-tune search parameters',
                                'Implement partial result caching',
                                'Optimize database queries'
                            ]
                        })
                
                elif 'search' in test_name.lower():
                    recommendations.append({
                        'priority': 'high',
                        'category': 'search_optimization',
                        'description': f"Search component performance issue: {test_name}",
                        'suggestions': [
                            'Optimize vector index configuration',
                            'Review search algorithm parameters',
                            'Implement search result caching',
                            'Consider search index warming'
                        ]
                    })
                
                elif 'database' in test_name.lower():
                    recommendations.append({
                        'priority': 'high',
                        'category': 'database_optimization',
                        'description': f"Database performance issue: {test_name}",
                        'suggestions': [
                            'Add database indexes',
                            'Optimize slow queries',
                            'Implement connection pooling',
                            'Consider query result caching'
                        ]
                    })
        
        # Analyze load test results
        if 'metrics' in self.test_results['load_tests']:
            metrics = self.test_results['load_tests']['metrics']
            
            if metrics.get('median_response_time', 0) > 5000:  # 5 seconds in ms
                recommendations.append({
                    'priority': 'high',
                    'category': 'load_performance',
                    'description': 'System does not meet KPI under load',
                    'suggestions': [
                        'Implement horizontal scaling',
                        'Add load balancing',
                        'Optimize resource allocation',
                        'Implement async processing'
                    ]
                })
            
            failure_rate = metrics.get('failure_count', 0) / max(metrics.get('total_requests', 1), 1)
            if failure_rate > 0.05:  # 5% failure rate
                recommendations.append({
                    'priority': 'high',
                    'category': 'reliability',
                    'description': f'High failure rate under load: {failure_rate:.1%}',
                    'suggestions': [
                        'Implement circuit breakers',
                        'Add retry mechanisms',
                        'Improve error handling',
                        'Increase resource limits'
                    ]
                })
        
        # Add general recommendations if no specific issues found
        if not recommendations:
            recommendations.append({
                'priority': 'low',
                'category': 'optimization',
                'description': 'System performance is acceptable but can be optimized',
                'suggestions': [
                    'Implement comprehensive caching strategy',
                    'Monitor performance trends over time',
                    'Consider proactive scaling policies',
                    'Optimize resource utilization'
                ]
            })
        
        self.test_results['recommendations'] = recommendations
    
    def generate_report(self) -> str:
        """Generate comprehensive performance test report."""
        # Generate recommendations
        self.generate_recommendations()
        
        # Calculate overall status
        all_passed = (
            self.test_results['unit_tests'].get('status') == 'passed' and
            self.test_results['benchmarks'].get('status') == 'passed' and
            self.test_results['load_tests'].get('status') == 'passed'
        )
        
        self.test_results['summary'] = {
            'overall_status': 'passed' if all_passed else 'failed',
            'timestamp': datetime.now().isoformat(),
            'kpi_compliance': self._calculate_kpi_compliance()
        }
        
        # Save detailed results
        results_file = self.results_dir / f"performance_report_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Generate summary report
        report = self._format_summary_report()
        
        summary_file = self.results_dir / "latest_performance_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(report)
        
        return report
    
    def _calculate_kpi_compliance(self) -> Dict[str, Any]:
        """Calculate KPI compliance metrics."""
        compliance = {
            'median_latency_compliant': False,
            'throughput_adequate': False,
            'success_rate_acceptable': False,
            'overall_compliant': False
        }
        
        # Check benchmark compliance
        if 'performance_summary' in self.test_results['benchmarks']:
            summary = self.test_results['benchmarks']['performance_summary']
            total = summary.get('total_tests', 1)
            compliant = summary.get('kpi_compliant', 0)
            compliance['benchmark_compliance_rate'] = compliant / total if total > 0 else 0
        
        # Check load test compliance
        if 'metrics' in self.test_results['load_tests']:
            metrics = self.test_results['load_tests']['metrics']
            
            # Median latency should be ≤ 5s (5000ms)
            median_time = metrics.get('median_response_time', 0)
            compliance['median_latency_compliant'] = median_time <= 5000
            
            # Success rate should be ≥ 95%
            total_requests = metrics.get('total_requests', 1)
            failures = metrics.get('failure_count', 0)
            success_rate = (total_requests - failures) / total_requests if total_requests > 0 else 0
            compliance['success_rate_acceptable'] = success_rate >= 0.95
            
            # Throughput should be reasonable
            rps = metrics.get('requests_per_second', 0)
            compliance['throughput_adequate'] = rps >= 1.0  # At least 1 req/sec
        
        # Overall compliance
        compliance['overall_compliant'] = (
            compliance.get('median_latency_compliant', False) and
            compliance.get('success_rate_acceptable', False) and
            compliance.get('throughput_adequate', False)
        )
        
        return compliance
    
    def _format_summary_report(self) -> str:
        """Format a human-readable summary report."""
        summary = self.test_results['summary']
        
        report = f"""
{'='*80}
RNA LAB NAVIGATOR - PERFORMANCE TEST REPORT
{'='*80}
Test Date: {summary['timestamp']}
Overall Status: {'✅ PASSED' if summary['overall_status'] == 'passed' else '❌ FAILED'}

UNIT PERFORMANCE TESTS
{'-'*40}
Status: {self.test_results['unit_tests'].get('status', 'not_run').upper()}
"""
        
        # Benchmark results
        if 'performance_summary' in self.test_results['benchmarks']:
            perf_summary = self.test_results['benchmarks']['performance_summary']
            report += f"""
BENCHMARK TESTS
{'-'*40}
Total Tests: {perf_summary['total_tests']}
Passed: {perf_summary['passed']}
Failed: {perf_summary['failed']}
KPI Compliant: {perf_summary['kpi_compliant']}/{perf_summary['total_tests']}
"""
            
            if 'kpi_violations' in self.test_results['benchmarks']:
                violations = self.test_results['benchmarks']['kpi_violations']
                if violations:
                    report += f"\nKPI Violations:\n"
                    for v in violations:
                        report += f"  - {v['test']}: {v['mean_time']:.3f}s > {v['threshold']}s\n"
        
        # Load test results
        if 'metrics' in self.test_results['load_tests']:
            metrics = self.test_results['load_tests']['metrics']
            report += f"""
LOAD TEST RESULTS
{'-'*40}
Total Requests: {metrics['total_requests']}
Failed Requests: {metrics['failure_count']}
Success Rate: {((metrics['total_requests'] - metrics['failure_count']) / metrics['total_requests']) * 100:.1f}%
Median Response Time: {metrics['median_response_time']:.0f}ms
Average Response Time: {metrics['average_response_time']:.0f}ms
Requests/Second: {metrics['requests_per_second']:.2f}
"""
        
        # KPI Compliance
        kpi = summary.get('kpi_compliance', {})
        report += f"""
KPI COMPLIANCE ANALYSIS
{'-'*40}
≤5s Median Latency: {'✅' if kpi.get('median_latency_compliant') else '❌'}
≥95% Success Rate: {'✅' if kpi.get('success_rate_acceptable') else '❌'}
Adequate Throughput: {'✅' if kpi.get('throughput_adequate') else '❌'}
Overall KPI Compliance: {'✅' if kpi.get('overall_compliant') else '❌'}
"""
        
        # Recommendations
        recommendations = self.test_results.get('recommendations', [])
        if recommendations:
            report += f"""
OPTIMIZATION RECOMMENDATIONS
{'-'*40}
"""
            high_priority = [r for r in recommendations if r.get('priority') == 'high']
            medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
            
            if high_priority:
                report += "HIGH PRIORITY:\n"
                for rec in high_priority:
                    report += f"  - {rec['description']}\n"
                    for suggestion in rec['suggestions'][:2]:  # Show top 2 suggestions
                        report += f"    • {suggestion}\n"
                    report += "\n"
            
            if medium_priority:
                report += "MEDIUM PRIORITY:\n"
                for rec in medium_priority:
                    report += f"  - {rec['description']}\n"
        
        report += f"""
{'='*80}
END OF REPORT
{'='*80}
"""
        
        return report


def main():
    """Main function to run performance tests."""
    parser = argparse.ArgumentParser(description="RNA Lab Navigator Performance Test Runner")
    
    parser.add_argument('--all', action='store_true',
                       help='Run all performance tests')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick performance tests only')
    parser.add_argument('--unit-tests', action='store_true',
                       help='Run unit performance tests')
    parser.add_argument('--benchmark-only', action='store_true',
                       help='Run benchmark tests only')
    parser.add_argument('--load-test', action='store_true',
                       help='Run load tests')
    parser.add_argument('--stress-test', action='store_true',
                       help='Run stress tests')
    
    parser.add_argument('--users', type=int, default=20,
                       help='Number of concurrent users for load testing')
    parser.add_argument('--duration', type=int, default=180,
                       help='Duration of load test in seconds')
    parser.add_argument('--host', default='http://localhost:8000',
                       help='Target host for load testing')
    
    parser.add_argument('--output-dir', 
                       help='Output directory for test results')
    
    args = parser.parse_args()
    
    # Create test runner
    runner = PerformanceTestRunner(args.output_dir)
    
    # Determine what tests to run
    run_unit = args.all or args.quick or args.unit_tests
    run_benchmark = args.all or args.quick or args.benchmark_only
    run_load = args.all or args.load_test
    run_stress = args.all or args.stress_test
    
    if not any([run_unit, run_benchmark, run_load, run_stress]):
        # Default to quick tests
        run_unit = True
        run_benchmark = True
    
    print("🚀 Starting RNA Lab Navigator Performance Tests")
    print(f"Output directory: {runner.results_dir}")
    
    # Run selected tests
    results = []
    
    if run_unit:
        results.append(runner.run_unit_performance_tests())
    
    if run_benchmark:
        results.append(runner.run_benchmark_tests())
    
    if run_load:
        results.append(runner.run_load_test(args.users, args.duration, args.host))
    
    if run_stress:
        results.append(runner.run_stress_test(args.users, args.duration, args.host))
    
    # Generate and display report
    report = runner.generate_report()
    print("\n" + report)
    
    # Exit with appropriate code
    overall_success = all(results) if results else False
    
    if overall_success:
        print("🎉 All performance tests passed!")
        sys.exit(0)
    else:
        print("💥 Some performance tests failed. Check the report for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()