"""
Integration tests for the Retrieval-Augmented Generation (RAG) pipeline.
Tests the complete flow from query to answer generation.
"""

import pytest
from unittest.mock import patch, MagicMock

from api.views import QueryView
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_full_rag_pipeline(authenticated_client, mock_openai, mock_weaviate, sample_query_request):
    """Test the full RAG pipeline from query to answer."""
    client, _ = authenticated_client
    url = reverse('query')
    
    # Make the query
    response = client.post(url, sample_query_request, format='json')
    
    # Verify response
    assert response.status_code == status.HTTP_200_OK
    assert 'answer' in response.data
    assert 'sources' in response.data
    assert 'confidence_score' in response.data
    
    # Verify the proper components were called
    assert mock_weaviate.query.get.called  # Vector search was performed
    assert mock_openai.chat.create.called  # LLM was called for answer generation


@pytest.mark.django_db
@patch('api.views.get_vector_db_client')
@patch('api.views.get_llm_client')
def test_query_retrieval_flow(mock_get_llm, mock_get_vector_db, authenticated_client, sample_query_request):
    """Test the query and retrieval flow in detail."""
    # Set up complex mocks to test the flow
    mock_vector_db = MagicMock()
    mock_get_vector_db.return_value = mock_vector_db
    
    mock_query_builder = MagicMock()
    mock_vector_db.query.get.return_value = mock_query_builder
    
    mock_near_text = MagicMock()
    mock_query_builder.with_near_text.return_value = mock_near_text
    
    mock_with_additional = MagicMock()
    mock_near_text.with_additional.return_value = mock_with_additional
    
    mock_with_limit = MagicMock()
    mock_with_additional.with_limit.return_value = mock_with_limit
    
    # Mock the search results
    mock_with_limit.do.return_value = {
        "data": {
            "Get": {
                "Document": [
                    {
                        "title": "RNA Biology Basics",
                        "content": "RNA is a nucleic acid that plays various roles in the cell.",
                        "doc_type": "paper",
                        "year": 2023,
                        "authors": "Test Author",
                        "source": "test_source.pdf",
                        "_additional": {
                            "certainty": 0.95,
                            "distance": 0.05
                        }
                    },
                    {
                        "title": "RNA Functions",
                        "content": "RNA can function as a messenger, transfer, or ribosomal molecule.",
                        "doc_type": "paper",
                        "year": 2022,
                        "authors": "Another Author",
                        "source": "functions.pdf",
                        "_additional": {
                            "certainty": 0.92,
                            "distance": 0.08
                        }
                    }
                ]
            }
        }
    }
    
    # Mock LLM response
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm
    
    mock_chat = MagicMock()
    mock_llm.chat = mock_chat
    
    mock_chat.create.return_value.choices = [
        type('obj', (object,), {
            'message': type('obj', (object,), {
                'content': 'RNA is a nucleic acid that plays various roles in the cell, including messenger RNA, transfer RNA, and ribosomal RNA. [Source 1] [Source 2]'
            }),
            'finish_reason': 'stop'
        })
    ]
    
    # Make the query
    client, _ = authenticated_client
    url = reverse('query')
    response = client.post(url, sample_query_request, format='json')
    
    # Verify the response
    assert response.status_code == status.HTTP_200_OK
    assert 'answer' in response.data
    assert 'sources' in response.data
    assert len(response.data['sources']) == 2
    
    # Verify that the vector search was performed correctly
    mock_vector_db.query.get.assert_called_once_with('Document')
    
    # For Weaviate's API, verify the search parameters
    mock_query_builder.with_near_text.assert_called_once()
    near_text_args = mock_query_builder.with_near_text.call_args[0][0]
    assert 'concepts' in near_text_args
    assert near_text_args['concepts'] == sample_query_request['question']
    
    # Verify the prompt sent to the LLM contains the retrieved documents
    llm_call_args = mock_chat.create.call_args[1]
    assert 'messages' in llm_call_args
    
    # The prompt should contain the retrieved documents
    system_message = llm_call_args['messages'][0]['content']
    assert 'RNA is a nucleic acid' in system_message
    assert 'RNA can function as a messenger' in system_message


@pytest.mark.django_db
def test_citation_requirement(authenticated_client, mock_openai, mock_weaviate, sample_query_request):
    """Test that answers require citations to sources."""
    client, _ = authenticated_client
    url = reverse('query')
    
    # First test: LLM includes citations
    mock_openai.chat.create.return_value.choices = [
        type('obj', (object,), {
            'message': type('obj', (object,), {
                'content': 'RNA is important in cellular processes. [Source 1]'
            }),
            'finish_reason': 'stop'
        })
    ]
    
    response = client.post(url, sample_query_request, format='json')
    assert response.status_code == status.HTTP_200_OK
    
    # Second test: LLM does not include citations
    mock_openai.chat.create.return_value.choices = [
        type('obj', (object,), {
            'message': type('obj', (object,), {
                'content': 'RNA is important in cellular processes.'  # No citation
            }),
            'finish_reason': 'stop'
        })
    ]
    
    # This should still work but have a warning or lower confidence
    response = client.post(url, sample_query_request, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['confidence_score'] < 0.5  # Lower confidence for no citations


@pytest.mark.django_db
def test_low_confidence_handling(authenticated_client, mock_openai, mock_weaviate):
    """Test handling of low confidence results."""
    client, _ = authenticated_client
    url = reverse('query')
    
    # Mock very low relevance results from vector search
    mock_weaviate.query.get.return_value.with_near_text.return_value.with_additional.return_value.with_limit.return_value.do.return_value = {
        "data": {
            "Get": {
                "Document": [
                    {
                        "title": "Unrelated Topic",
                        "content": "This is completely unrelated content.",
                        "doc_type": "paper",
                        "year": 2023,
                        "authors": "Test Author",
                        "source": "unrelated.pdf",
                        "_additional": {
                            "certainty": 0.3,  # Very low certainty
                            "distance": 0.7
                        }
                    }
                ]
            }
        }
    }
    
    # Query about RNA
    query_request = {
        "question": "What is the structure of RNA?",
        "doc_type": "all",
        "threshold": 0.7  # High threshold
    }
    
    response = client.post(url, query_request, format='json')
    
    # Should indicate low confidence or no good matches
    assert response.status_code == status.HTTP_200_OK
    assert 'confidence_score' in response.data
    assert response.data['confidence_score'] < 0.5
    assert "I don't know" in response.data['answer'] or "No relevant information" in response.data['answer']