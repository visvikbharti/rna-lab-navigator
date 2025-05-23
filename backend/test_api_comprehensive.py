#!/usr/bin/env python
"""
Comprehensive API testing for RNA Lab Navigator
Tests RAG query, hypothesis exploration, and protocol generation endpoints
"""

import requests
import json
import time
from typing import Dict, List, Any
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000/api"
HEADERS = {"Content-Type": "application/json"}

# Test cases for different endpoints
RAG_QUERY_TESTS = [
    # Basic scientific queries
    {
        "query": "What is the optimal temperature for RNA extraction using TRIzol?",
        "expected_keywords": ["temperature", "TRIzol", "RNA", "extraction"],
        "check_citations": True
    },
    {
        "query": "How do I design CRISPR guide RNAs for gene editing?",
        "expected_keywords": ["CRISPR", "guide RNA", "gRNA", "design"],
        "check_citations": True
    },
    {
        "query": "What are the steps for Western blot protocol?",
        "expected_keywords": ["Western blot", "protocol", "antibody", "transfer"],
        "check_citations": True
    },
    # Edge cases
    {
        "query": "Tell me about quantum computing",  # Off-topic query
        "expected_keywords": [],
        "check_no_answer": True
    },
    {
        "query": "",  # Empty query
        "expected_error": True
    },
    {
        "query": "a" * 1000,  # Very long query
        "expected_error": True
    },
    # Hallucination tests
    {
        "query": "What is the protocol for extracting DNA from unicorns?",
        "expected_keywords": [],
        "check_no_answer": True
    },
    {
        "query": "Explain the RNA extraction protocol developed by Dr. FakeName in 2030",
        "expected_keywords": [],
        "check_no_answer": True
    }
]

HYPOTHESIS_TESTS = [
    # Valid hypotheses
    {
        "question": "What if we could use CRISPR-Cas9 to edit RNA directly?",
        "use_advanced_model": False,
        "expected_keywords": ["CRISPR", "RNA", "editing", "Cas9", "limitations"]
    },
    {
        "question": "How might temperature affect RNA stability during extraction?",
        "use_advanced_model": False,
        "expected_keywords": ["temperature", "RNA", "stability", "extraction", "degradation"]
    },
    # Edge cases
    {
        "question": "",
        "use_advanced_model": False,
        "expected_error": True
    },
    # Hallucination prevention
    {
        "question": "What if unicorn horn extract could enhance PCR efficiency?",
        "use_advanced_model": False,
        "check_scientific_validity": True
    }
]

PROTOCOL_GENERATION_TESTS = [
    # Valid protocol requests
    {
        "requirements": "I need a protocol for RNA extraction from mammalian cells that can be completed in 2 hours using basic equipment",
        "base_protocol_id": None,
        "expected_sections": ["materials", "procedure", "safety", "troubleshooting"]
    },
    {
        "requirements": "Generate a CRISPR gene editing protocol for HEK293 cells suitable for beginners with limited budget",
        "base_protocol_id": None,
        "expected_sections": ["materials", "procedure", "timeline", "validation"]
    },
    # Edge cases
    {
        "requirements": "",
        "base_protocol_id": None,
        "expected_error": True
    },
    {
        "requirements": "Create a protocol for quantum teleportation of biological samples",  # Invalid experiment
        "base_protocol_id": None,
        "check_rejection": True
    }
]


