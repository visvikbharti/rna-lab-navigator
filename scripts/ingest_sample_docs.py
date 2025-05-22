#!/usr/bin/env python
"""
Ingest Sample Documents Script for RNA Lab Navigator

This script loads sample documents from the data/sample_docs directory
into the Weaviate vector database for demo purposes.

Usage:
    python scripts/ingest_sample_docs.py [--purge]

Options:
    --purge    Purge existing data before ingestion (default: False)
"""

import os
import sys
import argparse
import logging
import pathlib
import django
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project directory to the Python path
script_dir = pathlib.Path(__file__).resolve().parent
project_dir = script_dir.parent
sys.path.append(str(project_dir))
sys.path.append(str(project_dir / "backend"))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rna_backend.settings")
django.setup()

# Now we can import Django models
from api.models import Document
from api.ingestion.ingest_thesis import ingest_thesis
from api.ingestion.chunking_utils import process_pdf_document


def ingest_sample_docs(purge=False):
    """
    Ingest sample documents from data/sample_docs directory
    
    Args:
        purge (bool): Whether to purge existing data before ingestion
    """
    # Paths to sample documents
    sample_dir = project_dir / "data" / "sample_docs"
    theses_dir = sample_dir / "theses"
    papers_dir = sample_dir / "papers"
    protocols_dir = sample_dir / "community_protocols"
    troubleshooting_dir = sample_dir / "troubleshooting"
    
    # Purge existing data if requested
    if purge:
        logger.info("Purging existing documents...")
        Document.objects.all().delete()
        
        # Connect to Weaviate and delete classes
        from api.ingestion.embeddings_utils import get_weaviate_client
        client = get_weaviate_client()
        
        try:
            if client.schema.exists("Document"):
                client.schema.delete_class("Document")
                logger.info("Deleted Document class from Weaviate")
            
            if client.schema.exists("Figure"):
                client.schema.delete_class("Figure")
                logger.info("Deleted Figure class from Weaviate")
        except Exception as e:
            logger.error(f"Error purging Weaviate data: {e}")
    
    # Process thesis documents
    logger.info("Processing thesis documents...")
    for thesis_file in theses_dir.glob("*.pdf"):
        try:
            filename = os.path.basename(thesis_file)
            parts = filename.split('_')
            
            # Extract year, author from filename (format: YYYY_Author_Title_PhD_Thesis.pdf)
            year = int(parts[0])
            author = parts[1]
            
            logger.info(f"Processing thesis: {filename}, Author: {author}, Year: {year}")
            ingest_thesis(
                pdf_path=str(thesis_file),
                author=author,
                year=year
            )
            logger.info(f"Successfully processed thesis: {filename}")
        except Exception as e:
            logger.error(f"Error processing thesis {thesis_file}: {e}")
    
    # Process protocol documents
    logger.info("Processing protocol documents...")
    for protocol_file in protocols_dir.glob("*.pdf"):
        try:
            filename = os.path.basename(protocol_file)
            # Extract simplified title from filename
            title = filename.replace(".pdf", "").replace("-", " ").replace("_", " ")
            
            logger.info(f"Processing protocol: {filename}")
            doc = Document.objects.create(
                title=title,
                doc_type="protocol",
                author="Lab Protocol",
                year=datetime.now().year,
                file_path=str(protocol_file),
                status="pending"
            )
            
            process_pdf_document(
                doc_id=doc.id,
                pdf_path=str(protocol_file),
                chunk_size=400,
                chunk_overlap=100
            )
            
            doc.status = "processed"
            doc.save()
            
            logger.info(f"Successfully processed protocol: {filename}")
        except Exception as e:
            logger.error(f"Error processing protocol {protocol_file}: {e}")
    
    # Process paper documents
    logger.info("Processing paper documents...")
    for paper_file in papers_dir.glob("*.pdf"):
        try:
            filename = os.path.basename(paper_file)
            parts = filename.split('_')
            
            # Extract year, author from filename (format: YYYY_Author_Journal_Title.pdf)
            year = int(parts[0])
            author = parts[1]
            
            # Extract journal and title
            journal = parts[2] if len(parts) > 2 else "Unknown"
            title = " ".join(parts[3:]).replace(".pdf", "")
            
            logger.info(f"Processing paper: {filename}, Author: {author}, Year: {year}")
            doc = Document.objects.create(
                title=title,
                doc_type="paper",
                author=author,
                year=year,
                journal=journal,
                file_path=str(paper_file),
                status="pending"
            )
            
            process_pdf_document(
                doc_id=doc.id,
                pdf_path=str(paper_file),
                chunk_size=400,
                chunk_overlap=100
            )
            
            doc.status = "processed"
            doc.save()
            
            logger.info(f"Successfully processed paper: {filename}")
        except Exception as e:
            logger.error(f"Error processing paper {paper_file}: {e}")
    
    # Process troubleshooting documents
    logger.info("Processing troubleshooting documents...")
    for ts_file in troubleshooting_dir.glob("*.md"):
        try:
            filename = os.path.basename(ts_file)
            title = filename.replace(".md", "").replace("_", " ").title()
            
            logger.info(f"Processing troubleshooting doc: {filename}")
            
            with open(ts_file, 'r') as f:
                content = f.read()
            
            doc = Document.objects.create(
                title=title,
                doc_type="troubleshooting",
                author="Lab Support",
                year=datetime.now().year,
                file_path=str(ts_file),
                status="pending"
            )
            
            # For markdown files, we'll create a single chunk with the entire content
            from api.ingestion.embeddings_utils import store_chunk
            
            store_chunk(
                doc_id=doc.id,
                content=content,
                chunk_id="1",
                metadata={
                    "title": title,
                    "doc_type": "troubleshooting",
                    "author": "Lab Support",
                    "year": datetime.now().year
                }
            )
            
            doc.status = "processed"
            doc.save()
            
            logger.info(f"Successfully processed troubleshooting doc: {filename}")
        except Exception as e:
            logger.error(f"Error processing troubleshooting doc {ts_file}: {e}")
    
    # Print summary
    doc_count = Document.objects.count()
    logger.info(f"Ingestion complete. {doc_count} documents processed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest sample documents for RNA Lab Navigator")
    parser.add_argument("--purge", action="store_true", help="Purge existing data before ingestion")
    args = parser.parse_args()
    
    ingest_sample_docs(purge=args.purge)