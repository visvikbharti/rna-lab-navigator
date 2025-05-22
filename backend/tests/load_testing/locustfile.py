"""
Locust load testing configuration for RNA Lab Navigator.

This file defines load testing scenarios to validate the ≤5s latency KPI
under various load conditions and user behaviors.

Usage:
1. Install locust: pip install locust
2. Run basic load test: locust -f tests/load_testing/locustfile.py --host=http://localhost:8000
3. Run with specific parameters: locust -f tests/load_testing/locustfile.py --host=http://localhost:8000 -u 50 -r 5 -t 300s
4. Run headless: locust -f tests/load_testing/locustfile.py --host=http://localhost:8000 -u 20 -r 2 -t 120s --headless

KPI Requirements:
- Median end-to-end latency ≤ 5s
- Handle multiple concurrent users efficiently
- Maintain high success rate under load
"""

import json
import random
import time
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import logging

# Setup logging for load testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data sets for realistic load testing
RESEARCH_QUERIES = [
    "What is RNA?",
    "How do you extract RNA from cells?", 
    "What is the difference between DNA and RNA?",
    "Explain PCR protocol steps",
    "What are the latest advances in CRISPR technology?",
    "How to perform western blot analysis?",
    "What is qPCR and how does it work?",
    "Describe RNA sequencing workflows",
    "What is RNA interference?",
    "How does transcription work?",
    "What are microRNAs?",
    "Explain gel electrophoresis procedure",
    "What is Northern blotting?",
    "How to perform RT-PCR?",
    "What are ribosomes?",
    "Describe RNA folding mechanisms",
    "What is CRISPR-Cas9?",
    "How to isolate total RNA?",
    "What is RNA-seq data analysis?",
    "Explain splicing mechanisms"
]

PROTOCOL_QUERIES = [
    "RNA extraction protocol",
    "Western blot protocol steps",
    "qPCR setup procedure", 
    "Cell culture maintenance",
    "Protein purification steps",
    "DNA cloning protocol",
    "Immunofluorescence staining",
    "Flow cytometry analysis",
    "ELISA protocol",
    "ChIP-seq procedure"
]

COMPLEX_QUERIES = [
    "What is the relationship between RNA structure and function in ribozymes?",
    "How do post-transcriptional modifications affect RNA stability and protein recognition?",
    "Explain the mechanisms of RNA interference and its therapeutic applications",
    "What are the latest advances in single-cell RNA sequencing and data analysis?",
    "How does alternative splicing contribute to protein diversity in eukaryotes?",
    "Describe the role of long non-coding RNAs in gene regulation",
    "What are the molecular mechanisms of CRISPR-mediated genome editing?",
    "How do RNA-binding proteins regulate mRNA stability and translation?",
    "Explain the biogenesis and function of microRNAs in development",
    "What are the emerging applications of RNA therapeutics in medicine?"
]

DOC_TYPES = ["all", "paper", "protocol", "thesis"]

# Global metrics collection
performance_metrics = {
    "response_times": [],
    "failures": 0,
    "successes": 0,
    "kpi_violations": 0
}


