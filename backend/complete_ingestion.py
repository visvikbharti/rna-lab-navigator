#!/usr/bin/env python3
"""
Comprehensive document ingestion script for RNA Lab Navigator
Processes ALL documents from data/sample_docs/ systematically
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.append('/Users/vishalbharti/Downloads/rna-lab-navigator/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings')
django.setup()

from api.models import Document
from api.search.real_rag import vector_store
import pdfplumber
import re

def extract_pdf_text(pdf_path):
    """Extract text from PDF file."""
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF {pdf_path}: {e}")
        return None

def parse_paper_filename(filename):
    """Parse paper filename to extract year, author, and title."""
    # Format: YYYY_Author_Journal_Title_Keywords.pdf
    parts = filename.replace('.pdf', '').split('_')
    if len(parts) >= 3:
        year = parts[0] if parts[0].isdigit() else "2024"
        author = parts[1] if len(parts) > 1 else "Unknown"
        # Take rest as title, clean it up
        title_parts = parts[1:]  # Skip year
        title = ' '.join(title_parts).replace('_', ' ')
        return year, author, title
    return "2024", "Unknown", filename.replace('.pdf', '').replace('_', ' ')

def chunk_text(text, chunk_size=400, overlap=100):
    """Split text into overlapping chunks."""
    if not text:
        return []
    
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk = ' '.join(chunk_words)
        chunks.append(chunk)
        
        if i + chunk_size >= len(words):
            break
    
    return chunks

def ingest_paper(pdf_path):
    """Ingest a single research paper."""
    filename = os.path.basename(pdf_path)
    year, author, title = parse_paper_filename(filename)
    
    print(f"Processing paper: {filename}")
    print(f"  -> Parsed as: {title} by {author} ({year})")
    
    # Check if already exists
    existing = Document.objects.filter(title__icontains=title[:30]).first()
    if existing:
        print(f"  -> Already exists: {existing.title}")
        return existing, 0
    
    # Extract text
    text = extract_pdf_text(pdf_path)
    if not text:
        print(f"  -> Failed to extract text")
        return None, 0
    
    print(f"  -> Extracted {len(text)} characters")
    
    # Create document entry
    doc = Document.objects.create(
        title=title,
        author=author,
        year=int(year),
        doc_type='paper'
    )
    
    # Chunk and add to vector store
    chunks = chunk_text(text)
    print(f"  -> Generated {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        metadata = {
            'title': title,
            'author': author,
            'doc_type': 'paper',
            'year': int(year),
            'document_id': doc.id,
            'chunk_index': i,
            'text': chunk
        }
        vector_store.add_document(chunk, metadata)
    
    return doc, len(chunks)

def ingest_protocol(pdf_path):
    """Ingest a single protocol document."""
    filename = os.path.basename(pdf_path)
    title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
    
    print(f"Processing protocol: {filename}")
    print(f"  -> Title: {title}")
    
    # Check if already exists
    existing = Document.objects.filter(title__icontains=title[:30]).first()
    if existing:
        print(f"  -> Already exists: {existing.title}")
        return existing, 0
    
    # Extract text
    text = extract_pdf_text(pdf_path)
    if not text:
        print(f"  -> Failed to extract text")
        return None, 0
    
    print(f"  -> Extracted {len(text)} characters")
    
    # Create document entry
    doc = Document.objects.create(
        title=title,
        author="Lab Protocol",
        year=2024,
        doc_type='protocol'
    )
    
    # Chunk and add to vector store
    chunks = chunk_text(text)
    print(f"  -> Generated {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        metadata = {
            'title': title,
            'author': "Lab Protocol",
            'doc_type': 'protocol',
            'year': 2024,
            'document_id': doc.id,
            'chunk_index': i,
            'text': chunk
        }
        vector_store.add_document(chunk, metadata)
    
    return doc, len(chunks)

def ingest_troubleshooting_file(file_path):
    """Ingest troubleshooting markdown file."""
    filename = os.path.basename(file_path)
    title = filename.replace('.md', '').replace('_', ' ').title()
    
    print(f"Processing troubleshooting: {filename}")
    
    # Check if already exists
    existing = Document.objects.filter(title__icontains=title).first()
    if existing:
        print(f"  -> Already exists: {existing.title}")
        return existing, 0
    
    # Read markdown content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"  -> Failed to read file: {e}")
        return None, 0
    
    print(f"  -> Read {len(text)} characters")
    
    # Create document entry
    doc = Document.objects.create(
        title=title,
        author="Lab Documentation",
        year=2024,
        doc_type='protocol'  # Treat as protocol
    )
    
    # Chunk and add to vector store
    chunks = chunk_text(text)
    print(f"  -> Generated {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        metadata = {
            'title': title,
            'author': "Lab Documentation",
            'doc_type': 'protocol',
            'year': 2024,
            'document_id': doc.id,
            'chunk_index': i,
            'text': chunk
        }
        vector_store.add_document(chunk, metadata)
    
    return doc, len(chunks)

def main():
    """Main ingestion process."""
    print("🚀 COMPLETE DOCUMENT INGESTION STARTING...")
    print("=" * 60)
    
    base_path = Path("/Users/vishalbharti/Downloads/rna-lab-navigator/data/sample_docs")
    
    total_docs = 0
    total_chunks = 0
    
    # 1. Ingest ALL papers
    print("\n📄 INGESTING RESEARCH PAPERS...")
    papers_path = base_path / "papers"
    paper_files = list(papers_path.glob("*.pdf"))
    print(f"Found {len(paper_files)} paper files")
    
    for pdf_file in sorted(paper_files):
        try:
            doc, chunks = ingest_paper(pdf_file)
            if doc and chunks > 0:
                total_docs += 1
                total_chunks += chunks
                print(f"  ✅ Success: {chunks} chunks")
            else:
                print(f"  ❌ Skipped")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # 2. Ingest ALL protocols
    print(f"\n📋 INGESTING PROTOCOL DOCUMENTS...")
    protocols_path = base_path / "community_protocols"
    protocol_files = list(protocols_path.glob("*.pdf"))
    print(f"Found {len(protocol_files)} protocol files")
    
    for pdf_file in sorted(protocol_files):
        try:
            doc, chunks = ingest_protocol(pdf_file)
            if doc and chunks > 0:
                total_docs += 1
                total_chunks += chunks
                print(f"  ✅ Success: {chunks} chunks")
            else:
                print(f"  ❌ Skipped")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # 3. Ingest troubleshooting files
    print(f"\n🔧 INGESTING TROUBLESHOOTING FILES...")
    troubleshooting_path = base_path / "troubleshooting"
    md_files = list(troubleshooting_path.glob("*.md"))
    print(f"Found {len(md_files)} troubleshooting files")
    
    for md_file in sorted(md_files):
        try:
            doc, chunks = ingest_troubleshooting_file(md_file)
            if doc and chunks > 0:
                total_docs += 1
                total_chunks += chunks
                print(f"  ✅ Success: {chunks} chunks")
            else:
                print(f"  ❌ Skipped")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Save vector store
    print(f"\n💾 SAVING VECTOR STORE...")
    vector_store.save_to_cache()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 INGESTION COMPLETE!")
    print(f"📊 Documents processed this session: {total_docs}")
    print(f"🧩 Chunks generated this session: {total_chunks}")
    print(f"📚 Total vector store size: {len(vector_store.vectors)}")
    
    # Database summary
    all_docs = Document.objects.all()
    print(f"\n📈 FINAL DATABASE STATUS:")
    print(f"Total documents: {all_docs.count()}")
    for doc_type in ['thesis', 'paper', 'protocol']:
        count = all_docs.filter(doc_type=doc_type).count()
        print(f"  {doc_type}: {count}")

if __name__ == "__main__":
    main()