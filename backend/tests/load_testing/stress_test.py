#!/usr/bin/env python3
"""
Stress testing script for RNA Lab Navigator.

This script performs automated stress testing with various load patterns
to identify performance bottlenecks and validate KPI requirements.

Usage:
    python stress_test.py --host http://localhost:8000 --duration 300
    python stress_test.py --host http://localhost:8000 --users 50 --spawn-rate 5
"""

import argparse
import asyncio
import aiohttp
import time
import json
import statistics
import logging
import sys
from typing import Dict, List, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Container for test results."""
    timestamp: float
    response_time: float
    status_code: int
    success: bool
    query_type: str
    error_message: str = ""

@dataclass 
class StressTestMetrics:
    """Container for aggregated stress test metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    kpi_violations: int = 0
    test_duration: float = 0
    start_time: float = 0
    end_time: float = 0
    
    @property
    def success_rate(self) -> float:
        return self.successful_requests / self.total_requests if self.total_requests > 0 else 0
    
    @property
    def throughput(self) -> float:
        return self.successful_requests / self.test_duration if self.test_duration > 0 else 0
    
    @property
    def mean_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0
    
    @property
    def median_response_time(self) -> float:
        return statistics.median(self.response_times) if self.response_times else 0
    
    @property
    def p95_response_time(self) -> float:
        if len(self.response_times) >= 20:
            return statistics.quantiles(self.response_times, n=20)[18]
        return max(self.response_times) if self.response_times else 0
    
    @property
    def p99_response_time(self) -> float:
        if len(self.response_times) >= 100:
            return statistics.quantiles(self.response_times, n=100)[98]
        return max(self.response_times) if self.response_times else 0


