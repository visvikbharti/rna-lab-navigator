#!/usr/bin/env python3
"""
Quick script to ingest a few sample documents
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

def quick_ingest():
    """Ingest just a few sample documents quickly."""
    
    # Base path for sample documents
    sample_dir = Path(backend_dir).parent / "data" / "sample_docs"
    
    # Select a few documents to ingest
    documents_to_ingest = [
        # Papers
        ("papers/2021_Gulati_TrendsGenet_LowCost_CRISPR_Dx_RLS.pdf", "Gulati", 2021, "paper"),
        ("papers/2025_Sharma_bioRxiv_MLC1_iPSC_Vacuolation.pdf", "Sharma", 2025, "paper"),
        # Protocols
        ("community_protocols/RTPCR.pdf", "Lab Protocol", 2024, "protocol"),
        ("community_protocols/general-western-blot-protocol.pdf", "Lab Protocol", 2024, "protocol"),
        ("community_protocols/protocol_RNAextraction.pdf", "Lab Protocol", 2024, "protocol"),
    ]
    
    success = 0
    total = len(documents_to_ingest)
    
    for relative_path, author, year, doc_type in documents_to_ingest:
        pdf_path = sample_dir / relative_path
        if pdf_path.exists():
            print(f"\n{'='*60}")
            print(f"Processing: {relative_path}")
            print(f"{'='*60}")
            
            try:
                if ingest_document(str(pdf_path), author, year, doc_type):
                    success += 1
                    print("✓ SUCCESS")
                else:
                    print("✗ FAILED")
            except Exception as e:
                print(f"✗ ERROR: {e}")
        else:
            print(f"\n✗ File not found: {relative_path}")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"Successfully ingested: {success}/{total} documents")
    print(f"{'='*60}")

if __name__ == "__main__":
    quick_ingest()