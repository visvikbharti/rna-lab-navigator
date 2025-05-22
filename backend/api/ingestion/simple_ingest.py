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
    client = weaviate.connect_to_local(host="localhost", port=8080)
    return client


def create_simple_schema(client):
    """Create a simple schema for documents."""
    try:
        # Check if collection exists
        if client.collections.exists("Document"):
            print("Document collection already exists")
            return
        
        # Create collection
        client.collections.create(
            name="Document",
            description="RNA Lab document chunks",
            vectorizer_config=weaviate.classes.config.Configure.Vectorizer.text2vec_openai(
                model="text-embedding-ada-002"
            ),
            properties=[
                weaviate.classes.config.Property(
                    name="content",
                    data_type=weaviate.classes.config.DataType.TEXT,
                    description="Text content of the chunk"
                ),
                weaviate.classes.config.Property(
                    name="title",
                    data_type=weaviate.classes.config.DataType.TEXT,
                    description="Document title"
                ),
                weaviate.classes.config.Property(
                    name="author",
                    data_type=weaviate.classes.config.DataType.TEXT,
                    description="Document author"
                ),
                weaviate.classes.config.Property(
                    name="doc_type",
                    data_type=weaviate.classes.config.DataType.TEXT,
                    description="Type of document"
                ),
                weaviate.classes.config.Property(
                    name="year",
                    data_type=weaviate.classes.config.DataType.INT,
                    description="Publication year"
                ),
                weaviate.classes.config.Property(
                    name="document_id",
                    data_type=weaviate.classes.config.DataType.INT,
                    description="Database document ID"
                ),
                weaviate.classes.config.Property(
                    name="chunk_index",
                    data_type=weaviate.classes.config.DataType.INT,
                    description="Chunk index within document"
                )
            ]
        )
        print("Created Document collection")
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
    collection = client.collections.get("Document")
    
    for i, chunk in enumerate(chunks):
        try:
            # Create object
            collection.data.insert(
                properties={
                    "content": chunk,
                    "title": document.title,
                    "author": document.author,
                    "doc_type": document.doc_type,
                    "year": document.year,
                    "document_id": document.id,
                    "chunk_index": i
                }
            )
            
            if (i + 1) % 5 == 0:
                print(f"  Added {i + 1} chunks...")
                
        except Exception as e:
            print(f"Error adding chunk {i}: {e}")
            continue
    
    client.close()
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