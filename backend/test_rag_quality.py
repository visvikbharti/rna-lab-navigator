#!/usr/bin/env python
"""
Comprehensive RAG Quality Testing Script
Tests the RNA Lab Navigator with deep, critical questions
"""

import requests
import json
import time
from datetime import datetime

# API configuration
BASE_URL = "http://localhost:8000/api"
LOGIN_URL = f"{BASE_URL}/auth/login/"
QUERY_URL = f"{BASE_URL}/query/"

# Test credentials
USERNAME = "admin"
PASSWORD = "admin123"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

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
        print(f"{RED}Login failed: {response.text}{RESET}")
        return None

def test_query(query, token, expected_topics=None):
    """Test a single query and analyze the response"""
    print(f"\n{BLUE}Testing Query:{RESET} {query}")
    print(f"{BLUE}Expected Topics:{RESET} {expected_topics or 'General'}")
    
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
        
        # Extract key metrics
        answer = data.get('answer', '')
        sources = data.get('sources', [])
        confidence = data.get('confidence_score', 0)
        
        print(f"\n{GREEN}Response Time:{RESET} {elapsed_time:.2f} seconds")
        print(f"{GREEN}Confidence Score:{RESET} {confidence:.2%}")
        print(f"{GREEN}Number of Sources:{RESET} {len(sources)}")
        
        # Analyze answer quality
        word_count = len(answer.split())
        has_citations = any(source in answer for source in [s.get('title', '') for s in sources])
        
        print(f"{GREEN}Answer Length:{RESET} {word_count} words")
        print(f"{GREEN}Contains Citations:{RESET} {'Yes' if has_citations else 'No'}")
        
        # Show sources
        if sources:
            print(f"\n{YELLOW}Sources Used:{RESET}")
            for i, source in enumerate(sources[:5], 1):
                print(f"  {i}. {source.get('title', 'Unknown')} by {source.get('author', 'Unknown')} ({source.get('year', 'N/A')})")
        
        # Show answer preview
        print(f"\n{YELLOW}Answer Preview:{RESET}")
        preview = answer[:500] + "..." if len(answer) > 500 else answer
        print(preview)
        
        # Quality assessment
        quality_score = 0
        if confidence > 0.7:
            quality_score += 2
        elif confidence > 0.5:
            quality_score += 1
            
        if len(sources) >= 2:
            quality_score += 2
        elif len(sources) >= 1:
            quality_score += 1
            
        if word_count > 100:
            quality_score += 2
        elif word_count > 50:
            quality_score += 1
            
        if has_citations:
            quality_score += 1
            
        quality_rating = "Excellent" if quality_score >= 6 else "Good" if quality_score >= 4 else "Fair" if quality_score >= 2 else "Poor"
        print(f"\n{GREEN}Quality Rating:{RESET} {quality_rating} ({quality_score}/7)")
        
        return {
            "success": True,
            "time": elapsed_time,
            "confidence": confidence,
            "sources": len(sources),
            "quality": quality_rating,
            "quality_score": quality_score
        }
    else:
        print(f"{RED}Query failed:{RESET} {response.text}")
        return {
            "success": False,
            "time": elapsed_time,
            "error": response.text
        }

