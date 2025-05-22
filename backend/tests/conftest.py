"""
Pytest configuration file for RNA Lab Navigator backend.
Provides fixtures and configuration for test environment.
"""

import os
import json
import pytest
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from unittest.mock import patch


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Configure test database settings."""
    with django_db_blocker.unblock():
        # Any database initialization for testing can be done here
        pass


@pytest.fixture
def api_client():
    """Return a Django Rest Framework API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    """Return an authenticated API client."""
    client = APIClient()
    user = User.objects.create_user(
        username="test_user", 
        password="test_password",
        email="test@example.com"
    )
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def admin_client(db):
    """Return an API client authenticated as admin."""
    client = APIClient()
    admin_user = User.objects.create_user(
        username="admin_user", 
        password="admin_password",
        email="admin@example.com",
        is_staff=True,
        is_superuser=True
    )
    client.force_authenticate(user=admin_user)
    return client, admin_user


@pytest.fixture
def mock_openai():
    """Mock OpenAI API responses."""
    with patch("openai.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        
        # Mock chat completion
        mock_chat = mock_client.chat
        mock_chat.create.return_value.choices = [
            type('obj', (object,), {
                'message': type('obj', (object,), {
                    'content': 'This is a mock response from the language model.'
                }),
                'finish_reason': 'stop'
            })
        ]
        
        # Mock embeddings
        mock_embeddings = mock_client.embeddings
        mock_embeddings.create.return_value = type('obj', (object,), {
            'data': [
                type('obj', (object,), {
                    'embedding': [0.1] * 768,
                    'index': 0
                })
            ],
            'model': 'text-embedding-ada-002',
            'usage': {
                'prompt_tokens': 8,
                'total_tokens': 8
            }
        })
        
        yield mock_client


@pytest.fixture
def mock_weaviate():
    """Mock Weaviate client responses."""
    with patch("weaviate.Client") as mock_weaviate:
        mock_client = mock_weaviate.return_value
        
        # Mock get
        mock_get = mock_client.get
        mock_get.return_value.with_additional.return_value.with_limit.return_value.do.return_value = {
            "data": {
                "Get": {
                    "Document": [
                        {
                            "title": "Test Document",
                            "content": "This is test content.",
                            "doc_type": "paper",
                            "year": 2023,
                            "authors": "Test Author",
                            "source": "test_source.pdf",
                            "_additional": {
                                "certainty": 0.95,
                                "distance": 0.05
                            }
                        }
                    ]
                }
            }
        }
        
        # Mock query
        mock_query = mock_client.query
        mock_query.get.return_value.with_near_text.return_value.with_additional.return_value.with_limit.return_value.do.return_value = {
            "data": {
                "Get": {
                    "Document": [
                        {
                            "title": "Test Document",
                            "content": "This is test content.",
                            "doc_type": "paper",
                            "year": 2023,
                            "authors": "Test Author",
                            "source": "test_source.pdf",
                            "_additional": {
                                "certainty": 0.95,
                                "distance": 0.05
                            }
                        }
                    ]
                }
            }
        }
        
        yield mock_client


@pytest.fixture
def sample_query_request():
    """Return a sample query request data."""
    return {
        "question": "What is RNA?",
        "doc_type": "all",
        "max_results": 5,
        "threshold": 0.7
    }


@pytest.fixture
def sample_document_data():
    """Return sample document data."""
    return {
        "title": "Test Document",
        "content": "This is a test document about RNA biology.",
        "doc_type": "paper",
        "year": 2023,
        "authors": "Test Author",
        "source": "test_source.pdf"
    }


@pytest.fixture
def sample_thesis_text():
    """Return sample thesis text for testing."""
    return """
    # CHAPTER 1: Introduction
    
    This is a sample introduction to the thesis.
    It contains information about RNA biology.
    
    # CHAPTER 2: Literature Review
    
    This chapter reviews the literature on RNA.
    
    # CHAPTER 3: Methodology
    
    This chapter describes the methods used.
    
    # CHAPTER 4: Results
    
    Here are the results of the study.
    
    # CHAPTER 5: Discussion
    
    This chapter discusses the implications of the results.
    
    # CHAPTER 6: Conclusion
    
    In conclusion, RNA is important for many biological processes.
    """


@pytest.fixture
def mock_pdf_path(tmp_path):
    """Create a mock PDF file for testing."""
    pdf_path = tmp_path / "test.pdf"
    # Create an empty file - for tests that just need the path
    pdf_path.write_bytes(b"%PDF-1.5\n%Test PDF file for testing")
    return str(pdf_path)


@pytest.fixture
def disable_rate_limits(settings):
    """Disable rate limits for testing."""
    settings.ENABLE_RATE_LIMITING = False
    return settings


@pytest.fixture
def disable_waf(settings):
    """Disable WAF for testing."""
    settings.WAF_ENABLED = False
    return settings