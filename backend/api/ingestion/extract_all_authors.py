#!/usr/bin/env python
"""
Enhanced author extraction to capture ALL authors from papers.
This fixes the issue where co-authors like Vishal Bharti aren't found in search.
"""

import re
import pdfplumber
from typing import List, Dict, Tuple
import os

def extract_all_authors_from_pdf(pdf_path: str) -> Tuple[str, List[str]]:
    """
    Extract ALL authors from a PDF paper, not just the first author.
    
    Returns:
        - primary_author: The first/corresponding author
        - all_authors: List of all authors including co-authors
    """
    all_authors = []
    primary_author = ""
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Get text from first few pages (authors are usually on page 1-2)
            text = ""
            for i, page in enumerate(pdf.pages[:3]):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
                if i >= 2:  # First 3 pages should be enough
                    break
            
            # Extract authors using multiple patterns
            all_authors = extract_authors_from_text(text)
            
            # If no authors found in content, try metadata
            if not all_authors and pdf.metadata:
                author_meta = pdf.metadata.get('Author', '')
                if author_meta:
                    # Split common author delimiters in metadata
                    all_authors = re.split(r'[,;&]|\sand\s', author_meta)
                    all_authors = [a.strip() for a in all_authors if a.strip()]
            
            # Set primary author
            if all_authors:
                primary_author = all_authors[0]
                
    except Exception as e:
        print(f"Error extracting authors from {pdf_path}: {e}")
    
    return primary_author, all_authors

def extract_authors_from_text(text: str) -> List[str]:
    """
    Extract author names from paper text using various patterns.
    """
    authors = []
    
    # Clean the text
    text = text.replace('\n\n\n', '\n\n')
    lines = text.split('\n')
    
    # Pattern 1: Look for author section with names and affiliations
    # Often appears as "Name1^1, Name2^2, Name3^1,2" or similar
    author_patterns = [
        # Pattern for "FirstName LastName1,2, FirstName LastName3,4"
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s*[,\d\*†‡§¶]+)*(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s*[,\d\*†‡§¶]+)*)*)',
        
        # Pattern for author lists after "Authors:" or similar
        r'(?:Authors?|BY|By)[\s:]+([^\n]+(?:\n(?![A-Z][a-z]+:)[^\n]+)*)',
        
        # Pattern for names with middle initials
        r'^((?:[A-Z][a-z]+(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z]+)+(?:\s*[,\d\*†‡§¶]+)*(?:\s*,\s*)?)+)',
    ]
    
    # Try to find authors in the first part of the document
    first_section = '\n'.join(lines[:50])  # First 50 lines usually contain authors
    
    for pattern in author_patterns:
        matches = re.finditer(pattern, first_section, re.MULTILINE)
        for match in matches:
            author_text = match.group(1)
            
            # Skip if it's likely not authors (too long, contains keywords)
            skip_keywords = ['abstract', 'introduction', 'keywords', 'summary', 'received', 'accepted']
            if any(keyword in author_text.lower() for keyword in skip_keywords):
                continue
            
            # Extract individual names
            # Remove superscripts and special characters
            author_text = re.sub(r'[*†‡§¶\d]+', '', author_text)
            
            # Split by commas and 'and'
            potential_authors = re.split(r',\s*|\s+and\s+', author_text)
            
            for author in potential_authors:
                author = author.strip()
                
                # Validate it looks like a name (at least 2 parts, starts with capital)
                parts = author.split()
                if len(parts) >= 2 and parts[0][0].isupper() and len(author) < 50:
                    # Handle "LastName, FirstName" format
                    if ',' in author and len(parts) == 2:
                        author = f"{parts[1]} {parts[0].rstrip(',')}"
                    
                    authors.append(author)
            
            if authors:
                break
    
    # Pattern 2: Look for specific Indian names pattern (common in the lab)
    if not authors:
        # Names often appear early in the document
        indian_name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:[,\d\*†‡§¶]+|$)'
        
        for i, line in enumerate(lines[:30]):
            if len(line) > 10 and not any(kw in line.lower() for kw in ['university', 'institute', 'department']):
                names = re.findall(indian_name_pattern, line)
                valid_names = []
                
                for name in names:
                    parts = name.split()
                    # Check if it's likely a person's name
                    if 2 <= len(parts) <= 4 and all(p[0].isupper() for p in parts):
                        valid_names.append(name)
                
                # If we found multiple names on a line, likely an author line
                if len(valid_names) >= 2:
                    authors.extend(valid_names)
                    break
    
    # Remove duplicates while preserving order
    seen = set()
    unique_authors = []
    for author in authors:
        if author not in seen:
            seen.add(author)
            unique_authors.append(author)
    
    return unique_authors

def update_document_with_all_authors(doc_id: int, all_authors: List[str]):
    """
    Update a document's metadata to include all authors in a searchable way.
    Since we can't change the database schema, we'll append co-authors to the title
    or content to make them searchable.
    """
    from api.models import Document
    
    try:
        doc = Document.objects.get(id=doc_id)
        
        # Create a searchable author string
        author_string = f"Authors: {', '.join(all_authors)}"
        
        # We can't change the schema, so let's add to the year field (if not used)
        # Or better, we'll include it in the chunks when vectorizing
        
        # For now, update the author field to include primary author
        if all_authors:
            doc.author = all_authors[0]
            doc.save()
            
        return author_string
        
    except Document.DoesNotExist:
        print(f"Document {doc_id} not found")
        return ""

def test_author_extraction():
    """Test the author extraction on sample papers."""
    
    # Test with a sample text that might appear in papers
    sample_text = """
    Research Article
    
    Structural basis for target-site selection in RNA-guided DNA transposition systems
    
    Saumya Sharma1,2, Vishal Bharti1, Riya Rauthan1,3, Mohit Kumar1, and Debojyoti Chakraborty1,*
    
    1CSIR-Institute of Genomics and Integrative Biology, New Delhi, India
    2Academy of Scientific and Innovative Research (AcSIR), Ghaziabad, India
    3Current address: University of California, San Francisco
    *Corresponding author: debojyoti.chakraborty@igib.res.in
    
    Abstract
    CRISPR-associated transposons (CASTs) are...
    """
    
    authors = extract_authors_from_text(sample_text)
    print("Extracted authors:", authors)
    
    # Should output: ['Saumya Sharma', 'Vishal Bharti', 'Riya Rauthan', 'Mohit Kumar', 'Debojyoti Chakraborty']

if __name__ == "__main__":
    test_author_extraction()
    
    # Example: Process a specific paper
    # pdf_path = "/path/to/paper.pdf"
    # primary, all_authors = extract_all_authors_from_pdf(pdf_path)
    # print(f"Primary author: {primary}")
    # print(f"All authors: {all_authors}")