class AsyncStressTester:
    """Asynchronous stress tester for the RNA Lab Navigator."""
    
    def __init__(self, base_url: str, concurrent_users: int = 10):
        self.base_url = base_url.rstrip('/')
        self.concurrent_users = concurrent_users
        self.session = None
        self.results = []
        self.metrics = StressTestMetrics()
        
        # Test queries categorized by complexity
        self.simple_queries = [
            "What is RNA?",
            "DNA vs RNA",
            "PCR protocol",
            "Western blot",
            "qPCR steps"
        ]
        
        self.medium_queries = [
            "How do you extract RNA from cells?",
            "What is the difference between DNA and RNA?", 
            "Explain PCR protocol steps in detail",
            "How to perform western blot analysis?",
            "What is qPCR and how does it work?"
        ]
        
        self.complex_queries = [
            "What is the relationship between RNA structure and function in ribozymes?",
            "How do post-transcriptional modifications affect RNA stability?",
            "Explain the mechanisms of RNA interference and therapeutic applications",
            "What are the latest advances in single-cell RNA sequencing?",
            "How does alternative splicing contribute to protein diversity?"
        ]
    
    async def setup_session(self):
        """Setup aiohttp session with appropriate settings."""
        timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={"Content-Type": "application/json"}
        )
    
    async def cleanup_session(self):
        """Cleanup aiohttp session."""
        if self.session:
            await self.session.close()
    
    async def authenticate_user(self, user_id: int) -> str:
        """Authenticate a test user and return token."""
        username = f"stress_test_user_{user_id}"
        password = "test_password"
        email = f"{username}@test.com"
        
        # Try to register user (will fail if exists, that's ok)
        try:
            async with self.session.post(f"{self.base_url}/api/auth/register/", json={
                "username": username,
                "password": password,
                "email": email
            }) as response:
                pass  # Ignore response
        except Exception:
            pass  # User might already exist
        
        # Login user
        try:
            async with self.session.post(f"{self.base_url}/api/auth/login/", json={
                "username": username,
                "password": password
            }) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("token", "")
        except Exception as e:
            logger.error(f"Failed to authenticate user {user_id}: {str(e)}")
        
        return ""
    
    async def perform_query(self, token: str, query: str, query_type: str) -> TestResult:
        """Perform a single query and measure performance."""
        start_time = time.time()
        
        headers = {"Authorization": f"Token {token}"} if token else {}
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/query/",
                json={"question": query, "doc_type": "all"},
                headers=headers
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                success = response.status == 200
                
                return TestResult(
                    timestamp=start_time,
                    response_time=response_time,
                    status_code=response.status,
                    success=success,
                    query_type=query_type,
                    error_message="" if success else f"HTTP {response.status}"
                )
        
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            return TestResult(
                timestamp=start_time,
                response_time=response_time,
                status_code=0,
                success=False,
                query_type=query_type,
                error_message=str(e)
            )
    
    async def user_session(self, user_id: int, duration: int, queries_per_minute: int = 10):
        """Simulate a user session with multiple queries."""
        token = await self.authenticate_user(user_id)
        
        session_start = time.time()
        query_interval = 60.0 / queries_per_minute  # Seconds between queries
        
        user_results = []
        
        while time.time() - session_start < duration:
            # Select query type based on realistic distribution
            import random
            rand = random.random()
            if rand < 0.6:  # 60% simple queries
                query = random.choice(self.simple_queries)
                query_type = "simple"
            elif rand < 0.85:  # 25% medium queries  
                query = random.choice(self.medium_queries)
                query_type = "medium"
            else:  # 15% complex queries
                query = random.choice(self.complex_queries)
                query_type = "complex"
            
            # Perform query
            result = await self.perform_query(token, query, query_type)
            user_results.append(result)
            
            # Wait for next query
            await asyncio.sleep(query_interval + random.uniform(-0.1, 0.1))  # Add jitter
        
        return user_results
    
    async def run_stress_test(self, duration: int = 300, spawn_rate: int = 1) -> StressTestMetrics:
        """Run the stress test with specified parameters."""
        logger.info(f"Starting stress test: {self.concurrent_users} users, {duration}s duration")
        
        await self.setup_session()
        
        self.metrics.start_time = time.time()
        
        try:
            # Create user sessions with staggered start times
            tasks = []
            for i in range(self.concurrent_users):
                # Stagger user starts
                delay = i / spawn_rate
                task = asyncio.create_task(
                    self.delayed_user_session(i, duration, delay)
                )
                tasks.append(task)
            
            # Wait for all sessions to complete
            all_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Aggregate results
            for user_results in all_results:
                if isinstance(user_results, Exception):
                    logger.error(f"User session failed: {str(user_results)}")
                    continue
                
                for result in user_results:
                    self.results.append(result)
                    self.metrics.total_requests += 1
                    
                    if result.success:
                        self.metrics.successful_requests += 1
                        self.metrics.response_times.append(result.response_time)
                        
                        # Check KPI compliance
                        threshold = 5.0 if result.query_type != "complex" else 8.0
                        if result.response_time > threshold:
                            self.metrics.kpi_violations += 1
                    else:
                        self.metrics.failed_requests += 1
                        self.metrics.errors.append(result.error_message)
        
        finally:
            self.metrics.end_time = time.time()
            self.metrics.test_duration = self.metrics.end_time - self.metrics.start_time
            await self.cleanup_session()
        
        return self.metrics
    
    async def delayed_user_session(self, user_id: int, duration: int, delay: float):
        """Start a user session after a delay."""
        await asyncio.sleep(delay)
        return await self.user_session(user_id, duration)
    
    def generate_report(self, output_file: str = None) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        report = {
            "test_summary": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": self.metrics.success_rate,
                "test_duration": self.metrics.test_duration,
                "throughput": self.metrics.throughput,
                "concurrent_users": self.concurrent_users
            },
            "response_times": {
                "mean": self.metrics.mean_response_time,
                "median": self.metrics.median_response_time,
                "p95": self.metrics.p95_response_time,
                "p99": self.metrics.p99_response_time,
                "min": min(self.metrics.response_times) if self.metrics.response_times else 0,
                "max": max(self.metrics.response_times) if self.metrics.response_times else 0
            },
            "kpi_analysis": {
                "violations": self.metrics.kpi_violations,
                "violation_rate": self.metrics.kpi_violations / self.metrics.total_requests if self.metrics.total_requests > 0 else 0,
                "compliance_rate": 1 - (self.metrics.kpi_violations / self.metrics.total_requests) if self.metrics.total_requests > 0 else 1,
                "median_meets_kpi": self.metrics.median_response_time <= 5.0,
                "p95_meets_kpi": self.metrics.p95_response_time <= 5.0
            }
        }
        
        # Query type breakdown
        query_types = {}
        for result in self.results:
            if result.query_type not in query_types:
                query_types[result.query_type] = {"count": 0, "success": 0, "times": []}
            
            query_types[result.query_type]["count"] += 1
            if result.success:
                query_types[result.query_type]["success"] += 1
                query_types[result.query_type]["times"].append(result.response_time)
        
        for query_type, data in query_types.items():
            if data["times"]:
                data["mean_time"] = statistics.mean(data["times"])
                data["success_rate"] = data["success"] / data["count"]
        
        report["query_types"] = query_types
        
        # Save report if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {output_file}")
        
        return report
    
    def print_report(self):
        """Print formatted test report to console."""
        report = self.generate_report()
        
        print("\n" + "="*80)
        print("RNA LAB NAVIGATOR - STRESS TEST REPORT")
        print("="*80)
        
        # Test Summary
        summary = report["test_summary"]
        print(f"Test Duration: {summary['test_duration']:.1f}s")
        print(f"Concurrent Users: {summary['concurrent_users']}")
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Successful Requests: {summary['successful_requests']}")
        print(f"Failed Requests: {summary['failed_requests']}")
        print(f"Success Rate: {summary['success_rate']:.2%}")
        print(f"Throughput: {summary['throughput']:.2f} req/s")
        
        # Response Times
        times = report["response_times"]
        print(f"\nResponse Time Statistics:")
        print(f"  Mean: {times['mean']:.3f}s")
        print(f"  Median: {times['median']:.3f}s")
        print(f"  P95: {times['p95']:.3f}s")
        print(f"  P99: {times['p99']:.3f}s")
        print(f"  Min: {times['min']:.3f}s")
        print(f"  Max: {times['max']:.3f}s")
        
        # KPI Analysis
        kpi = report["kpi_analysis"]
        print(f"\nKPI Analysis (≤5s target):")
        print(f"  KPI Violations: {kpi['violations']}")
        print(f"  Violation Rate: {kpi['violation_rate']:.2%}")
        print(f"  Compliance Rate: {kpi['compliance_rate']:.2%}")
        print(f"  Median Meets KPI: {'✓' if kpi['median_meets_kpi'] else '✗'}")
        print(f"  P95 Meets KPI: {'✓' if kpi['p95_meets_kpi'] else '✗'}")
        
        # Query Type Breakdown
        print(f"\nQuery Type Performance:")
        for query_type, data in report["query_types"].items():
            print(f"  {query_type.capitalize()}:")
            print(f"    Count: {data['count']}")
            print(f"    Success Rate: {data.get('success_rate', 0):.2%}")
            print(f"    Mean Time: {data.get('mean_time', 0):.3f}s")
        
        # Overall Assessment
        print(f"\n" + "="*80)
        overall_pass = (kpi['median_meets_kpi'] and kpi['compliance_rate'] >= 0.95 and 
                       summary['success_rate'] >= 0.95)
        
        if overall_pass:
            print("✅ STRESS TEST PASSED")
            print("System meets performance requirements under stress conditions.")
        else:
            print("❌ STRESS TEST FAILED")
            print("System requires optimization to meet performance requirements.")
            
            if not kpi['median_meets_kpi']:
                print("  - Median response time exceeds 5s KPI")
            if kpi['compliance_rate'] < 0.95:
                print("  - Too many requests exceed response time threshold")
            if summary['success_rate'] < 0.95:
                print("  - Success rate below acceptable threshold")
        
        print("="*80)


