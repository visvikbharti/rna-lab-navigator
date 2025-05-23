#!/usr/bin/env python
"""
Quick API test to verify basic functionality
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def quick_test():
    print("🚀 Quick API Test")
    print("================")
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print("   ❌ Health check failed")
    except Exception as e:
        print(f"   💥 Error: {e}")
        print("\n❌ Server is not running. Please start it with:")
        print("   cd backend && python manage.py runserver")
        return
    
    # Test 2: Simple query
    print("\n2. Testing RAG query endpoint...")
    try:
        response = requests.post(
            f"{BASE_URL}/query/",
            json={"query": "What is RNA extraction?"},
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Query endpoint working")
            print(f"   Answer preview: {data.get('answer', '')[:100]}...")
            print(f"   Confidence: {data.get('confidence', 'N/A')}")
            print(f"   Sources: {len(data.get('sources', []))} found")
        else:
            print(f"   ❌ Query failed: {response.text[:200]}")
    except Exception as e:
        print(f"   💥 Error: {e}")
    
    # Test 3: Check new endpoints
    print("\n3. Checking new hypothesis endpoints...")
    
    # Hypothesis exploration
    try:
        response = requests.post(
            f"{BASE_URL}/hypothesis/explore/",
            json={
                "question": "What if we could use CRISPR to edit RNA directly?",
                "use_advanced_model": False
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("   ✅ Hypothesis exploration endpoint found")
        elif response.status_code == 404:
            print("   ⚠️  Hypothesis exploration endpoint not found - may need to implement")
        else:
            print(f"   ❌ Hypothesis endpoint error: {response.status_code}")
    except Exception as e:
        print(f"   💥 Error: {e}")
    
    # Protocol generation
    try:
        response = requests.post(
            f"{BASE_URL}/hypothesis/generate-protocol/",
            json={
                "requirements": "I need a protocol for RNA extraction from cells",
                "base_protocol_id": None
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("   ✅ Protocol generation endpoint found")
        elif response.status_code == 404:
            print("   ⚠️  Protocol generation endpoint not found - may need to implement")
        else:
            print(f"   ❌ Protocol endpoint error: {response.status_code}")
    except Exception as e:
        print(f"   💥 Error: {e}")
    
    print("\n✨ Quick test complete!")
    print("\nTo run full test suite:")
    print("  ./run_all_api_tests.sh")

if __name__ == "__main__":
    quick_test()