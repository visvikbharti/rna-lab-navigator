"""
Unit tests for document ingestion utilities.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock

from api.ingestion.chunking_utils import (
    chunk_text, 
    chunk_thesis_by_chapter, 
    split_into_sections
)
from api.ingestion.embeddings_utils import (
    create_embeddings, 
    create_document_embeddings
)
from api.ingestion.ingest_thesis import (
    extract_text_from_pdf, 
    process_thesis
)


def test_chunk_text():
    """Test text chunking with overlap."""
    text = "This is a test text. " * 100  # ~1800 characters
    
    # Test with default settings
    chunks = chunk_text(text)
    assert len(chunks) > 1
    
    # Verify chunks have reasonable size
    for chunk in chunks:
        assert len(chunk.split()) <= 500  # Max words per chunk
    
    # Test with custom settings
    custom_chunks = chunk_text(text, chunk_size=100, chunk_overlap=20)
    assert len(custom_chunks) > len(chunks)  # Should have more chunks with smaller size


def test_chunk_thesis_by_chapter():
    """Test thesis chunking by chapter."""
    thesis_text = """
    # CHAPTER 1: Introduction
    
    This is the introduction.
    
    # CHAPTER 2: Literature Review
    
    This is the literature review.
    
    # CHAPTER 3: Methodology
    
    This is the methodology section.
    """
    
    chunks = chunk_thesis_by_chapter(thesis_text)
    
    # Should have 3 chunks (one per chapter)
    assert len(chunks) == 3
    
    # Check content of chunks
    assert "Introduction" in chunks[0]
    assert "Literature Review" in chunks[1]
    assert "Methodology" in chunks[2]


def test_split_into_sections():
    """Test splitting text into sections."""
    text = """
    # Section 1
    Content for section 1.
    
    ## Subsection 1.1
    More content.
    
    # Section 2
    Content for section 2.
    """
    
    sections = split_into_sections(text)
    
    # Should have 2 main sections
    assert len(sections) == 2
    
    # Check content of sections
    assert "Section 1" in sections[0]
    assert "Subsection 1.1" in sections[0]
    assert "Section 2" in sections[1]


@patch('api.ingestion.embeddings_utils.get_llm_client')
def test_create_embeddings(mock_get_llm_client):
    """Test creating embeddings for text."""
    # Mock the embedding model
    mock_embedding_model = MagicMock()
    mock_embedding_model.create.return_value.data = [
        type('obj', (object,), {
            'embedding': [0.1] * 768,
            'index': 0
        })
    ]
    mock_get_llm_client.return_value.embeddings = mock_embedding_model
    
    # Test creating embeddings
    text = "This is a test text."
    embeddings = create_embeddings(text)
    
    # Verify output
    assert len(embeddings) == 768
    assert isinstance(embeddings, list)
    assert all(isinstance(x, float) for x in embeddings)
    
    # Verify API was called correctly
    mock_embedding_model.create.assert_called_once()
    args, kwargs = mock_embedding_model.create.call_args
    assert kwargs['input'] == text


@patch('api.ingestion.embeddings_utils.create_embeddings')
def test_create_document_embeddings(mock_create_embeddings):
    """Test creating embeddings for document chunks."""
    # Mock embedding function
    mock_create_embeddings.return_value = [0.1] * 768
    
    # Test creating document embeddings
    chunks = ["Chunk 1", "Chunk 2", "Chunk 3"]
    document_data = {
        "title": "Test Document",
        "content": "\n\n".join(chunks),
        "doc_type": "paper",
        "year": 2023,
        "authors": "Test Author"
    }
    
    embeddings = create_document_embeddings(document_data, chunks)
    
    # Verify output
    assert len(embeddings) == 3
    assert all(isinstance(e, dict) for e in embeddings)
    
    # Check required fields in each embedding
    for i, embedding in enumerate(embeddings):
        assert "title" in embedding
        assert "content" in embedding
        assert "doc_type" in embedding
        assert "year" in embedding
        assert "authors" in embedding
        assert "embedding" in embedding
        assert embedding["content"] == chunks[i]
    
    # Verify create_embeddings was called for each chunk
    assert mock_create_embeddings.call_count == 3


@patch('api.ingestion.ingest_thesis.PyPDF2.PdfReader')
def test_extract_text_from_pdf(mock_pdf_reader):
    """Test extracting text from PDF."""
    # Mock PDF reader
    mock_pdf = MagicMock()
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1 content."
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2 content."
    
    mock_pdf.pages = [mock_page1, mock_page2]
    mock_pdf_reader.return_value = mock_pdf
    
    # Test PDF text extraction
    with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
        text = extract_text_from_pdf(temp_file.name)
        
        # Verify output
        assert "Page 1 content." in text
        assert "Page 2 content." in text
        
        # Verify reader was called correctly
        mock_pdf_reader.assert_called_once_with(temp_file.name)


@patch('api.ingestion.ingest_thesis.extract_text_from_pdf')
@patch('api.ingestion.ingest_thesis.chunk_thesis_by_chapter')
@patch('api.ingestion.ingest_thesis.create_document_embeddings')
@patch('api.ingestion.ingest_thesis.get_vector_db_client')
def test_process_thesis(mock_get_vector_db, mock_create_embeddings, 
                        mock_chunk_thesis, mock_extract_text):
    """Test end-to-end thesis processing."""
    # Mock dependencies
    mock_extract_text.return_value = "# CHAPTER 1\nTest thesis content."
    mock_chunk_thesis.return_value = ["Test thesis content."]
    mock_create_embeddings.return_value = [{"content": "Test thesis content.", "embedding": [0.1] * 768}]
    
    mock_weaviate = MagicMock()
    mock_get_vector_db.return_value = mock_weaviate
    
    # Test thesis processing
    with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
        result = process_thesis(temp_file.name, "Test Author", 2023)
        
        # Verify output
        assert result['success'] is True
        assert result['chunks_created'] == 1
        
        # Verify Weaviate client was called correctly
        mock_weaviate.batch.create_objects.assert_called_once()
    
    # Test error handling
    mock_extract_text.side_effect = Exception("Test error")
    
    with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
        result = process_thesis(temp_file.name, "Test Author", 2023)
        
        # Verify error handling
        assert result['success'] is False
        assert "Test error" in result['error']