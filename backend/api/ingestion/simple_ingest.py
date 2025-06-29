"""
Simple ingestion script for the RNA Lab Navigator using Weaviate v4.
"""

import argparse
import os
import sys
import django
import pdfplumber
from pathlib import Path

# Add the parent directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(script_dir))
sys.path.append(backend_dir)

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rna_backend.settings")
django.setup()

from api.models import Document
from api.ingestion.chunking_utils import chunk_text
from django.conf import settings
import openai
import weaviate


def get_simple_weaviate_client():
    """Get a simple Weaviate client."""
    # Pass OpenAI API key to Weaviate
    additional_headers = {
        "X-OpenAI-Api-Key": settings.OPENAI_API_KEY
    }
    client = weaviate.Client(
        url="http://localhost:8080",
        additional_headers=additional_headers
    )
    return client


def create_simple_schema(client):
    """Create a simple schema for documents."""
    try:
        # Check if class exists
        schema = client.schema.get()
        existing_classes = [c['class'] for c in schema.get('classes', [])]
        
        if "Document" in existing_classes:
            print("Document class already exists")
            return
        
        # Create class
        document_class = {
            "class": "Document",
            "description": "RNA Lab document chunks",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "ada",
                    "modelVersion": "002", 
                    "type": "text"
                }
            },
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Text content of the chunk"
                },
                {
                    "name": "title",
                    "dataType": ["text"],
                    "description": "Document title"
                },
                {
                    "name": "author",
                    "dataType": ["text"],
                    "description": "Document author"
                },
                {
                    "name": "doc_type",
                    "dataType": ["text"],
                    "description": "Type of document"
                },
                {
                    "name": "year",
                    "dataType": ["int"],
                    "description": "Publication year"
                },
                {
                    "name": "document_id",
                    "dataType": ["int"],
                    "description": "Database document ID"
                },
                {
                    "name": "chunk_index",
                    "dataType": ["int"],
                    "description": "Chunk index within document"
                }
            ]
        }
        
        client.schema.create_class(document_class)
        print("Created Document class")
    except Exception as e:
        print(f"Error creating schema: {e}")


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""
    return text


def ingest_document(pdf_path, author, year, doc_type="paper"):
    """Ingest a document into the system."""
    print(f"Ingesting {doc_type}: {pdf_path}")
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        print("No text extracted")
        return False
    
    print(f"Extracted {len(text)} characters")
    
    # Create Django record
    filename = os.path.basename(pdf_path)
    title = filename.replace('.pdf', '').replace('_', ' ')
    
    try:
        document = Document.objects.create(
            title=title,
            author=author,
            doc_type=doc_type,
            year=int(year),
        )
        print(f"Created document: {document.title}")
    except Exception as e:
        print(f"Error creating document: {e}")
        return False
    
    # Set up OpenAI
    openai.api_key = settings.OPENAI_API_KEY
    
    # Get Weaviate client
    client = get_simple_weaviate_client()
    
    # Create schema if needed
    create_simple_schema(client)
    
    # Chunk text
    chunks = chunk_text(text)
    print(f"Created {len(chunks)} chunks")
    
    # Add to Weaviate
    with client.batch() as batch:
        for i, chunk in enumerate(chunks):
            try:
                # Create object
                data_object = {
                    "content": chunk,
                    "title": document.title,
                    "author": document.author,
                    "doc_type": document.doc_type,
                    "year": document.year,
                    "document_id": document.id,
                    "chunk_index": i
                }
                
                batch.add_data_object(
                    data_object=data_object,
                    class_name="Document"
                )
                
                if (i + 1) % 5 == 0:
                    print(f"  Added {i + 1} chunks...")
                    
            except Exception as e:
                print(f"Error adding chunk {i}: {e}")
                continue
    
    print(f"Successfully ingested: {title}")
    return True


def main():
    parser = argparse.ArgumentParser(description='Ingest documents into RNA Lab Navigator')
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('author', help='Author name')
    parser.add_argument('year', help='Publication year')
    parser.add_argument('--type', default='paper', choices=['paper', 'thesis', 'protocol'], 
                       help='Document type')
    
    args = parser.parse_args()
    
    success = ingest_document(args.pdf_path, args.author, args.year, args.type)
    if success:
        print("Ingestion completed!")
    else:
        print("Ingestion failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()