class RAGUser(HttpUser):
    """Simulates a typical RNA lab researcher using the system."""
    
    # Wait time between tasks (1-5 seconds)
    wait_time = between(1, 5)
    
    def on_start(self):
        """Called when a user starts - perform login."""
        self.login()
    
    def login(self):
        """Authenticate the user."""
        # Create a test user or use existing one
        login_data = {
            "username": f"load_test_user_{random.randint(1, 1000)}",
            "password": "test_password"
        }
        
        # Try to create user first (will fail if exists, that's ok)
        self.client.post("/api/auth/register/", {
            "username": login_data["username"],
            "password": login_data["password"],
            "email": f"{login_data['username']}@test.com"
        })
        
        # Login
        response = self.client.post("/api/auth/login/", login_data)
        if response.status_code == 200:
            # Extract token if using token auth
            data = response.json()
            if "token" in data:
                self.client.headers.update({"Authorization": f"Token {data['token']}"})
        
    @task(50)  # 50% weight - most common queries
    def simple_research_query(self):
        """Perform simple research queries (most common use case)."""
        query = random.choice(RESEARCH_QUERIES)
        doc_type = random.choice(DOC_TYPES)
        
        start_time = time.time()
        
        with self.client.post("/api/query/", json={
            "question": query,
            "doc_type": doc_type
        }, catch_response=True) as response:
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Check if response meets KPI requirement
                if response_time > 5.0:
                    performance_metrics["kpi_violations"] += 1
                    response.failure(f"Response time {response_time:.2f}s exceeds 5s KPI")
                else:
                    performance_metrics["successes"] += 1
                    performance_metrics["response_times"].append(response_time)
            else:
                performance_metrics["failures"] += 1
                response.failure(f"HTTP {response.status_code}")
    
    @task(30)  # 30% weight - protocol searches
    def protocol_query(self):
        """Search for laboratory protocols."""
        query = random.choice(PROTOCOL_QUERIES)
        
        start_time = time.time()
        
        with self.client.post("/api/query/", json={
            "question": query,
            "doc_type": "protocol"
        }, catch_response=True) as response:
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                if response_time > 5.0:
                    performance_metrics["kpi_violations"] += 1
                    response.failure(f"Protocol query time {response_time:.2f}s exceeds 5s KPI")
                else:
                    performance_metrics["successes"] += 1
                    performance_metrics["response_times"].append(response_time)
            else:
                performance_metrics["failures"] += 1
                response.failure(f"HTTP {response.status_code}")
    
    @task(15)  # 15% weight - complex research queries
    def complex_research_query(self):
        """Perform complex, detailed research queries."""
        query = random.choice(COMPLEX_QUERIES)
        
        start_time = time.time()
        
        with self.client.post("/api/query/", json={
            "question": query,
            "doc_type": "all"
        }, catch_response=True) as response:
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Complex queries get slightly more lenient threshold (8s)
                if response_time > 8.0:
                    performance_metrics["kpi_violations"] += 1
                    response.failure(f"Complex query time {response_time:.2f}s exceeds 8s threshold")
                else:
                    performance_metrics["successes"] += 1
                    performance_metrics["response_times"].append(response_time)
            else:
                performance_metrics["failures"] += 1
                response.failure(f"HTTP {response.status_code}")
    
    @task(3)  # 3% weight - search functionality
    def search_documents(self):
        """Test search endpoint directly."""
        query = random.choice(RESEARCH_QUERIES[:10])  # Use shorter queries for search
        
        with self.client.get("/api/search/", params={
            "q": query,
            "limit": 10
        }, catch_response=True) as response:
            
            if response.status_code != 200:
                response.failure(f"Search failed with HTTP {response.status_code}")
    
    @task(2)  # 2% weight - check system health
    def health_check(self):
        """Perform health checks."""
        with self.client.get("/api/health/", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Health check failed with HTTP {response.status_code}")


class BurstTrafficUser(HttpUser):
    """Simulates burst traffic patterns (e.g., multiple students using system simultaneously)."""
    
    # Shorter wait times to simulate burst
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Authenticate user."""
        self.login()
    
    def login(self):
        """Simple login for burst testing."""
        login_data = {
            "username": f"burst_user_{random.randint(1, 500)}",
            "password": "test_password"
        }
        
        self.client.post("/api/auth/register/", {
            "username": login_data["username"], 
            "password": login_data["password"],
            "email": f"{login_data['username']}@test.com"
        })
        
        response = self.client.post("/api/auth/login/", login_data)
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                self.client.headers.update({"Authorization": f"Token {data['token']}"})
    
    @task
    def rapid_queries(self):
        """Perform rapid successive queries."""
        for _ in range(random.randint(2, 5)):  # 2-5 queries per burst
            query = random.choice(RESEARCH_QUERIES[:15])  # Use common queries
            
            start_time = time.time()
            
            with self.client.post("/api/query/", json={
                "question": query,
                "doc_type": "all"
            }, catch_response=True) as response:
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    if response_time > 5.0:
                        performance_metrics["kpi_violations"] += 1
                        response.failure(f"Burst query time {response_time:.2f}s exceeds 5s KPI")
                    else:
                        performance_metrics["successes"] += 1
                        performance_metrics["response_times"].append(response_time)
                else:
                    performance_metrics["failures"] += 1
                    response.failure(f"HTTP {response.status_code}")
            
            # Very short delay between burst queries
            time.sleep(random.uniform(0.1, 0.5))


class SlowConnectionUser(HttpUser):
    """Simulates users with slower connections (to test system robustness)."""
    
    wait_time = between(3, 8)  # Longer delays
    connection_timeout = 10  # Longer timeout
    network_timeout = 10
    
    def on_start(self):
        """Setup for slow connection simulation."""
        self.login()
    
    def login(self):
        """Login with slower connection simulation."""
        login_data = {
            "username": f"slow_user_{random.randint(1, 200)}",
            "password": "test_password"
        }
        
        self.client.post("/api/auth/register/", {
            "username": login_data["username"],
            "password": login_data["password"], 
            "email": f"{login_data['username']}@test.com"
        })
        
        response = self.client.post("/api/auth/login/", login_data)
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                self.client.headers.update({"Authorization": f"Token {data['token']}"})
    
    @task
    def slow_connection_query(self):
        """Perform queries with simulated slow connection."""
        query = random.choice(RESEARCH_QUERIES)
        
        start_time = time.time()
        
        with self.client.post("/api/query/", json={
            "question": query,
            "doc_type": "all"
        }, timeout=15, catch_response=True) as response:  # Longer timeout
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Even with slow connections, system should respond within KPI
                if response_time > 5.0:
                    performance_metrics["kpi_violations"] += 1
                    response.failure(f"Slow connection query time {response_time:.2f}s exceeds 5s KPI")
                else:
                    performance_metrics["successes"] += 1
                    performance_metrics["response_times"].append(response_time)
            else:
                performance_metrics["failures"] += 1
                response.failure(f"HTTP {response.status_code}")


# Event handlers for metrics collection and reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    logger.info("Starting RNA Lab Navigator load test...")
    logger.info(f"Target host: {environment.host}")
    if isinstance(environment.runner, MasterRunner):
        logger.info(f"Running distributed test with {environment.runner.worker_count} workers")


@events.test_stop.add_listener  
def on_test_stop(environment, **kwargs):
    """Called when test stops - report KPI metrics."""
    logger.info("Load test completed. Analyzing KPI metrics...")
    
    if performance_metrics["response_times"]:
        import statistics
        
        response_times = performance_metrics["response_times"]
        total_requests = performance_metrics["successes"] + performance_metrics["failures"]
        success_rate = performance_metrics["successes"] / total_requests if total_requests > 0 else 0
        
        # Calculate response time statistics
        mean_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
        p99_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times)
        
        # KPI Analysis
        kpi_compliance = (performance_metrics["kpi_violations"] / total_requests) if total_requests > 0 else 0
        
        print("\n" + "="*60)
        print("RNA LAB NAVIGATOR - LOAD TEST KPI REPORT")
        print("="*60)
        print(f"Total Requests: {total_requests}")
        print(f"Successful Requests: {performance_metrics['successes']}")
        print(f"Failed Requests: {performance_metrics['failures']}")
        print(f"Success Rate: {success_rate:.2%}")
        print(f"\nResponse Time Statistics:")
        print(f"  Mean: {mean_time:.3f}s")
        print(f"  Median: {median_time:.3f}s")
        print(f"  95th Percentile: {p95_time:.3f}s")
        print(f"  99th Percentile: {p99_time:.3f}s")
        print(f"  Min: {min(response_times):.3f}s")
        print(f"  Max: {max(response_times):.3f}s")
        print(f"\nKPI Compliance:")
        print(f"  Requests exceeding 5s: {performance_metrics['kpi_violations']}")
        print(f"  KPI violation rate: {kpi_compliance:.2%}")
        print(f"  KPI compliance rate: {(1-kpi_compliance):.2%}")
        
        # KPI Assessment
        print(f"\nKPI ASSESSMENT:")
        kpi_pass = median_time <= 5.0 and kpi_compliance <= 0.05  # Allow 5% violation rate
        print(f"  ≤5s Median Latency: {'✓ PASS' if median_time <= 5.0 else '✗ FAIL'} ({median_time:.3f}s)")
        print(f"  Overall KPI Compliance: {'✓ PASS' if kpi_pass else '✗ FAIL'}")
        
        if not kpi_pass:
            print(f"\n⚠️  KPI REQUIREMENTS NOT MET!")
            print(f"   - System requires optimization to meet ≤5s latency requirement")
            print(f"   - Consider implementing caching, query optimization, or scaling")
        else:
            print(f"\n✅ KPI REQUIREMENTS MET!")
            print(f"   - System successfully meets ≤5s median latency requirement")
        
        print("="*60)
    else:
        logger.warning("No successful requests recorded for KPI analysis")


# Custom load shapes for different testing scenarios
class StepLoadShape:
    """Gradually increase load to find breaking point."""
    
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time < 60:
            return (10, 2)  # 10 users, spawn 2/sec
        elif run_time < 120:
            return (25, 3)  # 25 users, spawn 3/sec  
        elif run_time < 180:
            return (50, 5)  # 50 users, spawn 5/sec
        elif run_time < 240:
            return (75, 7)  # 75 users, spawn 7/sec
        elif run_time < 300:
            return (100, 10)  # 100 users, spawn 10/sec
        else:
            return None  # Stop test


if __name__ == "__main__":
    # Example usage when running directly
    print("RNA Lab Navigator Load Testing Configuration")
    print("Use with: locust -f locustfile.py --host=http://localhost:8000")
    print("\nAvailable user classes:")
    print("- RAGUser: Normal research usage patterns")
    print("- BurstTrafficUser: Burst traffic simulation")  
    print("- SlowConnectionUser: Slow connection simulation")