async def main():
    """Main function to run stress tests."""
    parser = argparse.ArgumentParser(description="RNA Lab Navigator Stress Test")
    parser.add_argument("--host", default="http://localhost:8000", 
                       help="Target host URL")
    parser.add_argument("--users", type=int, default=20,
                       help="Number of concurrent users")
    parser.add_argument("--duration", type=int, default=180,
                       help="Test duration in seconds")
    parser.add_argument("--spawn-rate", type=int, default=2,
                       help="User spawn rate (users/second)")
    parser.add_argument("--output", help="Output file for JSON report")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress detailed output")
    
    args = parser.parse_args()
    
    # Configure logging
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Create and run stress tester
    tester = AsyncStressTester(args.host, args.users)
    
    try:
        print(f"Starting stress test against {args.host}")
        print(f"Configuration: {args.users} users, {args.duration}s duration, {args.spawn_rate} spawn rate")
        
        metrics = await tester.run_stress_test(args.duration, args.spawn_rate)
        
        # Generate and print report
        tester.print_report()
        
        # Save report if requested
        if args.output:
            tester.generate_report(args.output)
        
        # Exit with appropriate code
        kpi_pass = (metrics.median_response_time <= 5.0 and 
                   metrics.kpi_violations / metrics.total_requests <= 0.05 if metrics.total_requests > 0 else True)
        
        sys.exit(0 if kpi_pass else 1)
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())