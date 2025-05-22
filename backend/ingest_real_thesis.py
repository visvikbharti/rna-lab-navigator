#!/usr/bin/env python
"""
Script to ingest the real thesis PDF into the simple vector store.
"""

import os
import sys
import django
import pdfplumber

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings')
django.setup()

from api.models import Document
from api.search.real_rag import vector_store
from api.ingestion.chunking_utils import chunk_thesis_by_chapter

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
        print(f"Error extracting text: {e}")
        return None
    return text

def main():
    # Path to the real thesis
    thesis_path = "../data/sample_docs/theses/2025_Phutela_Rhythm_PhD_Thesis.pdf"
    
    print(f"Ingesting real thesis: {thesis_path}")
    
    # Extract text from PDF
    print("Extracting text from PDF...")
    full_text = extract_text_from_pdf(thesis_path)
    
    if not full_text:
        print("Failed to extract text from PDF")
        return
    
    print(f"Extracted {len(full_text)} characters")
    
    # Create or update document in database
    doc, created = Document.objects.get_or_create(
        title="2025 Phutela Rhythm PhD Thesis - Real Content",
        author="Rhythm Phutela",
        doc_type="thesis",
        year=2025
    )
    
    if created:
        print("Created new document entry")
    else:
        print("Updated existing document entry")
    
    # Chunk the thesis by chapters
    print("Chunking thesis by chapters...")
    chunks = chunk_thesis_by_chapter(full_text)
    print(f"Generated {len(chunks)} chunks")
    
    # Add chunks to vector store
    print("Adding chunks to vector store...")
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
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(chunks)} chunks")
    
    print(f"Successfully ingested thesis with {len(chunks)} chunks!")
    print(f"Vector store now has {len(vector_store.vectors)} total vectors")

if __name__ == "__main__":
    main()