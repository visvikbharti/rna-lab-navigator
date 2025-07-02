#!/usr/bin/env python3
"""
Script to ingest sample documents from data/sample_docs directory
"""

import os
import sys
import django
from pathlib import Path

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rna_backend.settings")
django.setup()

from api.ingestion.simple_ingest import ingest_document

def ingest_all_samples():
    """Ingest all sample documents."""
    
    # Base path for sample documents
    sample_dir = Path(backend_dir).parent / "data" / "sample_docs"
    
    # Track ingestion stats
    total = 0
    success = 0
    
    # Ingest papers
    papers_dir = sample_dir / "papers"
    if papers_dir.exists():
        print("\n=== Ingesting Research Papers ===")
        for pdf_file in papers_dir.glob("*.pdf"):
            total += 1
            filename = pdf_file.name
            
            # Parse filename format: YYYY_Author_Journal_Title.pdf
            parts = filename.split('_')
            if len(parts) >= 2:
                try:
                    year = int(parts[0])
                    author = parts[1]
                    
                    print(f"\nProcessing: {filename}")
                    if ingest_document(str(pdf_file), author, year, "paper"):
                        success += 1
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
    
    # Ingest protocols
    protocols_dir = sample_dir / "community_protocols"
    if protocols_dir.exists():
        print("\n=== Ingesting Protocols ===")
        for pdf_file in protocols_dir.glob("*.pdf"):
            total += 1
            filename = pdf_file.name
            
            print(f"\nProcessing: {filename}")
            # Use filename as title, "Lab Protocol" as author
            if ingest_document(str(pdf_file), "Lab Protocol", 2024, "protocol"):
                success += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Ingestion Summary:")
    print(f"Total documents: {total}")
    print(f"Successfully ingested: {success}")
    print(f"Failed: {total - success}")
    print(f"{'='*50}")

if __name__ == "__main__":
    ingest_all_samples()