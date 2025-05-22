"""
Script to ingest a thesis PDF into the vector store.
Usage: python ingest_thesis.py /path/Thesis.pdf "Author Name" 2023 [--extract-figures]
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
from api.ingestion.chunking_utils import chunk_text, split_by_chapter
from api.ingestion.embeddings_utils import (
    create_schema_if_not_exists,
    add_document_chunk_to_weaviate
)
from api.ingestion.figure_extractor import extract_figures_from_pdf


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text
    """
    text = ""
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return text
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    
    return text


def ingest_thesis(pdf_path, author, year, extract_figures=False):
    """
    Ingest a thesis PDF into the vector store.
    
    Args:
        pdf_path (str): Path to the PDF file
        author (str): Author of the thesis
        year (int): Year of publication
        extract_figures (bool): Whether to extract figures and tables
        
    Returns:
        bool: True if ingestion was successful, False otherwise
    """
    # Get the filename for the title (fallback)
    filename = Path(pdf_path).stem
    
    # Extract text from PDF
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("Error: Could not extract text from PDF")
        return False
    
    print(f"Extracted {len(text)} characters")
    
    # Create Document record
    doc = Document.objects.create(
        title=filename,
        doc_type="thesis",
        author=author,
        year=year
    )
    
    # Ensure Weaviate schema exists
    create_schema_if_not_exists()
    
    # Split text by chapters
    print("Splitting text by chapters...")
    chapters = split_by_chapter(text)
    
    if not chapters:
        print("No chapters found, treating the entire document as a single text")
        chapters = {"Introduction": text}
    
    print(f"Found {len(chapters)} chapters")
    
    # Process each chapter
    total_chunks = 0
    for chapter_num, chapter_text in chapters.items():
        print(f"Processing Chapter {chapter_num}...")
        
        # Chunk the chapter text
        chunks = chunk_text(chapter_text)
        
        # Store each chunk in Weaviate
        for i, chunk in enumerate(chunks):
            # Skip empty chunks
            if not chunk.strip():
                continue
            
            metadata = {
                "doc_type": "thesis",
                "title": filename,
                "author": author,
                "year": year,
                "chapter": str(chapter_num),
                "source": pdf_path
            }
            
            # Add to Weaviate
            result = add_document_chunk_to_weaviate(chunk, metadata)
            
            if result:
                total_chunks += 1
            
            # Rate limiting to avoid OpenAI API rate limits
            if i > 0 and i % 10 == 0:
                time.sleep(1)
    
    print(f"Successfully added {total_chunks} chunks to the vector store")
    
    # Extract figures if requested
    if extract_figures:
        print("Extracting figures and tables from PDF...")
        
        try:
            # Prepare document metadata
            doc_metadata = {
                "title": filename,
                "author": author,
                "year": year,
                "doc_type": "thesis"
            }
            
            # Extract figures and add to vector database
            figures, figure_ids = extract_figures_from_pdf(pdf_path, doc_metadata)
            
            print(f"Successfully extracted {len(figures)} figures/tables")
            print(f"Added {len(figure_ids)} figures/tables to the vector store")
            
        except Exception as e:
            print(f"Error extracting figures: {e}")
            print("Continuing with text-only ingestion")
    
    return True


def ingest_protocol(pdf_path, title=None, author=None, year=None, extract_figures=False):
    """
    Ingest a protocol PDF into the vector store.
    
    Args:
        pdf_path (str): Path to the PDF file
        title (str, optional): Title of the protocol
        author (str, optional): Author of the protocol
        year (int, optional): Year of publication
        extract_figures (bool): Whether to extract figures and tables
        
    Returns:
        bool: True if ingestion was successful, False otherwise
    """
    # Get the filename for the title (fallback)
    if not title:
        title = Path(pdf_path).stem
    
    # Extract text from PDF
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("Error: Could not extract text from PDF")
        return False
    
    print(f"Extracted {len(text)} characters")
    
    # Create Document record
    doc = Document.objects.create(
        title=title,
        doc_type="protocol",
        author=author or "",
        year=year
    )
    
    # Ensure Weaviate schema exists
    create_schema_if_not_exists()
    
    # Chunk the text
    chunks = chunk_text(text)
    
    # Store each chunk in Weaviate
    total_chunks = 0
    for i, chunk in enumerate(chunks):
        # Skip empty chunks
        if not chunk.strip():
            continue
        
        metadata = {
            "doc_type": "protocol",
            "title": title,
            "author": author or "",
            "year": year,
            "source": pdf_path
        }
        
        # Add to Weaviate
        result = add_document_chunk_to_weaviate(chunk, metadata)
        
        if result:
            total_chunks += 1
        
        # Rate limiting to avoid OpenAI API rate limits
        if i > 0 and i % 10 == 0:
            time.sleep(1)
    
    print(f"Successfully added {total_chunks} chunks to the vector store")
    
    # Extract figures if requested
    if extract_figures:
        print("Extracting figures and tables from PDF...")
        
        try:
            # Prepare document metadata
            doc_metadata = {
                "title": title,
                "author": author or "",
                "year": year,
                "doc_type": "protocol"
            }
            
            # Extract figures and add to vector database
            figures, figure_ids = extract_figures_from_pdf(pdf_path, doc_metadata)
            
            print(f"Successfully extracted {len(figures)} figures/tables")
            print(f"Added {len(figure_ids)} figures/tables to the vector store")
            
        except Exception as e:
            print(f"Error extracting figures: {e}")
            print("Continuing with text-only ingestion")
    
    return True


def main():
    """
    Main function to ingest a thesis or protocol PDF.
    """
    parser = argparse.ArgumentParser(description="Ingest a PDF into the vector store.")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("author", help="Author of the document")
    parser.add_argument("year", type=int, help="Year the document was published")
    parser.add_argument("--doc-type", choices=["thesis", "protocol"], default="thesis",
                        help="Type of document (thesis or protocol)")
    parser.add_argument("--title", help="Title of the document (optional, uses filename if not provided)")
    parser.add_argument("--extract-figures", action="store_true", 
                        help="Extract figures and tables from the PDF")
    
    args = parser.parse_args()
    
    print(f"Ingesting {args.doc_type}: {args.pdf_path}")
    print(f"Author: {args.author}, Year: {args.year}")
    
    if args.extract_figures:
        print("Figure extraction enabled")
    
    if args.doc_type == "thesis":
        success = ingest_thesis(args.pdf_path, args.author, args.year, args.extract_figures)
    else:
        title = args.title or Path(args.pdf_path).stem
        success = ingest_protocol(args.pdf_path, title, args.author, args.year, args.extract_figures)
    
    if success:
        print(f"{args.doc_type.capitalize()} ingestion completed successfully")
    else:
        print(f"{args.doc_type.capitalize()} ingestion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()