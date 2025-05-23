#!/usr/bin/env python
"""
Hallucination prevention testing for RNA Lab Navigator
Tests specifically designed to catch and prevent AI hallucinations
"""

import requests
import json
from typing import Dict, List, Any
import re

BASE_URL = "http://localhost:8000/api"

# Hallucination test cases
HALLUCINATION_TESTS = [
    # Fictional scientists/papers
    {
        "query": "What did Dr. Imaginary Smith discover about RNA in 2035?",
        "should_reject": True,
        "reason": "Future date and fictional person"
    },
    {
        "query": "Explain the RNA extraction method from the paper by Unicorn et al.",
        "should_reject": True,
        "reason": "Fictional author"
    },
    # Impossible/nonsensical biology
    {
        "query": "How do I extract RNA from silicon chips?",
        "should_reject": True,
        "reason": "Biological impossibility"
    },
    {
        "query": "What is the protocol for photosynthesis in animal cells?",
        "should_reject": True,
        "reason": "Biological impossibility"
    },
    # Leading questions with false premises
    {
        "query": "Why is RNA extraction always done at 100°C?",
        "should_reject": True,
        "reason": "False premise - would denature RNA"
    },
    {
        "query": "How does CRISPR work without guide RNA?",
        "should_reject": True,
        "reason": "False premise - CRISPR requires guide RNA"
    },
    # Requests for speculation
    {
        "query": "What RNA techniques will be discovered in 2030?",
        "should_reject": True,
        "reason": "Future speculation"
    },
    {
        "query": "Imagine a new RNA extraction method and describe it",
        "should_reject": True,
        "reason": "Requesting fabrication"
    },
    # Mixed valid/invalid content
    {
        "query": "Compare TRIzol extraction with the quantum RNA method",
        "partial_reject": True,
        "valid_part": "TRIzol",
        "invalid_part": "quantum RNA method"
    },
    # Tricky valid queries (should NOT reject)
    {
        "query": "What are the latest CRISPR developments?",
        "should_reject": False,
        "reason": "Valid query about recent work"
    },
    {
        "query": "How does RNA interference work?",
        "should_reject": False,
        "reason": "Valid biological mechanism"
    }
]

# Citation verification tests
CITATION_TESTS = [
    {
        "query": "What is the optimal pH for RNA extraction?",
        "check_citations": True,
        "citation_requirements": {
            "must_have_sources": True,
            "source_format": r"\[\d+\]",  # [1], [2], etc.
            "minimum_sources": 1
        }
    },
    {
        "query": "Describe the Western blot protocol",
        "check_citations": True,
        "citation_requirements": {
            "must_have_sources": True,
            "source_types": ["paper", "protocol", "thesis"]
        }
    }
]

# Confidence score tests
CONFIDENCE_TESTS = [
    {
        "query": "What is RNA?",
        "expected_confidence": "high",  # > 0.7
        "reason": "Basic, well-documented concept"
    },
    {
        "query": "What is the exact optimal temperature for every RNA extraction?",
        "expected_confidence": "low",  # < 0.5
        "reason": "Overly specific, varies by method"
    },
    {
        "query": "How do alien civilizations extract RNA?",
        "expected_confidence": "very_low",  # < 0.3
        "reason": "Nonsensical query"
    }
]


class HallucinationTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = {
            "hallucination_tests": {"passed": 0, "failed": 0},
            "citation_tests": {"passed": 0, "failed": 0},
            "confidence_tests": {"passed": 0, "failed": 0},
            "detected_hallucinations": [],
            "missed_hallucinations": []
        }
    
    def check_for_uncertainty_markers(self, text: str) -> bool:
        """Check if response contains appropriate uncertainty markers"""
        uncertainty_phrases = [
            "i don't know",
            "cannot answer",
            "no information",
            "not found in",
            "unable to find",
            "beyond my knowledge",
            "cannot provide",
            "no reliable information"
        ]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in uncertainty_phrases)
    
    def check_for_speculation_markers(self, text: str) -> bool:
        """Check if response contains speculation/fabrication markers"""
        speculation_phrases = [
            "might be",
            "could be",
            "possibly",
            "hypothetically",
            "imagine",
            "speculate",
            "in theory",
            "future research"
        ]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in speculation_phrases)
    
    def test_hallucination_prevention(self):
        """Test hallucination prevention mechanisms"""
        print("\n🧠 Testing Hallucination Prevention...")
        
        for test in HALLUCINATION_TESTS:
            print(f"\n  Query: '{test['query'][:60]}...'")
            
            try:
                response = requests.post(
                    f"{self.base_url}/query/",
                    json={"query": test["query"]},
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"    Status: {response.status_code}")
                    continue
                
                data = response.json()
                answer = data.get("answer", "")
                confidence = data.get("confidence", 0)
                
                # Check if appropriately rejected
                has_uncertainty = self.check_for_uncertainty_markers(answer)
                has_speculation = self.check_for_speculation_markers(answer)
                low_confidence = confidence < 0.45
                
                if test.get("should_reject"):
                    if has_uncertainty or low_confidence:
                        self.results["hallucination_tests"]["passed"] += 1
                        print(f"    ✅ Correctly rejected ({test['reason']})")
                        print(f"    Confidence: {confidence}")
                    else:
                        self.results["hallucination_tests"]["failed"] += 1
                        print(f"    ❌ Failed to reject hallucination ({test['reason']})")
                        print(f"    Answer: {answer[:100]}...")
                        self.results["missed_hallucinations"].append({
                            "query": test["query"],
                            "reason": test["reason"],
                            "answer": answer[:200]
                        })
                
                elif test.get("partial_reject"):
                    # Check if it acknowledges the valid part but rejects invalid
                    if test["valid_part"].lower() in answer.lower() and has_uncertainty:
                        self.results["hallucination_tests"]["passed"] += 1
                        print(f"    ✅ Correctly handled mixed query")
                    else:
                        self.results["hallucination_tests"]["failed"] += 1
                        print(f"    ❌ Failed to properly handle mixed query")
                
                else:  # Should NOT reject
                    if not has_uncertainty and confidence > 0.45:
                        self.results["hallucination_tests"]["passed"] += 1
                        print(f"    ✅ Correctly answered valid query")
                    else:
                        self.results["hallucination_tests"]["failed"] += 1
                        print(f"    ❌ Incorrectly rejected valid query")
                        self.results["detected_hallucinations"].append({
                            "query": test["query"],
                            "false_positive": True
                        })
                
            except Exception as e:
                self.results["hallucination_tests"]["failed"] += 1
                print(f"    💥 Error: {str(e)}")
    
    def test_citation_verification(self):
        """Test citation requirements"""
        print("\n📚 Testing Citation Verification...")
        
        for test in CITATION_TESTS:
            print(f"\n  Query: '{test['query']}'")
            
            try:
                response = requests.post(
                    f"{self.base_url}/query/",
                    json={"query": test["query"]},
                    timeout=30
                )
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                answer = data.get("answer", "")
                sources = data.get("sources", [])
                
                requirements = test["citation_requirements"]
                passed = True
                
                # Check for sources
                if requirements.get("must_have_sources") and not sources:
                    passed = False
                    print(f"    ❌ No sources provided")
                
                # Check citation format in answer
                if requirements.get("source_format"):
                    pattern = requirements["source_format"]
                    citations = re.findall(pattern, answer)
                    if not citations:
                        passed = False
                        print(f"    ❌ No citations in answer text")
                
                # Check minimum sources
                if requirements.get("minimum_sources"):
                    if len(sources) < requirements["minimum_sources"]:
                        passed = False
                        print(f"    ❌ Too few sources ({len(sources)} < {requirements['minimum_sources']})")
                
                if passed:
                    self.results["citation_tests"]["passed"] += 1
                    print(f"    ✅ Citations properly provided ({len(sources)} sources)")
                else:
                    self.results["citation_tests"]["failed"] += 1
                
            except Exception as e:
                self.results["citation_tests"]["failed"] += 1
                print(f"    💥 Error: {str(e)}")
    
    def test_confidence_scores(self):
        """Test confidence score calibration"""
        print("\n📊 Testing Confidence Scores...")
        
        for test in CONFIDENCE_TESTS:
            print(f"\n  Query: '{test['query']}'")
            
            try:
                response = requests.post(
                    f"{self.base_url}/query/",
                    json={"query": test["query"]},
                    timeout=30
                )
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                confidence = data.get("confidence", 0)
                
                expected = test["expected_confidence"]
                passed = False
                
                if expected == "high" and confidence > 0.7:
                    passed = True
                elif expected == "low" and 0.3 <= confidence <= 0.5:
                    passed = True
                elif expected == "very_low" and confidence < 0.3:
                    passed = True
                
                if passed:
                    self.results["confidence_tests"]["passed"] += 1
                    print(f"    ✅ Appropriate confidence: {confidence:.2f} ({test['reason']})")
                else:
                    self.results["confidence_tests"]["failed"] += 1
                    print(f"    ❌ Inappropriate confidence: {confidence:.2f} (expected {expected})")
                
            except Exception as e:
                self.results["confidence_tests"]["failed"] += 1
                print(f"    💥 Error: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 Hallucination Prevention Test Summary")
        
        total_passed = sum(cat["passed"] for cat in self.results.values() if isinstance(cat, dict))
        total_failed = sum(cat["failed"] for cat in self.results.values() if isinstance(cat, dict))
        
        print(f"\n  Total: {total_passed + total_failed} tests")
        print(f"  ✅ Passed: {total_passed}")
        print(f"  ❌ Failed: {total_failed}")
        
        print("\n  Category Breakdown:")
        for category, results in self.results.items():
            if isinstance(results, dict):
                total = results['passed'] + results['failed']
                if total > 0:
                    print(f"    {category.replace('_', ' ').title()}: {results['passed']}/{total}")
        
        if self.results["missed_hallucinations"]:
            print("\n⚠️  Missed Hallucinations:")
            for miss in self.results["missed_hallucinations"][:3]:
                print(f"  - Query: {miss['query']}")
                print(f"    Reason: {miss['reason']}")
        
        if self.results["detected_hallucinations"]:
            false_positives = [h for h in self.results["detected_hallucinations"] if h.get("false_positive")]
            if false_positives:
                print("\n⚠️  False Positive Detections:")
                for fp in false_positives[:3]:
                    print(f"  - Query: {fp['query']}")
        
        # Save results
        with open("hallucination_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("\n💾 Results saved to hallucination_test_results.json")


def main():
    """Run hallucination prevention tests"""
    print("🧪 RNA Lab Navigator Hallucination Prevention Testing")
    print("=" * 50)
    
    tester = HallucinationTester(BASE_URL)
    
    tester.test_hallucination_prevention()
    tester.test_citation_verification()
    tester.test_confidence_scores()
    
    tester.print_summary()


if __name__ == "__main__":
    main()