def main():
    """Run comprehensive RAG tests"""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}RNA Lab Navigator - RAG Quality Testing{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Login first
    print(f"\n{YELLOW}Logging in...{RESET}")
    token = login()
    if not token:
        return
    
    print(f"{GREEN}Login successful!{RESET}")
    
    # Define test queries - deep and critical
    test_queries = [
        {
            "query": "What are the specific molecular mechanisms by which ERBB4 regulates DNA repair pathways in the context of Rhythm Phutela's thesis findings?",
            "topics": ["ERBB4", "DNA repair", "thesis", "molecular mechanisms"]
        },
        {
            "query": "Compare and contrast the efficiency of NHEJ versus HDR repair mechanisms as documented in the lab's research, including quantitative data if available.",
            "topics": ["NHEJ", "HDR", "DNA repair", "comparison", "quantitative"]
        },
        {
            "query": "What are the specific steps and critical considerations for RNA extraction using Trizol method, particularly for samples with low RNA yield?",
            "topics": ["RNA extraction", "Trizol", "protocol", "low yield"]
        },
        {
            "query": "Explain the RAPID FnCas9 system's mechanism for COVID-19 detection, including its sensitivity, specificity, and advantages over RT-PCR.",
            "topics": ["RAPID", "FnCas9", "COVID-19", "detection", "sensitivity"]
        },
        {
            "query": "What are the documented limitations and potential artifacts in CRISPR-Cas9 genome editing experiments, and how does the lab address these challenges?",
            "topics": ["CRISPR", "limitations", "artifacts", "troubleshooting"]
        },
        {
            "query": "Describe the role of glial cells in MLC disease pathogenesis based on the lab's research, including any therapeutic targets identified.",
            "topics": ["MLC disease", "glial cells", "pathogenesis", "therapeutic targets"]
        },
        {
            "query": "What quality control metrics and validation steps are recommended for Western blot experiments in the lab's protocols?",
            "topics": ["Western blot", "quality control", "validation", "protocols"]
        },
        {
            "query": "How does the lab's research on RNA biology contribute to understanding neurodegenerative diseases? Provide specific examples from published work.",
            "topics": ["RNA biology", "neurodegeneration", "research contributions"]
        },
        {
            "query": "What are the key differences between the various CRISPR variants (Cas9, Cas12, Cas13) studied in the lab, and their specific applications?",
            "topics": ["CRISPR variants", "Cas9", "Cas12", "Cas13", "applications"]
        },
        {
            "query": "Synthesize the lab's findings on DNA damage response pathways and their implications for cancer therapy development.",
            "topics": ["DNA damage response", "cancer therapy", "synthesis", "implications"]
        }
    ]
    
    # Run tests
    results = []
    total_start = time.time()
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Test {i}/{len(test_queries)}{RESET}")
        result = test_query(test['query'], token, test['topics'])
        results.append(result)
        
        # Brief pause between queries to avoid overwhelming the server
        if i < len(test_queries):
            time.sleep(2)
    
    total_time = time.time() - total_start
    
    # Summary statistics
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\n{GREEN}Total Tests:{RESET} {len(results)}")
    print(f"{GREEN}Successful:{RESET} {len(successful)}")
    print(f"{RED}Failed:{RESET} {len(failed)}")
    
    if successful:
        avg_time = sum(r['time'] for r in successful) / len(successful)
        avg_confidence = sum(r['confidence'] for r in successful) / len(successful)
        avg_sources = sum(r['sources'] for r in successful) / len(successful)
        avg_quality_score = sum(r['quality_score'] for r in successful) / len(successful)
        
        print(f"\n{YELLOW}Performance Metrics:{RESET}")
        print(f"  Average Response Time: {avg_time:.2f} seconds")
        print(f"  Average Confidence: {avg_confidence:.2%}")
        print(f"  Average Sources: {avg_sources:.1f}")
        print(f"  Average Quality Score: {avg_quality_score:.1f}/7")
        
        # Quality distribution
        quality_dist = {}
        for r in successful:
            quality = r['quality']
            quality_dist[quality] = quality_dist.get(quality, 0) + 1
        
        print(f"\n{YELLOW}Quality Distribution:{RESET}")
        for quality, count in sorted(quality_dist.items()):
            print(f"  {quality}: {count} ({count/len(successful)*100:.1f}%)")
    
    print(f"\n{GREEN}Total Test Time:{RESET} {total_time:.2f} seconds")
    print(f"\n{BLUE}{'='*60}{RESET}")
    
    # Recommendations
    print(f"\n{YELLOW}Recommendations based on testing:{RESET}")
    
    if successful:
        if avg_time > 30:
            print(f"  {RED}⚠{RESET}  Response time is high ({avg_time:.1f}s). Consider optimizing vector search and disabling query preloading.")
        elif avg_time > 10:
            print(f"  {YELLOW}⚠{RESET}  Response time could be improved ({avg_time:.1f}s).")
        else:
            print(f"  {GREEN}✓{RESET} Response time is good ({avg_time:.1f}s).")
            
        if avg_confidence < 0.5:
            print(f"  {RED}⚠{RESET}  Low average confidence ({avg_confidence:.2%}). Consider improving document quality or chunking strategy.")
        elif avg_confidence < 0.7:
            print(f"  {YELLOW}⚠{RESET}  Moderate confidence levels ({avg_confidence:.2%}).")
        else:
            print(f"  {GREEN}✓{RESET} Good confidence levels ({avg_confidence:.2%}).")
            
        if avg_sources < 2:
            print(f"  {YELLOW}⚠{RESET}  Low source diversity. Consider expanding the document corpus.")
        else:
            print(f"  {GREEN}✓{RESET} Good source diversity ({avg_sources:.1f} sources per query).")

if __name__ == "__main__":
    main()