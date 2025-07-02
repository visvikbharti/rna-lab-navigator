#!/usr/bin/env python3
"""
Script to check all documents indexed in Weaviate
"""

import weaviate
import json
from collections import defaultdict
import os
import sys

# Add parent directory to path to import Django settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings')

def check_weaviate_documents():
    """Query Weaviate to list all indexed documents."""
    
    # Connect to Weaviate
    client = weaviate.Client("http://localhost:8080")
    
    # Check if Document class exists
    try:
        schema = client.schema.get()
        print("Weaviate Schema:")
        print(json.dumps(schema, indent=2))
        print("\n" + "="*80 + "\n")
    except Exception as e:
        print(f"Error getting schema: {e}")
        return
    
    # Query all documents
    try:
        # Get all documents without any filter
        result = client.query.get(
            "Document",
            ["title", "author", "doc_type", "year", "chapter", "content"]
        ).with_limit(1000).do()  # Get up to 1000 documents
        
        if 'errors' in result:
            print(f"Query errors: {result['errors']}")
            return
            
        documents = result.get('data', {}).get('Get', {}).get('Document', [])
        
        print(f"Total documents indexed: {len(documents)}\n")
        
        # Categorize documents
        doc_types = defaultdict(list)
        unique_docs = {}
        
        for doc in documents:
            doc_type = doc.get('doc_type', 'unknown')
            title = doc.get('title', 'Unknown')
            author = doc.get('author', 'Unknown')
            year = doc.get('year', '')
            chapter = doc.get('chapter', '')
            
            # Create unique key for document
            doc_key = f"{title}_{author}_{year}"
            
            # Store document info
            if doc_key not in unique_docs:
                unique_docs[doc_key] = {
                    'title': title,
                    'author': author,
                    'year': year,
                    'type': doc_type,
                    'chapters': []
                }
            
            if chapter:
                unique_docs[doc_key]['chapters'].append(chapter)
            
            doc_types[doc_type].append(doc)
        
        # Print summary by document type
        print("Documents by Type:")
        print("-" * 50)
        for doc_type, docs in doc_types.items():
            print(f"{doc_type.upper()}: {len(docs)} chunks")
            
        print("\n" + "="*80 + "\n")
        
        # Print unique documents
        print("Unique Documents:")
        print("-" * 50)
        
        # Group by type
        docs_by_type = defaultdict(list)
        for doc_info in unique_docs.values():
            docs_by_type[doc_info['type']].append(doc_info)
        
        for doc_type, docs in docs_by_type.items():
            print(f"\n{doc_type.upper()} ({len(docs)} documents):")
            for doc in docs:
                print(f"  - Title: {doc['title']}")
                print(f"    Author: {doc['author']}")
                if doc['year']:
                    print(f"    Year: {doc['year']}")
                if doc['chapters']:
                    print(f"    Chapters: {', '.join(sorted(set(doc['chapters'])))}")
                print()
        
        # Check for sample documents
        print("\n" + "="*80 + "\n")
        print("Sample Documents Check:")
        print("-" * 50)
        
        sample_keywords = ['sample', 'test', 'demo', 'example']
        sample_docs = []
        
        for doc in documents:
            title = doc.get('title', '').lower()
            author = doc.get('author', '').lower()
            content = doc.get('content', '').lower()[:200]  # Check first 200 chars
            
            if any(keyword in title or keyword in author for keyword in sample_keywords):
                sample_docs.append({
                    'title': doc.get('title'),
                    'author': doc.get('author'),
                    'type': doc.get('doc_type')
                })
        
        if sample_docs:
            print(f"Found {len(sample_docs)} potential sample documents:")
            for doc in sample_docs:
                print(f"  - {doc['title']} by {doc['author']} ({doc['type']})")
        else:
            print("No obvious sample documents found.")
            
    except Exception as e:
        print(f"Error querying documents: {e}")
        import traceback
        traceback.print_exc()

def check_sample_directory():
    """Check what documents are available in the sample directory."""
    print("\n" + "="*80 + "\n")
    print("Sample Documents Directory Check:")
    print("-" * 50)
    
    sample_dir = "/Users/vishalbharti/Downloads/rna-lab-navigator/data/sample_docs"
    
    if os.path.exists(sample_dir):
        for root, dirs, files in os.walk(sample_dir):
            level = root.replace(sample_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            
            sub_indent = ' ' * 2 * (level + 1)
            for file in files:
                if not file.startswith('.'):  # Skip hidden files
                    size = os.path.getsize(os.path.join(root, file))
                    size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/1024/1024:.1f}MB"
                    print(f"{sub_indent}{file} ({size_str})")
    else:
        print(f"Sample directory not found at: {sample_dir}")

if __name__ == "__main__":
    print("Checking Weaviate Documents")
    print("="*80)
    check_weaviate_documents()
    check_sample_directory()