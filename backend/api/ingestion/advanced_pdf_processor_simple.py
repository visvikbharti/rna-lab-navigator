"""
Simplified advanced PDF processor that uses available libraries.
"""

import io
import os
import re
from typing import List, Dict, Any, Tuple
import pdfplumber
import pandas as pd
from pathlib import Path


class AdvancedPDFProcessor:
    """Advanced PDF processing with table extraction using pdfplumber."""
    
    def __init__(self):
        self.temp_dir = Path("/tmp/pdf_processing")
        self.temp_dir.mkdir(exist_ok=True)
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF with advanced extraction of text, tables, and metadata.
        
        Returns:
            Dict containing:
            - text: Full text content
            - tables: List of extracted tables with metadata
            - sections: Document structure with headers
            - metadata: Document metadata
        """
        result = {
            "text": "",
            "tables": [],
            "figures": [],  # Placeholder for now
            "sections": [],
            "metadata": {},
            "equations": []
        }
        
        # Extract text and structure with pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            # Extract metadata
            result["metadata"] = self._extract_metadata(pdf)
            
            # Extract text with structure
            full_text = []
            current_section = {"title": "Introduction", "content": [], "page": 1}
            
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                full_text.append(page_text)
                
                # Extract section headers
                sections = self._extract_sections(page_text, page_num)
                if sections:
                    # Save current section
                    if current_section["content"]:
                        result["sections"].append(current_section)
                    # Start new section
                    current_section = {
                        "title": sections[-1]["title"],
                        "content": [],
                        "page": sections[-1]["page"]
                    }
                
                current_section["content"].append(page_text)
                
                # Extract tables from this page
                tables = self._extract_tables_from_page(page, page_num)
                result["tables"].extend(tables)
            
            # Save last section
            if current_section["content"]:
                result["sections"].append(current_section)
            
            result["text"] = "\n\n".join(full_text)
        
        # Extract equations from text
        equations = self._extract_equations(result["text"])
        result["equations"] = equations
        
        return result
    
    def _extract_metadata(self, pdf) -> Dict[str, Any]:
        """Extract PDF metadata."""
        metadata = pdf.metadata or {}
        return {
            "title": metadata.get("Title", ""),
            "author": metadata.get("Author", ""),
            "subject": metadata.get("Subject", ""),
            "keywords": metadata.get("Keywords", ""),
            "pages": len(pdf.pages),
            "creation_date": str(metadata.get("CreationDate", "")),
            "modification_date": str(metadata.get("ModDate", ""))
        }
    
    def _extract_sections(self, text: str, page_num: int) -> List[Dict[str, Any]]:
        """Extract section headers from text."""
        sections = []
        
        # Common section patterns in scientific papers
        section_patterns = [
            r"^(\d+\.?\d*)\s+([A-Z][A-Za-z\s]+)$",  # 1. Introduction
            r"^([A-Z][A-Z\s]+)$",  # INTRODUCTION
            r"^(Abstract|Introduction|Methods|Results|Discussion|Conclusion|References)$",
            r"^(CHAPTER\s+\d+)\s*:?\s*(.+)$",  # Thesis chapters
        ]
        
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if len(line) < 100:  # Headers are usually short
                for pattern in section_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        sections.append({
                            "title": line,
                            "page": page_num
                        })
                        break
        
        return sections
    
    def _extract_tables_from_page(self, page, page_num: int) -> List[Dict[str, Any]]:
        """Extract tables from a page using pdfplumber."""
        tables = []
        
        try:
            # Extract tables with pdfplumber
            plumber_tables = page.extract_tables()
            
            for i, table_data in enumerate(plumber_tables):
                if table_data and len(table_data) > 1:
                    # Assume first row is header
                    headers = table_data[0] if table_data[0] else [f"Column_{j}" for j in range(len(table_data[0]))]
                    
                    # Create DataFrame
                    df = pd.DataFrame(table_data[1:], columns=headers)
                    
                    # Find potential caption
                    caption = f"Table {i+1} on page {page_num}"
                    
                    tables.append({
                        "page": page_num,
                        "index": i,
                        "caption": caption,
                        "data": df.to_dict('records'),
                        "shape": df.shape,
                        "accuracy": 0.8,  # Estimated
                        "html": df.to_html(index=False)
                    })
        except Exception as e:
            print(f"Error extracting tables from page {page_num}: {e}")
        
        return tables
    
    def _extract_equations(self, text: str) -> List[Dict[str, str]]:
        """Extract mathematical equations from text."""
        equations = []
        
        # Look for common equation patterns
        # E.g., "E = mc²" or "ΔG = ΔH - TΔS"
        equation_patterns = [
            r'([A-Za-zΔ∇∂]+\s*=\s*[A-Za-z0-9\s\+\-\*\/\^²³⁴√∑∏∫\(\)]+)',
            r'(\w+\s*=\s*\w+[\s\+\-\*\/\^]*\w*)',  # Simple equations
        ]
        
        for pattern in equation_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) > 5 and '=' in match:  # Filter out trivial matches
                    equations.append({
                        "type": "text",
                        "content": match.strip()
                    })
        
        # Remove duplicates
        unique_equations = []
        seen = set()
        for eq in equations:
            if eq["content"] not in seen:
                seen.add(eq["content"])
                unique_equations.append(eq)
        
        return unique_equations


class EnhancedChunker:
    """Enhanced text chunking with better context preservation."""
    
    def __init__(self, chunk_size: int = 400, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_document(self, doc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk document while preserving structure and context.
        
        Returns list of chunks with metadata.
        """
        chunks = []
        
        # Process sections
        for section in doc_data.get("sections", []):
            section_chunks = self._chunk_section(section)
            chunks.extend(section_chunks)
        
        # Process tables as separate chunks
        for table in doc_data.get("tables", []):
            table_chunk = {
                "type": "table",
                "content": self._table_to_text(table),
                "metadata": {
                    "page": table["page"],
                    "caption": table["caption"],
                    "shape": table["shape"]
                }
            }
            chunks.append(table_chunk)
        
        # Process equations
        for eq in doc_data.get("equations", []):
            eq_chunk = {
                "type": "equation",
                "content": eq["content"],
                "metadata": {
                    "equation_type": eq["type"]
                }
            }
            chunks.append(eq_chunk)
        
        return chunks
    
    def _chunk_section(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk a section while preserving headers."""
        chunks = []
        section_text = "\n".join(section["content"])
        
        # Split into sentences
        sentences = self._split_into_sentences(section_text)
        current_chunk = [f"Section: {section['title']}"]
        current_size = len(current_chunk[0].split())
        
        for sentence in sentences:
            sentence_size = len(sentence.split())
            
            if current_size + sentence_size > self.chunk_size:
                # Create chunk
                chunks.append({
                    "type": "text",
                    "content": " ".join(current_chunk),
                    "metadata": {
                        "section": section["title"],
                        "page": section["page"]
                    }
                })
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap(current_chunk)
                current_chunk = [f"Section: {section['title']}"] + overlap_sentences + [sentence]
                current_size = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add last chunk
        if current_chunk:
            chunks.append({
                "type": "text",
                "content": " ".join(current_chunk),
                "metadata": {
                    "section": section["title"],
                    "page": section["page"]
                }
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap(self, chunk: List[str]) -> List[str]:
        """Get overlap sentences from the end of a chunk."""
        overlap_words = 0
        overlap_sentences = []
        
        for sentence in reversed(chunk[1:]):  # Skip section header
            sentence_words = len(sentence.split())
            if overlap_words + sentence_words <= self.overlap:
                overlap_sentences.insert(0, sentence)
                overlap_words += sentence_words
            else:
                break
        
        return overlap_sentences
    
    def _table_to_text(self, table: Dict[str, Any]) -> str:
        """Convert table to searchable text format."""
        text_parts = [f"Table: {table['caption']}"]
        
        # Convert table data to readable format
        df = pd.DataFrame(table['data'])
        
        # Add column headers
        if not df.empty:
            headers = " | ".join(str(col) for col in df.columns)
            text_parts.append(f"Headers: {headers}")
            
            # Add first few rows as context
            for idx, row in df.head(5).iterrows():
                row_text = " | ".join(str(val) for val in row.values)
                text_parts.append(row_text)
            
            if len(df) > 5:
                text_parts.append(f"... and {len(df) - 5} more rows")
        
        return "\n".join(text_parts)