#!/usr/bin/env python
"""
Quick test to verify RAG is working in the Django server context
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings')
django.setup()

from api.search.real_rag import vector_store, perform_rag_query

print(f"Vector store has {len(vector_store.vectors)} vectors")

if len(vector_store.vectors) == 0:
    print("ERROR: Vector store is empty! Re-running thesis ingestion...")
    from ingest_real_thesis import main
    main()
else:
    print("Testing RAG query...")
    result = perform_rag_query("what is this thesis about", "all")
    print(f"Answer: {result['answer'][:100]}...")
    print(f"Confidence: {result['confidence_score']}")
    print(f"Sources: {len(result['sources'])}")