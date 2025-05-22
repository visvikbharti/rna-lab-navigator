"""
Utility module for extracting figures and tables from PDF documents.
Integrates with the vector storage system to link figures with their textual content.
"""

import os
import re
import base64
import json
import hashlib
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import cv2
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .embeddings_utils import add_document_chunk_to_weaviate


class FigureExtractor:
    """
    Extracts figures, tables, and their captions from PDF documents.
    Links them to the text context and stores them in the vector database.
    """
    
    def __init__(self, pdf_path: str, doc_metadata: Dict[str, Any]):
        """
        Initialize the figure extractor with a PDF path and metadata.
        
        Args:
            pdf_path (str): Path to the PDF file
            doc_metadata (dict): Metadata about the document (title, author, etc.)
        """
        self.pdf_path = pdf_path
        self.doc_metadata = doc_metadata
        self.figures = []
        self.tables = []
        self.figure_dir = self._get_figure_storage_path()
        
        # Ensure figure directory exists
        os.makedirs(self.figure_dir, exist_ok=True)
    
    def _get_figure_storage_path(self) -> str:
        """
        Get the directory path for storing extracted figures.
        
        Returns:
            str: Directory path for figure storage
        """
        # Create a unique folder for this document
        doc_hash = hashlib.md5((
            self.doc_metadata.get('title', '') + 
            self.doc_metadata.get('author', '') +
            str(self.doc_metadata.get('year', ''))
        ).encode()).hexdigest()[:10]
        
        # Use MEDIA_ROOT if defined, otherwise use a default location
        if hasattr(settings, 'MEDIA_ROOT'):
            base_dir = os.path.join(settings.MEDIA_ROOT, 'figures')
        else:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), 'media', 'figures')
        
        return os.path.join(base_dir, doc_hash)
    
    def extract_all_figures(self) -> List[Dict[str, Any]]:
        """
        Extract all figures and their captions from the PDF.
        
        Returns:
            list: List of dictionaries containing figure data
        """
        # Open the PDF
        doc = fitz.open(self.pdf_path)
        
        # Process each page
        for page_idx, page in enumerate(doc):
            # Extract images
            self._extract_images(page, page_idx)
            
            # Extract captions
            self._extract_captions(page, page_idx)
        
        # Match captions to images based on proximity and references
        self._match_captions_to_images()
        
        # Extract tables
        self._extract_tables(doc)
        
        # Close the document
        doc.close()
        
        # Save figure data
        return self.figures
    
    def _extract_images(self, page: fitz.Page, page_idx: int) -> None:
        """
        Extract images from a page.
        
        Args:
            page (fitz.Page): PDF page object
            page_idx (int): Page index
        """
        # Get images
        image_list = page.get_images(full=True)
        
        # Process each image
        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            
            try:
                # Extract image data
                base_img = page.parent.extract_image(xref)
                image_bytes = base_img["image"]
                
                # Get image format and extension
                img_format = base_img["ext"]
                
                # Generate a unique filename
                filename = f"page{page_idx+1}_img{img_idx+1}.{img_format}"
                full_path = os.path.join(self.figure_dir, filename)
                
                # Generate a thumbnail
                img = Image.open(fitz.Pixmap(image_bytes).tobytes())
                img.thumbnail((300, 300))  # Create a thumbnail for preview
                
                # Save original image
                with open(full_path, "wb") as f:
                    f.write(image_bytes)
                
                # Get image position on page
                for obj in page.get_images():
                    if obj[0] == xref:
                        # Get the rectangle containing the image
                        rect = page.get_image_bbox(obj)
                        break
                else:
                    rect = None
                
                # Add to figures list
                figure_data = {
                    "type": "image",
                    "page": page_idx + 1,
                    "rect": rect,
                    "filename": filename,
                    "format": img_format,
                    "file_path": full_path,
                    "caption": "",  # Will be filled later
                    "caption_text": "",  # Will be filled later
                    "figure_number": None,  # Will be filled later
                    "table_number": None,
                    "web_path": f"/media/figures/{os.path.basename(self.figure_dir)}/{filename}"
                }
                
                self.figures.append(figure_data)
            except Exception as e:
                print(f"Error extracting image on page {page_idx+1}: {e}")
    
    def _extract_captions(self, page: fitz.Page, page_idx: int) -> None:
        """
        Extract figure and table captions from a page.
        
        Args:
            page (fitz.Page): PDF page object
            page_idx (int): Page index
        """
        # Get text blocks
        blocks = page.get_text("dict")["blocks"]
        
        # Regex patterns for figure and table captions
        figure_patterns = [
            r"(?:Figure|Fig\.?)\s*(\d+(?:\.\d+)?)[\.\:]\s*(.*)",
            r"(?:Figure|Fig\.?)\s*(\d+(?:\.\d+)?)\s*[\.\:]?\s*(.*)"
        ]
        
        table_patterns = [
            r"Table\s*(\d+(?:\.\d+)?)[\.\:]\s*(.*)",
            r"Table\s*(\d+(?:\.\d+)?)\s*[\.\:]?\s*(.*)"
        ]
        
        # Process each text block
        for block in blocks:
            if block["type"] == 0:  # Text block
                lines = []
                for line in block["lines"]:
                    spans = []
                    for span in line["spans"]:
                        spans.append(span["text"])
                    line_text = " ".join(spans)
                    lines.append(line_text)
                
                # Join lines into a paragraph
                text = " ".join(lines)
                
                # Look for figure captions
                for pattern in figure_patterns:
                    match = re.search(pattern, text)
                    if match:
                        fig_num = match.group(1)
                        caption = match.group(2)
                        
                        # Add to figures list if it's a new figure
                        caption_data = {
                            "type": "figure_caption",
                            "page": page_idx + 1,
                            "rect": [block["bbox"][0], block["bbox"][1], block["bbox"][2], block["bbox"][3]],
                            "figure_number": fig_num,
                            "caption": f"Figure {fig_num}: {caption}",
                            "caption_text": caption
                        }
                        
                        # Check if we already have an image for this figure
                        image_found = False
                        for fig in self.figures:
                            if fig["figure_number"] is None and fig["page"] == page_idx + 1:
                                # Update existing image with caption
                                fig["figure_number"] = fig_num
                                fig["caption"] = f"Figure {fig_num}: {caption}"
                                fig["caption_text"] = caption
                                image_found = True
                                break
                        
                        if not image_found:
                            # Create a placeholder for the caption
                            self.figures.append(caption_data)
                        
                        break
                
                # Look for table captions
                for pattern in table_patterns:
                    match = re.search(pattern, text)
                    if match:
                        table_num = match.group(1)
                        caption = match.group(2)
                        
                        # Add to tables list
                        self.tables.append({
                            "type": "table_caption",
                            "page": page_idx + 1,
                            "rect": [block["bbox"][0], block["bbox"][1], block["bbox"][2], block["bbox"][3]],
                            "table_number": table_num,
                            "caption": f"Table {table_num}: {caption}",
                            "caption_text": caption
                        })
                        
                        break
    
    def _match_captions_to_images(self) -> None:
        """
        Match figure captions to images based on proximity and references.
        """
        # Group figures by page
        figures_by_page = {}
        for fig in self.figures:
            page = fig["page"]
            if page not in figures_by_page:
                figures_by_page[page] = []
            figures_by_page[page].append(fig)
        
        # Process each page
        for page, page_figures in figures_by_page.items():
            # Find image and caption pairs
            images = [fig for fig in page_figures if fig["type"] == "image"]
            captions = [fig for fig in page_figures if "figure_number" in fig and fig["figure_number"]]
            
            # Match by position (assume captions are below images)
            for caption in captions:
                if "rect" not in caption or caption["rect"] is None:
                    continue
                
                caption_top = caption["rect"][1]
                best_match = None
                min_distance = float('inf')
                
                for img in images:
                    if "rect" not in img or img["rect"] is None:
                        continue
                    
                    img_bottom = img["rect"][3]
                    distance = caption_top - img_bottom
                    
                    # Caption should be below the image with minimal distance
                    if 0 <= distance < min_distance:
                        min_distance = distance
                        best_match = img
                
                if best_match:
                    # Update image with caption info
                    best_match["figure_number"] = caption["figure_number"]
                    best_match["caption"] = caption["caption"]
                    best_match["caption_text"] = caption["caption_text"]
    
    def _extract_tables(self, doc: fitz.Document) -> None:
        """
        Extract tables from the document.
        This is a basic implementation that could be enhanced with dedicated table extraction libraries.
        
        Args:
            doc (fitz.Document): PDF document
        """
        # For each page in the document
        for page_idx, page in enumerate(doc):
            # Get page text and find table captions
            page_captions = [t for t in self.tables if t["page"] == page_idx + 1]
            
            if not page_captions:
                continue
            
            # Take a screenshot of the page
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_np = np.array(img)
            
            # Convert to grayscale for processing
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            
            # For each caption, look for a table near it
            for caption in page_captions:
                if "rect" not in caption or caption["rect"] is None:
                    continue
                
                # Scale caption coordinates to match the pixmap
                caption_rect = [c * 2 for c in caption["rect"]]
                
                # Search for table grid lines slightly above the caption
                search_area = [
                    caption_rect[0],
                    max(0, caption_rect[1] - 500),  # Look above the caption
                    caption_rect[2],
                    caption_rect[1]
                ]
                
                # Crop the image to the search area
                search_img = gray[
                    int(search_area[1]):int(search_area[3]),
                    int(search_area[0]):int(search_area[2])
                ]
                
                # Detect horizontal and vertical lines (table borders)
                # This is a simplified detection that could be improved
                edges = cv2.Canny(search_img, 50, 150, apertureSize=3)
                lines = cv2.HoughLinesP(
                    edges, 1, np.pi/180, threshold=100,
                    minLineLength=50, maxLineGap=10
                )
                
                if lines is not None and len(lines) > 5:  # Assume it's a table if enough lines
                    # Save table image
                    filename = f"page{page_idx+1}_table{caption['table_number']}.png"
                    full_path = os.path.join(self.figure_dir, filename)
                    
                    # Save cropped table image
                    table_img = img.crop((
                        int(search_area[0]),
                        int(search_area[1]),
                        int(search_area[2]),
                        int(search_area[3])
                    ))
                    table_img.save(full_path)
                    
                    # Add to tables list
                    table_data = {
                        "type": "table",
                        "page": page_idx + 1,
                        "rect": search_area,
                        "filename": filename,
                        "file_path": full_path,
                        "table_number": caption["table_number"],
                        "caption": caption["caption"],
                        "caption_text": caption["caption_text"],
                        "web_path": f"/media/figures/{os.path.basename(self.figure_dir)}/{filename}"
                    }
                    
                    self.tables.append(table_data)
    
    def add_figures_to_vector_db(self) -> List[str]:
        """
        Add extracted figures to the vector database.
        
        Returns:
            list: List of IDs for the added figures
        """
        added_ids = []
        
        # Process figures
        for figure in self.figures:
            if "filename" not in figure or not figure["caption"]:
                continue
            
            # Prepare caption text for embedding
            text_content = figure["caption"]
            if figure["caption_text"]:
                text_content += f"\n\n{figure['caption_text']}"
            
            # Add reference to the figure number if available
            if figure["figure_number"]:
                text_content = f"Figure {figure['figure_number']}: {text_content}"
            
            # Convert image to base64 for embedding
            try:
                with open(figure["file_path"], "rb") as f:
                    img_data = f.read()
                base64_img = base64.b64encode(img_data).decode('utf-8')
            except Exception as e:
                print(f"Error reading image file: {e}")
                base64_img = None
            
            # Create metadata
            metadata = {
                "doc_type": "figure",
                "title": self.doc_metadata.get("title", "Untitled"),
                "author": self.doc_metadata.get("author", ""),
                "year": self.doc_metadata.get("year"),
                "figure_number": figure.get("figure_number"),
                "page": figure.get("page"),
                "caption": figure.get("caption", ""),
                "image_path": figure.get("web_path"),
                "image_data": base64_img[:100] + "..." if base64_img else None,  # Store truncated version in metadata
                "source": self.pdf_path
            }
            
            # Add to Weaviate
            obj_id = add_document_chunk_to_weaviate(text_content, metadata)
            if obj_id:
                added_ids.append(obj_id)
        
        # Process tables
        for table in self.tables:
            if "type" not in table or table["type"] != "table" or not table["caption"]:
                continue
            
            # Prepare caption text for embedding
            text_content = table["caption"]
            if table["caption_text"]:
                text_content += f"\n\n{table['caption_text']}"
            
            # Add reference to the table number if available
            if table["table_number"]:
                text_content = f"Table {table['table_number']}: {text_content}"
            
            # Convert image to base64 for embedding
            try:
                with open(table["file_path"], "rb") as f:
                    img_data = f.read()
                base64_img = base64.b64encode(img_data).decode('utf-8')
            except Exception as e:
                print(f"Error reading table image file: {e}")
                base64_img = None
            
            # Create metadata
            metadata = {
                "doc_type": "table",
                "title": self.doc_metadata.get("title", "Untitled"),
                "author": self.doc_metadata.get("author", ""),
                "year": self.doc_metadata.get("year"),
                "table_number": table.get("table_number"),
                "page": table.get("page"),
                "caption": table.get("caption", ""),
                "image_path": table.get("web_path"),
                "image_data": base64_img[:100] + "..." if base64_img else None,  # Store truncated version in metadata
                "source": self.pdf_path
            }
            
            # Add to Weaviate
            obj_id = add_document_chunk_to_weaviate(text_content, metadata)
            if obj_id:
                added_ids.append(obj_id)
        
        return added_ids
    
    def get_figures_json(self) -> str:
        """
        Get figures data as JSON.
        
        Returns:
            str: JSON string with figures data
        """
        figures_data = []
        
        # Process figures
        for figure in self.figures:
            if "filename" not in figure or not figure["caption"]:
                continue
            
            # Create figure data
            figure_data = {
                "type": "figure",
                "figure_number": figure.get("figure_number"),
                "page": figure.get("page"),
                "caption": figure.get("caption", ""),
                "image_path": figure.get("web_path")
            }
            
            figures_data.append(figure_data)
        
        # Process tables
        for table in self.tables:
            if "type" not in table or table["type"] != "table" or not table["caption"]:
                continue
            
            # Create table data
            table_data = {
                "type": "table",
                "table_number": table.get("table_number"),
                "page": table.get("page"),
                "caption": table.get("caption", ""),
                "image_path": table.get("web_path")
            }
            
            figures_data.append(table_data)
        
        return json.dumps(figures_data, indent=2)


def extract_figures_from_pdf(pdf_path: str, doc_metadata: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Extract figures from a PDF and add them to the vector database.
    
    Args:
        pdf_path (str): Path to the PDF file
        doc_metadata (dict): Metadata about the document
        
    Returns:
        tuple: (List of figure data, List of IDs for the added figures)
    """
    # Create figure extractor
    extractor = FigureExtractor(pdf_path, doc_metadata)
    
    # Extract figures
    figures = extractor.extract_all_figures()
    
    # Add to vector database
    added_ids = extractor.add_figures_to_vector_db()
    
    return figures, added_ids