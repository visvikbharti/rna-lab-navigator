"""
Utility functions for chunking documents into manageable pieces.
Implements the "Chunking = 400 ± 50 words, 100-word overlap" golden rule.
"""

import re
from django.conf import settings


def chunk_text(text, chunk_size=None, chunk_overlap=None):
    """
    Split text into chunks of approximately chunk_size words with chunk_overlap words of overlap.
    
    Args:
        text (str): The text to be chunked
        chunk_size (int, optional): Target size for chunks in words. Defaults to settings.CHUNK_SIZE.
        chunk_overlap (int, optional): Number of words to overlap. Defaults to settings.CHUNK_OVERLAP.
        
    Returns:
        list: List of text chunks
    """
    # Using defaults from settings if not provided
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    # Check if text is empty or None
    if not text:
        return []
    
    # Normalize whitespace and split into words
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split(' ')
    
    # Return the entire text as one chunk if it's shorter than the chunk size
    if len(words) <= chunk_size:
        return [text]
    
    # Calculate the step size (chunk size - overlap)
    step_size = chunk_size - chunk_overlap
    
    # Generate chunks
    chunks = []
    for i in range(0, len(words), step_size):
        # Get chunk_size words or remaining words if less than chunk_size
        chunk_words = words[i:i + chunk_size]
        # Join words back into a string
        chunk = ' '.join(chunk_words)
        # Only add non-empty chunks
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks


def split_by_chapter(text):
    """
    Split text by chapter headings (for thesis documents).
    
    Args:
        text (str): Full text of the document
        
    Returns:
        dict: Dictionary with chapter numbers as keys and chapter text as values
    """
    if not text:
        return {}
    
    # Regular expression to find chapter headings
    # This regex matches common chapter heading patterns like "CHAPTER 1", "Chapter 1:", etc.
    chapter_pattern = re.compile(r'(?i)(CHAPTER\s+(\d+|[IVXLCDM]+)[\s\.:]*)(.*?)(?=(CHAPTER\s+(\d+|[IVXLCDM]+)[\s\.:]*|$))', re.DOTALL)
    
    chapters = {}
    
    # Find all chapters
    matches = chapter_pattern.findall(text)
    
    # If no chapters found, return the entire text as "Introduction"
    if not matches:
        # Check if there's any meaningful content
        if len(text.strip()) > 100:  # Arbitrary threshold to avoid empty or nearly empty texts
            chapters["Introduction"] = text
        return chapters
    
    # Process each chapter
    for match in matches:
        chapter_heading = match[0].strip()  # Full chapter heading
        chapter_number = match[1].strip()   # Just the number part
        chapter_content = match[2].strip()  # The content after the heading
        
        # Normalize roman numerals to arabic if needed
        try:
            # This will work for arabic numerals
            chapter_key = int(chapter_number)
        except ValueError:
            # For roman numerals or other formats, keep as string
            chapter_key = chapter_number
        
        chapters[str(chapter_key)] = chapter_content
    
    return chapters


def chunk_thesis_by_chapter(text):
    """
    Split thesis text into chunks based on chapters and then chunk each chapter.
    
    Args:
        text (str): The full text of the thesis
        
    Returns:
        list: List of text chunks
    """
    if not text:
        return []
    
    # First split by chapters
    chapters = split_by_chapter(text)
    
    # If no chapters were found, chunk the entire text
    if not chapters:
        return chunk_text(text)
    
    # Chunk each chapter separately
    all_chunks = []
    for chapter_num, chapter_text in chapters.items():
        # Create a chapter header that will be included in each chunk
        chapter_header = f"CHAPTER {chapter_num}: "
        
        # Get chunks for this chapter
        chapter_chunks = chunk_text(chapter_text)
        
        # Add chapter header to each chunk for context
        for chunk in chapter_chunks:
            all_chunks.append(f"{chapter_header}{chunk}")
    
    return all_chunks


def split_into_sections(text):
    """
    Split text into sections based on markdown-style headers.
    
    Args:
        text (str): The text to split
        
    Returns:
        list: List of sections
    """
    if not text:
        return []
    
    # Regular expression to find section headings (# Header or ## Subheader)
    section_pattern = re.compile(r'(^|\n)#\s+([^\n]+)($|\n)', re.MULTILINE)
    
    # Find all section positions
    matches = list(section_pattern.finditer(text))
    
    if not matches:
        return [text] if text.strip() else []
    
    sections = []
    
    # Process each section
    for i, match in enumerate(matches):
        start_pos = match.start()
        
        # Determine end position (start of next section or end of text)
        if i < len(matches) - 1:
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)
        
        # Extract section text
        section_text = text[start_pos:end_pos].strip()
        if section_text:
            sections.append(section_text)
    
    # Check if there's content before the first section
    if matches and matches[0].start() > 0:
        preamble = text[:matches[0].start()].strip()
        if preamble:
            sections.insert(0, preamble)
    
    return sections