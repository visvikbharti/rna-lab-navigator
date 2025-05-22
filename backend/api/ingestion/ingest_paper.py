"""
Script to ingest research papers into the vector store.
Usage: python ingest_paper.py /path/paper.pdf "Author Name" 2023
"""

import argparse
import os
import sys
import django
import pdfplumber
import time
from pathlib import Path

# Add the parent directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(script_dir))
sys.path.append(backend_dir)

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rna_backend.settings")
django.setup()

# Now Django models and utils can be imported
from api.models import Document
from api.ingestion.chunking_utils import chunk_text
from api.ingestion.embeddings_utils import (
    create_schema_if_not_exists,
    add_document_chunk_to_weaviate
)


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return text
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""
    
    return text


def ingest_single_paper(pdf_path, author, year):
    """Ingest a single research paper."""
    print(f"Ingesting paper: {pdf_path}")
    print(f"Author: {author}, Year: {year}")
    
    # Extract text
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text.strip():
        print("Error: No text extracted from PDF")
        return False
    
    print(f"Extracted {len(text)} characters")
    
    # Create schema if needed
    try:
        create_schema_if_not_exists()
    except Exception as e:
        print(f"Error creating schema: {e}")
        return False
    
    # Create document record
    filename = os.path.basename(pdf_path)
    title = filename.replace('.pdf', '').replace('_', ' ')
    
    try:
        document = Document.objects.create(
            title=title,
            author=author,
            doc_type='paper',
            year=int(year),
            filename=filename,
            content=text[:10000],  # Store truncated content
        )
        print(f"Created document record: {document.title}")
    except Exception as e:
        print(f"Error creating document: {e}")
        return False
    
    # Chunk and ingest
    print("Chunking text...")
    chunks = chunk_text(text)
    print(f"Created {len(chunks)} chunks")
    
    # Add chunks to vector store
    print("Adding chunks to vector store...")
    for i, chunk in enumerate(chunks):
        try:
            add_document_chunk_to_weaviate(
                text=chunk,
                document_id=document.id,
                document_title=document.title,
                document_type=document.doc_type,
                author=document.author,
                year=document.year,
                chunk_index=i
            )
            if (i + 1) % 10 == 0:
                print(f"  Added {i + 1} chunks...")
        except Exception as e:
            print(f"Error adding chunk {i}: {e}")
            continue
    
    print(f"Successfully ingested paper: {title}")
    return True


def main():
    parser = argparse.ArgumentParser(description='Ingest a research paper PDF')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('author', help='Author name')
    parser.add_argument('year', help='Publication year')
    
    args = parser.parse_args()
    
    success = ingest_single_paper(args.pdf_path, args.author, args.year)
    if success:
        print("Paper ingestion completed successfully!")
    else:
        print("Paper ingestion failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()