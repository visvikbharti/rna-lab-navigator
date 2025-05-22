#!/usr/bin/env python
"""
Systematic script to ingest ALL documents from data/sample_docs/
"""

import os
import sys
import django
import pdfplumber
from pathlib import Path

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings')
django.setup()

from api.models import Document
from api.search.real_rag import vector_store
from api.ingestion.chunking_utils import chunk_text, chunk_thesis_by_chapter

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None
    return text

def ingest_papers():
    """Ingest research papers from papers/ directory."""
    papers_dir = Path("../data/sample_docs/papers")
    papers = list(papers_dir.glob("*.pdf"))
    print(f"Found {len(papers)} papers to ingest")
    
    for paper_path in papers[:5]:  # Limit to 5 papers for demo
        # Extract author and year from filename (format: YYYY_Author_Title.pdf)
        filename = paper_path.stem
        parts = filename.split('_')
        year = int(parts[0]) if parts[0].isdigit() else 2024
        author = parts[1] if len(parts) > 1 else "Unknown"
        title = ' '.join(parts[2:]) if len(parts) > 2 else filename
        
        print(f"Ingesting paper: {title} by {author} ({year})")
        
        # Extract text
        text = extract_text_from_pdf(paper_path)
        if not text:
            continue
            
        # Create document
        doc, created = Document.objects.get_or_create(
            title=title,
            author=author,
            doc_type="paper",
            year=year
        )
        
        # Chunk and add to vector store
        chunks = chunk_text(text)
        print(f"  Generated {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            metadata = {
                'title': doc.title,
                'author': doc.author,
                'doc_type': doc.doc_type,
                'year': doc.year,
                'document_id': doc.id,
                'chunk_index': i
            }
            vector_store.add_document(chunk, metadata)

def ingest_protocols():
    """Ingest protocols from community_protocols/ directory."""
    protocols_dir = Path("../data/sample_docs/community_protocols")
    protocols = list(protocols_dir.glob("*.pdf"))
    print(f"Found {len(protocols)} protocols to ingest")
    
    for protocol_path in protocols[:3]:  # Limit to 3 protocols
        filename = protocol_path.stem
        # Clean up protocol names
        title = filename.replace('_', ' ').replace('-', ' ').title()
        
        print(f"Ingesting protocol: {title}")
        
        # Extract text
        text = extract_text_from_pdf(protocol_path)
        if not text:
            continue
            
        # Create document
        doc, created = Document.objects.get_or_create(
            title=title,
            author="Lab Protocol",
            doc_type="protocol",
            year=2024
        )
        
        # Chunk and add to vector store
        chunks = chunk_text(text)
        print(f"  Generated {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            metadata = {
                'title': doc.title,
                'author': doc.author,
                'doc_type': doc.doc_type,
                'year': doc.year,
                'document_id': doc.id,
                'chunk_index': i
            }
            vector_store.add_document(chunk, metadata)

def main():
    print("🚀 Starting systematic document ingestion...")
    print(f"Current vector store size: {len(vector_store.vectors)} vectors")
    
    # Clear existing vectors to start fresh
    print("Clearing existing vectors...")
    vector_store.vectors = []
    vector_store.metadata = []
    
    # Ingest thesis (keep existing)
    print("Re-ingesting thesis...")
    from ingest_real_thesis import main as ingest_thesis
    ingest_thesis()
    
    # Ingest papers
    print("\nIngesting research papers...")
    ingest_papers()
    
    # Ingest protocols  
    print("\nIngesting protocols...")
    ingest_protocols()
    
    # Save to cache
    vector_store.save_to_cache()
    
    print(f"\n✅ Ingestion complete!")
    print(f"Final vector store size: {len(vector_store.vectors)} vectors")
    
    # Test diversity
    print("\n📊 Document type breakdown:")
    doc_types = {}
    for metadata in vector_store.metadata:
        doc_type = metadata['doc_type']
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
    
    for doc_type, count in doc_types.items():
        print(f"  {doc_type}: {count} chunks")

if __name__ == "__main__":
    main()