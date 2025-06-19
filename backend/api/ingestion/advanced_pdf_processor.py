"""
Advanced PDF processor with table and figure extraction capabilities.
"""

import io
import os
import re
from typing import List, Dict, Any, Tuple
import pdfplumber
import fitz  # PyMuPDF
import camelot
import pandas as pd
from PIL import Image
import numpy as np
from pathlib import Path


class AdvancedPDFProcessor:
    """Advanced PDF processing with table, figure, and equation extraction."""
    
    def __init__(self):
        self.temp_dir = Path("/tmp/pdf_processing")
        self.temp_dir.mkdir(exist_ok=True)
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF with advanced extraction of text, tables, figures, and metadata.
        
        Returns:
            Dict containing:
            - text: Full text content
            - tables: List of extracted tables with metadata
            - figures: List of extracted figures with captions
            - sections: Document structure with headers
            - metadata: Document metadata
        """
        result = {
            "text": "",
            "tables": [],
            "figures": [],
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
                tables = self._extract_tables_from_page(pdf_path, page_num)
                result["tables"].extend(tables)
            
            # Save last section
            if current_section["content"]:
                result["sections"].append(current_section)
            
            result["text"] = "\n\n".join(full_text)
        
        # Extract figures with PyMuPDF
        figures = self._extract_figures(pdf_path)
        result["figures"] = figures
        
        # Extract equations
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
    
    def _extract_tables_from_page(self, pdf_path: str, page_num: int) -> List[Dict[str, Any]]:
        """Extract tables from a specific page using Camelot."""
        tables = []
        
        try:
            # Try to extract tables with Camelot
            camelot_tables = camelot.read_pdf(
                pdf_path,
                pages=str(page_num),
                flavor='lattice',  # Use 'stream' if lattice doesn't work
                suppress_stdout=True
            )
            
            for i, table in enumerate(camelot_tables):
                # Convert to pandas DataFrame
                df = table.df
                
                # Extract table caption if available
                caption = self._find_table_caption(table)
                
                tables.append({
                    "page": page_num,
                    "index": i,
                    "caption": caption,
                    "data": df.to_dict('records'),
                    "shape": df.shape,
                    "accuracy": table.accuracy,
                    "html": df.to_html(index=False)
                })
        except Exception as e:
            # Fallback to pdfplumber table extraction
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    page = pdf.pages[page_num - 1]
                    plumber_tables = page.extract_tables()
                    
                    for i, table_data in enumerate(plumber_tables):
                        if table_data and len(table_data) > 1:
                            df = pd.DataFrame(table_data[1:], columns=table_data[0])
                            tables.append({
                                "page": page_num,
                                "index": i,
                                "caption": f"Table {i+1} on page {page_num}",
                                "data": df.to_dict('records'),
                                "shape": df.shape,
                                "accuracy": 0.8,  # Estimated
                                "html": df.to_html(index=False)
                            })
            except Exception as e2:
                print(f"Failed to extract tables from page {page_num}: {e}, {e2}")
        
        return tables
    
    def _extract_figures(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract figures and their captions using PyMuPDF."""
        figures = []
        
        try:
            pdf_document = fitz.open(pdf_path)
            
            for page_num, page in enumerate(pdf_document, 1):
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image data
                        xref = img[0]
                        pix = fitz.Pixmap(pdf_document, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            # Save image
                            img_data = pix.tobytes("png")
                            
                            # Try to find caption
                            caption = self._find_figure_caption(page, img_index)
                            
                            figures.append({
                                "page": page_num,
                                "index": img_index,
                                "caption": caption,
                                "width": pix.width,
                                "height": pix.height,
                                "type": "image/png",
                                "size": len(img_data)
                            })
                        
                        pix = None
                    except Exception as e:
                        print(f"Failed to extract figure {img_index} from page {page_num}: {e}")
            
            pdf_document.close()
        except Exception as e:
            print(f"Failed to extract figures from PDF: {e}")
        
        return figures
    
    def _find_table_caption(self, table) -> str:
        """Try to find table caption near the table."""
        # This is a simplified version - in practice, you'd need more sophisticated logic
        return f"Table {table.page + 1}"
    
    def _find_figure_caption(self, page, img_index: int) -> str:
        """Try to find figure caption near the figure."""
        text = page.get_text()
        lines = text.split('\n')
        
        # Look for common figure caption patterns
        caption_patterns = [
            rf"Figure\s+\d+[:\.]?\s*(.+)",
            rf"Fig\.\s+\d+[:\.]?\s*(.+)",
            rf"FIG\s+\d+[:\.]?\s*(.+)"
        ]
        
        for i, line in enumerate(lines):
            for pattern in caption_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # Get caption text (current line + possibly next lines)
                    caption = match.group(0)
                    # Check if caption continues on next lines
                    j = i + 1
                    while j < len(lines) and not re.match(r'^(Figure|Fig\.|Table)', lines[j], re.IGNORECASE):
                        if lines[j].strip():
                            caption += " " + lines[j].strip()
                        j += 1
                        if j - i > 3:  # Don't go too far
                            break
                    return caption
        
        return f"Figure {img_index + 1}"
    
    def _extract_equations(self, text: str) -> List[Dict[str, str]]:
        """Extract mathematical equations from text."""
        equations = []
        
        # Look for LaTeX-style equations
        latex_patterns = [
            r'\$\$(.+?)\$\$',  # Display math
            r'\$(.+?)\$',      # Inline math
            r'\\begin{equation}(.+?)\\end{equation}',
            r'\\begin{align}(.+?)\\end{align}',
        ]
        
        for pattern in latex_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                equations.append({
                    "type": "latex",
                    "content": match.strip()
                })
        
        # Look for common equation patterns
        # E.g., "E = mc²" or "ΔG = ΔH - TΔS"
        equation_pattern = r'([A-Za-zΔ∇∂]+\s*=\s*[A-Za-z0-9\s\+\-\*\/\^²³⁴√∑∏∫\(\)]+)'
        matches = re.findall(equation_pattern, text)
        for match in matches:
            if len(match) > 5:  # Filter out trivial matches
                equations.append({
                    "type": "text",
                    "content": match.strip()
                })
        
        return equations


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
        
        # Process figures
        for figure in doc_data.get("figures", []):
            figure_chunk = {
                "type": "figure",
                "content": figure["caption"],
                "metadata": {
                    "page": figure["page"],
                    "dimensions": f"{figure['width']}x{figure['height']}"
                }
            }
            chunks.append(figure_chunk)
        
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
        
        # Use langchain's RecursiveCharacterTextSplitter logic
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
        # Simple sentence splitting - could be improved with NLTK
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