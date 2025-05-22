"""
Simplified views for the search functionality for demo purposes.
"""

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import random
import time

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def search_view(request):
    """
    Simplified search endpoint for demo purposes.
    """
    # Get search parameters
    query = request.GET.get('q', '') or request.data.get('query', '')
    doc_type = request.GET.get('type', '') or request.data.get('doc_type', '')
    
    # Simulate processing delay
    time.sleep(0.5)
    
    # Create mock search results
    results = []
    
    # Generate different results based on document type
    if doc_type == 'protocol':
        results = [
            {
                'id': '1',
                'title': 'RNA Extraction Protocol',
                'type': 'protocol',
                'author': 'Kumar et al.',
                'year': '2023',
                'snippet': 'This protocol describes how to extract RNA from tissue samples...',
                'score': 0.92,
            },
            {
                'id': '2',
                'title': 'qPCR Protocol Guide',
                'type': 'protocol',
                'author': 'Lab Protocols',
                'year': '2022',
                'snippet': 'Quantitative PCR protocol for gene expression analysis...',
                'score': 0.87,
            },
            {
                'id': '3',
                'title': 'Western Blot Protocol',
                'type': 'protocol',
                'author': 'Standard Protocols',
                'year': '2021',
                'snippet': 'Step-by-step guide for western blot analysis...',
                'score': 0.81,
            }
        ]
    elif doc_type == 'paper':
        results = [
            {
                'id': '1',
                'title': 'CRISPR Applications in RNA Biology',
                'type': 'paper',
                'author': 'Chakraborty et al.',
                'year': '2024',
                'snippet': 'Novel CRISPR applications for RNA editing and targeting...',
                'score': 0.94,
            },
            {
                'id': '2',
                'title': 'RNA Structure and Function',
                'type': 'paper',
                'author': 'Sharma et al.',
                'year': '2023',
                'snippet': 'Recent advances in understanding RNA tertiary structures...',
                'score': 0.89,
            },
            {
                'id': '3',
                'title': 'RNA-Protein Interactions',
                'type': 'paper',
                'author': 'Agarwal et al.',
                'year': '2022',
                'snippet': 'Comprehensive review of RNA-protein binding mechanisms...',
                'score': 0.85,
            }
        ]
    elif doc_type == 'thesis':
        results = [
            {
                'id': '1',
                'title': 'Rhythm PhD Thesis on RNA Dynamics',
                'type': 'thesis',
                'author': 'Phutela',
                'year': '2025',
                'snippet': 'Doctoral thesis on temporal dynamics of RNA processing...',
                'score': 0.96,
            }
        ]
    else:
        # Mixed results
        results = [
            {
                'id': '1',
                'title': 'RNA Extraction Protocol',
                'type': 'protocol',
                'author': 'Kumar et al.',
                'year': '2023',
                'snippet': 'This protocol describes how to extract RNA from tissue samples...',
                'score': 0.92,
            },
            {
                'id': '2',
                'title': 'CRISPR Applications in RNA Biology',
                'type': 'paper',
                'author': 'Chakraborty et al.',
                'year': '2024',
                'snippet': 'Novel CRISPR applications for RNA editing and targeting...',
                'score': 0.94,
            },
            {
                'id': '3',
                'title': 'Rhythm PhD Thesis on RNA Dynamics',
                'type': 'thesis',
                'author': 'Phutela',
                'year': '2025',
                'snippet': 'Doctoral thesis on temporal dynamics of RNA processing...',
                'score': 0.96,
            }
        ]
    
    # Apply query-specific filtering
    if query:
        # Special case for specific queries that users might try during demo
        if 'cleavage' in query.lower() or 'in vitro' in query.lower():
            # Add specific result for in vitro cleavage assay queries
            results = [
                {
                    'id': '4',
                    'title': 'In Vitro RNA Cleavage Assay Protocol',
                    'type': 'protocol',
                    'author': 'Kumar et al.',
                    'year': '2023',
                    'snippet': 'This protocol describes specific methods for in vitro RNA cleavage assays using purified enzymes. The assay is routinely used to evaluate ribozyme activity and RNA processing mechanisms in the lab.',
                    'score': 0.97,
                },
                {
                    'id': '5',
                    'title': 'CRISPR Nuclease Cleavage Activity Assessment',
                    'type': 'protocol',
                    'author': 'Chakraborty et al.',
                    'year': '2023',
                    'snippet': 'Protocol for evaluating the RNA cleavage activity of CRISPR nucleases in vitro, including Cas9, Cas12, and Cas13 variants.',
                    'score': 0.94,
                },
                {
                    'id': '6',
                    'title': 'Biochemical Analysis of RNA Processing',
                    'type': 'paper',
                    'author': 'Sharma et al.',
                    'year': '2024',
                    'snippet': 'A detailed investigation of in vitro cleavage assays for studying RNA processing events, with a focus on methodology and applications in RNA biology.',
                    'score': 0.92,
                }
            ]
            
            if doc_type and doc_type != 'all':
                # Filter by doc_type if specified
                results = [r for r in results if r['type'] == doc_type]
                
        else:
            # Standard filtering for other queries
            filtered_results = []
            query_lower = query.lower()
            for r in results:
                if (query_lower in r['title'].lower() or 
                    query_lower in r['snippet'].lower() or
                    query_lower in r['author'].lower()):
                    filtered_results.append(r)
            
            # If no results match the query, return some random ones
            if not filtered_results and results:
                filtered_results = random.sample(results, min(2, len(results)))
            
            results = filtered_results
    
    return JsonResponse({
        'query': query,
        'doc_type': doc_type,
        'results': results,
        'total': len(results),
        'processing_time': 0.5
    })