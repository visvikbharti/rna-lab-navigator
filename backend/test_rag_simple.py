#!/usr/bin/env python
"""
Simple RAG Testing Script - Tests individual queries
"""

import requests
import json
import time

# API configuration
BASE_URL = "http://localhost:8000/api"
LOGIN_URL = f"{BASE_URL}/auth/login/"
QUERY_URL = f"{BASE_URL}/query/"

# Test credentials
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    """Login and get auth token"""
    response = requests.post(LOGIN_URL, json={
        "username": USERNAME,
        "password": PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get('access')
    else:
        print(f"Login failed: {response.text}")
        return None

def test_single_query(query, token):
    """Test a single query"""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(QUERY_URL, 
                           json={"query": query},
                           headers=headers)
    
    elapsed_time = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\nResponse Time: {elapsed_time:.2f} seconds")
        print(f"Confidence Score: {data.get('confidence_score', 0):.2%}")
        print(f"Number of Sources: {len(data.get('sources', []))}")
        
        # Show sources
        sources = data.get('sources', [])
        if sources:
            print(f"\nSources:")
            for i, source in enumerate(sources, 1):
                print(f"  {i}. {source.get('title', 'Unknown')} by {source.get('author', 'Unknown')} ({source.get('year', 'N/A')})")
        
        # Show answer (first 500 chars)
        answer = data.get('answer', '')
        print(f"\nAnswer Preview:")
        print(answer[:500] + "..." if len(answer) > 500 else answer)
        
        return True
    else:
        print(f"Query failed: {response.text}")
        return False

def main():
    """Run simple RAG tests"""
    print("RNA Lab Navigator - Simple RAG Testing")
    
    # Login first
    print("\nLogging in...")
    token = login()
    if not token:
        return
    
    print("Login successful!")
    
    # Test queries one by one
    test_queries = [
        "What is CRISPR and how does it work?",
        "Tell me about ERBB4's role in DNA repair from Rhythm Phutela's thesis",
        "What is the protocol for RNA extraction using Trizol?",
        "Explain the RAPID FnCas9 system for COVID detection",
        "What are the key findings about MLC disease from the lab's research?"
    ]
    
    for query in test_queries:
        try:
            test_single_query(query, token)
            time.sleep(2)  # Brief pause between queries
        except Exception as e:
            print(f"Error testing query: {e}")
            continue
    
    print("\n" + "="*60)
    print("Testing complete!")

if __name__ == "__main__":
    main()