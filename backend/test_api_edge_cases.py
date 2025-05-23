#!/usr/bin/env python
"""
Edge case and security testing for RNA Lab Navigator APIs
Tests for malformed requests, injection attempts, and boundary conditions
"""

import requests
import json
import concurrent.futures
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api"

# Malformed request tests
MALFORMED_TESTS = [
    # Invalid JSON
    {
        "endpoint": "/query/",
        "data": '{"query": "test", invalid json}',
        "content_type": "application/json",
        "expected_status": 400
    },
    # Wrong content type
    {
        "endpoint": "/query/",
        "data": "query=test",
        "content_type": "application/x-www-form-urlencoded",
        "expected_status": 400
    },
    # Missing required fields
    {
        "endpoint": "/query/",
        "json": {},
        "expected_status": 400
    },
    {
        "endpoint": "/hypothesis/explore/",
        "json": {"use_advanced_model": False},  # Missing question
        "expected_status": 400
    },
    # Invalid field types
    {
        "endpoint": "/query/",
        "json": {"query": 123},  # Should be string
        "expected_status": 400
    },
    {
        "endpoint": "/hypothesis/generate-protocol/",
        "json": {
            "requirements": 123,  # Should be string
            "base_protocol_id": "not an int"  # Should be int or None
        },
        "expected_status": 400
    }
]

# Injection attempt tests
INJECTION_TESTS = [
    # SQL injection attempts
    {
        "endpoint": "/query/",
        "json": {"query": "'; DROP TABLE documents; --"},
        "check": "no_error"
    },
    {
        "endpoint": "/query/",
        "json": {"query": "RNA extraction' OR '1'='1"},
        "check": "no_error"
    },
    # Script injection
    {
        "endpoint": "/query/",
        "json": {"query": "<script>alert('xss')</script>RNA extraction"},
        "check": "sanitized_output"
    },
    # Command injection
    {
        "endpoint": "/hypothesis/explore/",
        "json": {
            "question": "test; cat /etc/passwd",
            "use_advanced_model": False
        },
        "check": "no_error"
    },
    # Path traversal
    {
        "endpoint": "/query/",
        "json": {"query": "../../etc/passwd"},
        "check": "no_error"
    }
]

# Boundary condition tests
BOUNDARY_TESTS = [
    # Very long input
    {
        "endpoint": "/query/",
        "json": {"query": "RNA " * 1000},  # ~4000 chars
        "expected_status": [200, 400]
    },
    # Unicode and special characters
    {
        "endpoint": "/query/",
        "json": {"query": "RNA extraction 🧬 测试 тест"},
        "expected_status": 200
    },
    # Empty strings vs null
    {
        "endpoint": "/hypothesis/explore/",
        "json": {"question": "", "use_advanced_model": False},
        "expected_status": 400
    },
    {
        "endpoint": "/hypothesis/explore/",
        "json": {"question": None, "use_advanced_model": None},
        "expected_status": 400
    },
    # Complex requirements
    {
        "endpoint": "/hypothesis/generate-protocol/",
        "json": {
            "requirements": "PCR protocol with nested requirements: " + "x" * 1000,
            "base_protocol_id": None
        },
        "expected_status": [200, 400]
    }
]

# Performance and rate limiting tests
PERFORMANCE_TESTS = [
    # Concurrent requests
    {
        "endpoint": "/query/",
        "json": {"query": "What is RNA extraction?"},
        "concurrent_requests": 10,
        "check_all_succeed": True
    },
    # Rapid sequential requests
    {
        "endpoint": "/query/",
        "json": {"query": "PCR protocol"},
        "rapid_requests": 20,
        "check_rate_limit": True
    }
]


class EdgeCaseTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = {
            "malformed": {"passed": 0, "failed": 0},
            "injection": {"passed": 0, "failed": 0},
            "boundary": {"passed": 0, "failed": 0},
            "performance": {"passed": 0, "failed": 0},
            "issues": []
        }
    
    def test_malformed_requests(self):
        """Test handling of malformed requests"""
        print("\n🔨 Testing Malformed Requests...")
        
        for test in MALFORMED_TESTS:
            endpoint = self.base_url + test["endpoint"]
            
            try:
                if "json" in test:
                    response = requests.post(
                        endpoint,
                        json=test["json"],
                        timeout=10
                    )
                else:
                    response = requests.post(
                        endpoint,
                        data=test.get("data", ""),
                        headers={"Content-Type": test.get("content_type", "application/json")},
                        timeout=10
                    )
                
                if response.status_code == test["expected_status"]:
                    self.results["malformed"]["passed"] += 1
                    print(f"  ✅ {test['endpoint']} - Correctly rejected")
                else:
                    self.results["malformed"]["failed"] += 1
                    print(f"  ❌ {test['endpoint']} - Got {response.status_code}, expected {test['expected_status']}")
                    self.results["issues"].append(f"Malformed request handling: {test}")
                    
            except Exception as e:
                self.results["malformed"]["failed"] += 1
                print(f"  💥 {test['endpoint']} - Error: {str(e)}")
    
    def test_injection_attempts(self):
        """Test handling of injection attempts"""
        print("\n💉 Testing Injection Attempts...")
        
        for test in INJECTION_TESTS:
            endpoint = self.base_url + test["endpoint"]
            
            try:
                response = requests.post(
                    endpoint,
                    json=test["json"],
                    timeout=10
                )
                
                if test["check"] == "no_error":
                    if response.status_code in [200, 400]:
                        self.results["injection"]["passed"] += 1
                        print(f"  ✅ {test['endpoint']} - Handled safely")
                    else:
                        self.results["injection"]["failed"] += 1
                        print(f"  ❌ {test['endpoint']} - Unexpected error")
                        self.results["issues"].append(f"Injection handling: {test}")
                
                elif test["check"] == "sanitized_output":
                    if response.status_code == 200:
                        data = response.json()
                        if "<script>" not in json.dumps(data):
                            self.results["injection"]["passed"] += 1
                            print(f"  ✅ {test['endpoint']} - Output sanitized")
                        else:
                            self.results["injection"]["failed"] += 1
                            print(f"  ❌ {test['endpoint']} - Output not sanitized")
                            self.results["issues"].append(f"XSS vulnerability: {test}")
                            
            except Exception as e:
                self.results["injection"]["failed"] += 1
                print(f"  💥 {test['endpoint']} - Error: {str(e)}")
    
    def test_boundary_conditions(self):
        """Test boundary conditions"""
        print("\n📏 Testing Boundary Conditions...")
        
        for test in BOUNDARY_TESTS:
            endpoint = self.base_url + test["endpoint"]
            
            try:
                response = requests.post(
                    endpoint,
                    json=test["json"],
                    timeout=10
                )
                
                expected = test["expected_status"]
                if isinstance(expected, list):
                    if response.status_code in expected:
                        self.results["boundary"]["passed"] += 1
                        print(f"  ✅ {test['endpoint']} - Status {response.status_code}")
                    else:
                        self.results["boundary"]["failed"] += 1
                        print(f"  ❌ {test['endpoint']} - Got {response.status_code}, expected one of {expected}")
                else:
                    if response.status_code == expected:
                        self.results["boundary"]["passed"] += 1
                        print(f"  ✅ {test['endpoint']} - Status {response.status_code}")
                    else:
                        self.results["boundary"]["failed"] += 1
                        print(f"  ❌ {test['endpoint']} - Got {response.status_code}, expected {expected}")
                        
            except Exception as e:
                self.results["boundary"]["failed"] += 1
                print(f"  💥 {test['endpoint']} - Error: {str(e)}")
    
    def test_performance(self):
        """Test performance and rate limiting"""
        print("\n⚡ Testing Performance & Rate Limiting...")
        
        for test in PERFORMANCE_TESTS:
            endpoint = self.base_url + test["endpoint"]
            
            if "concurrent_requests" in test:
                print(f"  Testing {test['concurrent_requests']} concurrent requests...")
                
                def make_request():
                    return requests.post(endpoint, json=test["json"], timeout=30)
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=test["concurrent_requests"]) as executor:
                    futures = [executor.submit(make_request) for _ in range(test["concurrent_requests"])]
                    results = [f.result() for f in concurrent.futures.as_completed(futures)]
                
                success_count = sum(1 for r in results if r.status_code == 200)
                if success_count == len(results):
                    self.results["performance"]["passed"] += 1
                    print(f"  ✅ All {len(results)} concurrent requests succeeded")
                else:
                    self.results["performance"]["failed"] += 1
                    print(f"  ❌ Only {success_count}/{len(results)} requests succeeded")
            
            elif "rapid_requests" in test:
                print(f"  Testing {test['rapid_requests']} rapid requests...")
                
                rate_limited = False
                for i in range(test["rapid_requests"]):
                    response = requests.post(endpoint, json=test["json"], timeout=10)
                    if response.status_code == 429:  # Too Many Requests
                        rate_limited = True
                        break
                
                if test.get("check_rate_limit") and rate_limited:
                    self.results["performance"]["passed"] += 1
                    print(f"  ✅ Rate limiting working (triggered at request {i+1})")
                elif not test.get("check_rate_limit") and not rate_limited:
                    self.results["performance"]["passed"] += 1
                    print(f"  ✅ All rapid requests handled")
                else:
                    self.results["performance"]["failed"] += 1
                    print(f"  ⚠️  Rate limiting may not be configured")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 Edge Case Test Summary")
        
        total_passed = sum(cat["passed"] for cat in self.results.values() if isinstance(cat, dict))
        total_failed = sum(cat["failed"] for cat in self.results.values() if isinstance(cat, dict))
        
        print(f"\n  Total: {total_passed + total_failed} tests")
        print(f"  ✅ Passed: {total_passed}")
        print(f"  ❌ Failed: {total_failed}")
        
        print("\n  Category Breakdown:")
        for category, results in self.results.items():
            if isinstance(results, dict):
                print(f"    {category.capitalize()}: {results['passed']}/{results['passed'] + results['failed']}")
        
        if self.results["issues"]:
            print("\n⚠️  Security/Stability Issues Found:")
            for issue in self.results["issues"][:5]:
                print(f"  - {issue}")
        
        # Save results
        with open("edge_case_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("\n💾 Results saved to edge_case_results.json")


def main():
    """Run edge case tests"""
    print("🧪 RNA Lab Navigator Edge Case Testing")
    print("=" * 50)
    
    tester = EdgeCaseTester(BASE_URL)
    
    tester.test_malformed_requests()
    tester.test_injection_attempts()
    tester.test_boundary_conditions()
    tester.test_performance()
    
    tester.print_summary()


if __name__ == "__main__":
    main()