class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "warnings": [],
            "timestamp": datetime.now().isoformat()
        }
    
    def test_rag_query(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test the RAG query endpoint"""
        endpoint = f"{self.base_url}/query/"
        
        try:
            response = requests.post(
                endpoint,
                headers=HEADERS,
                json={"query": test_case.get("query", "")},
                timeout=30
            )
            
            if test_case.get("expected_error"):
                if response.status_code >= 400:
                    return {"status": "pass", "message": "Expected error received"}
                else:
                    return {"status": "fail", "message": f"Expected error but got {response.status_code}"}
            
            if response.status_code != 200:
                return {"status": "fail", "message": f"Status code: {response.status_code}"}
            
            data = response.json()
            
            # Check response structure
            required_fields = ["answer", "sources", "confidence"]
            for field in required_fields:
                if field not in data:
                    return {"status": "fail", "message": f"Missing field: {field}"}
            
            # Check for hallucination indicators
            if test_case.get("check_no_answer"):
                if "I don't know" not in data["answer"] and "cannot answer" not in data["answer"]:
                    return {"status": "fail", "message": "Should have indicated inability to answer"}
            
            # Check citations
            if test_case.get("check_citations") and not data.get("sources"):
                return {"status": "fail", "message": "No citations provided"}
            
            # Check keywords
            answer_lower = data["answer"].lower()
            for keyword in test_case.get("expected_keywords", []):
                if keyword.lower() not in answer_lower:
                    return {"status": "warning", "message": f"Missing expected keyword: {keyword}"}
            
            # Check confidence score
            if data.get("confidence", 0) < 0.45 and not test_case.get("check_no_answer"):
                return {"status": "warning", "message": f"Low confidence: {data.get('confidence')}"}
            
            return {"status": "pass", "data": data}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def test_hypothesis_exploration(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test the hypothesis exploration endpoint"""
        endpoint = f"{self.base_url}/hypothesis/explore/"
        
        try:
            response = requests.post(
                endpoint,
                headers=HEADERS,
                json={
                    "question": test_case.get("question", ""),
                    "use_advanced_model": test_case.get("use_advanced_model", False)
                },
                timeout=30
            )
            
            if test_case.get("expected_error"):
                if response.status_code >= 400:
                    return {"status": "pass", "message": "Expected error received"}
                else:
                    return {"status": "fail", "message": f"Expected error but got {response.status_code}"}
            
            if response.status_code != 200:
                return {"status": "fail", "message": f"Status code: {response.status_code}"}
            
            data = response.json()
            
            # Check response structure - adjust based on actual response
            if "success" in data and not data["success"]:
                return {"status": "fail", "message": data.get("error", "Unknown error")}
            
            # Check for expected content in the response
            response_text = json.dumps(data).lower()
            
            # Check scientific validity
            if test_case.get("check_scientific_validity"):
                if any(word in response_text for word in ["unicorn", "magic", "impossible"]):
                    return {"status": "fail", "message": "Contains non-scientific content"}
            
            # Check keywords
            content = json.dumps(data).lower()
            for keyword in test_case.get("expected_keywords", []):
                if keyword.lower() not in content:
                    return {"status": "warning", "message": f"Missing expected keyword: {keyword}"}
            
            return {"status": "pass", "data": data}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def test_protocol_generation(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test the protocol generation endpoint"""
        endpoint = f"{self.base_url}/hypothesis/generate-protocol/"
        
        try:
            response = requests.post(
                endpoint,
                headers=HEADERS,
                json={
                    "requirements": test_case.get("requirements", ""),
                    "base_protocol_id": test_case.get("base_protocol_id")
                },
                timeout=30
            )
            
            if test_case.get("expected_error"):
                if response.status_code >= 400:
                    return {"status": "pass", "message": "Expected error received"}
                else:
                    return {"status": "fail", "message": f"Expected error but got {response.status_code}"}
            
            if test_case.get("check_rejection"):
                if response.status_code == 400 or (response.status_code == 200 and "cannot generate" in response.text):
                    return {"status": "pass", "message": "Invalid request properly rejected"}
                else:
                    return {"status": "fail", "message": "Should have rejected invalid experiment type"}
            
            if response.status_code != 200:
                return {"status": "fail", "message": f"Status code: {response.status_code}"}
            
            data = response.json()
            
            # Check response structure
            if "success" in data and not data["success"]:
                return {"status": "fail", "message": data.get("error", "Unknown error")}
            
            protocol_text = json.dumps(data).lower()
            
            # Check expected sections
            for section in test_case.get("expected_sections", []):
                if section not in protocol_text:
                    return {"status": "warning", "message": f"Missing expected section: {section}"}
            
            # Check for proper formatting
            if len(protocol_text) < 100:
                return {"status": "fail", "message": "Protocol too short"}
            
            return {"status": "pass", "data": data}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🧪 RNA Lab Navigator API Testing Suite")
        print("=" * 50)
        
        # Test RAG Query Endpoint
        print("\n📚 Testing RAG Query Endpoint...")
        for i, test in enumerate(RAG_QUERY_TESTS, 1):
            print(f"  Test {i}: {test.get('query', 'Error test')[:50]}...", end=" ")
            result = self.test_rag_query(test)
            self._process_result(result, test)
        
        # Test Hypothesis Exploration
        print("\n🔬 Testing Hypothesis Exploration Endpoint...")
        for i, test in enumerate(HYPOTHESIS_TESTS, 1):
            print(f"  Test {i}: {test.get('question', 'Error test')[:50]}...", end=" ")
            result = self.test_hypothesis_exploration(test)
            self._process_result(result, test)
        
        # Test Protocol Generation
        print("\n📋 Testing Protocol Generation Endpoint...")
        for i, test in enumerate(PROTOCOL_GENERATION_TESTS, 1):
            print(f"  Test {i}: {test.get('requirements', 'Error test')[:50]}...", end=" ")
            result = self.test_protocol_generation(test)
            self._process_result(result, test)
        
        # Print summary
        self._print_summary()
    
    def _process_result(self, result: Dict[str, Any], test_case: Dict[str, Any]):
        """Process test result and update counters"""
        self.results["total_tests"] += 1
        
        if result["status"] == "pass":
            self.results["passed"] += 1
            print("✅ PASS")
        elif result["status"] == "fail":
            self.results["failed"] += 1
            print("❌ FAIL")
            self.results["errors"].append({
                "test": test_case,
                "error": result.get("message", "Unknown error")
            })
        elif result["status"] == "warning":
            self.results["passed"] += 1
            print("⚠️  WARN")
            self.results["warnings"].append({
                "test": test_case,
                "warning": result.get("message", "Unknown warning")
            })
        else:  # error
            self.results["failed"] += 1
            print("💥 ERROR")
            self.results["errors"].append({
                "test": test_case,
                "error": result.get("message", "Unknown error")
            })
        
        # Print details for non-passing tests
        if result["status"] != "pass":
            print(f"     → {result.get('message', 'No message')}")
    
    def _print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print(f"  Total Tests: {self.results['total_tests']}")
        print(f"  ✅ Passed: {self.results['passed']}")
        print(f"  ❌ Failed: {self.results['failed']}")
        print(f"  ⚠️  Warnings: {len(self.results['warnings'])}")
        
        if self.results["errors"]:
            print("\n❌ Errors:")
            for error in self.results["errors"][:5]:  # Show first 5 errors
                print(f"  - {error['error']}")
        
        if self.results["warnings"]:
            print("\n⚠️  Warnings:")
            for warning in self.results["warnings"][:5]:  # Show first 5 warnings
                print(f"  - {warning['warning']}")
        
        # Save detailed results
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("\n💾 Detailed results saved to test_results.json")


def main():
    """Main test runner"""
    tester = APITester(BASE_URL)
    tester.run_all_tests()


if __name__ == "__main__":
    main()