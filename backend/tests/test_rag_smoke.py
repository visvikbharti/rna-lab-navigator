"""
Simple smoke test for the RAG pipeline.
This test verifies basic functionality without complex mocks.
"""

import pytest
from django.conf import settings
from api.ingestion.chunking_utils import chunk_text, split_by_chapter

@pytest.mark.django_db
def test_chunking_functions():
    """Test basic text chunking functionality."""
    # Test text
    sample_text = "This is a test word " * 1000  # Create text with 1000 words
    
    # Test chunking with default settings
    chunks = chunk_text(sample_text)
    
    # Verify multiple chunks were created
    assert len(chunks) > 1
    
    # Verify chunks are approximately the right size
    for chunk in chunks:
        words = chunk.split()
        assert len(words) <= settings.CHUNK_SIZE + 50
    
    # Test chapter splitting
    chapter_text = """
    CHAPTER 1: Introduction
    
    This is the introduction chapter.
    
    CHAPTER 2: Literature Review
    
    This is the literature review chapter.
    """
    
    chapters = split_by_chapter(chapter_text)
    assert len(chapters) == 2


@pytest.mark.django_db
def test_settings_consistency():
    """Test that settings adhere to golden rules."""
    # Verify the chunking sizes follow the golden rule
    assert 350 <= settings.CHUNK_SIZE <= 450, "Chunk size should be 400 ± 50 words"
    assert settings.CHUNK_OVERLAP == 100, "Chunk overlap should be 100 words"