"""
Tests for the query API endpoint.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from api.models import QueryHistory


@pytest.mark.django_db
def test_query_endpoint_authenticated(authenticated_client, mock_openai, mock_weaviate, sample_query_request):
    """Test that authenticated users can query the API."""
    client, user = authenticated_client
    url = reverse('query')
    
    response = client.post(url, sample_query_request, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    assert 'answer' in response.data
    assert 'sources' in response.data
    assert 'confidence_score' in response.data
    
    # Verify history was created
    history = QueryHistory.objects.filter(user=user).first()
    assert history is not None
    assert history.question == sample_query_request['question']
    assert history.doc_type == sample_query_request['doc_type']


@pytest.mark.django_db
def test_query_endpoint_unauthenticated(api_client, mock_openai, mock_weaviate, sample_query_request):
    """Test that unauthenticated users cannot query the API."""
    url = reverse('query')
    
    response = api_client.post(url, sample_query_request, format='json')
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_query_with_invalid_data(authenticated_client):
    """Test query with invalid data returns appropriate error."""
    client, _ = authenticated_client
    url = reverse('query')
    
    # Missing required field
    response = client.post(url, {"doc_type": "all"}, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Invalid doc_type
    response = client.post(url, {
        "question": "What is RNA?",
        "doc_type": "invalid_type"
    }, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_query_with_empty_question(authenticated_client):
    """Test query with empty question returns appropriate error."""
    client, _ = authenticated_client
    url = reverse('query')
    
    response = client.post(url, {
        "question": "",
        "doc_type": "all"
    }, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_query_with_filtered_doc_type(authenticated_client, mock_openai, mock_weaviate):
    """Test query with specific document type filter."""
    client, _ = authenticated_client
    url = reverse('query')
    
    # Test with paper doc_type
    response = client.post(url, {
        "question": "What is RNA?",
        "doc_type": "paper"
    }, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    
    # Mock was called with the correct doc_type filter
    mock_call_args = mock_weaviate.query.get.call_args_list
    assert len(mock_call_args) > 0
    
    # Test with thesis doc_type
    response = client.post(url, {
        "question": "What is RNA?",
        "doc_type": "thesis"
    }, format='json')
    
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_query_history_record(authenticated_client, mock_openai, mock_weaviate, sample_query_request):
    """Test that query history is recorded correctly with feedback."""
    client, user = authenticated_client
    url = reverse('query')
    
    # Make the query
    response = client.post(url, sample_query_request, format='json')
    assert response.status_code == status.HTTP_200_OK
    
    # Verify history record
    history = QueryHistory.objects.filter(user=user).first()
    assert history is not None
    assert history.question == sample_query_request['question']
    
    # Add feedback to the query
    feedback_url = reverse('feedback-list')
    feedback_data = {
        'query_id': str(history.id),
        'rating': 'positive',
        'comments': 'This was helpful'
    }
    
    feedback_response = client.post(feedback_url, feedback_data, format='json')
    assert feedback_response.status_code == status.HTTP_201_CREATED
    
    # Check that history has feedback
    history.refresh_from_db()
    assert history.feedback is not None
    assert history.feedback.rating == 'positive'


@pytest.mark.django_db
def test_query_with_threshold(authenticated_client, mock_openai, mock_weaviate):
    """Test query with custom confidence threshold."""
    client, _ = authenticated_client
    url = reverse('query')
    
    # Test with high threshold
    response = client.post(url, {
        "question": "What is RNA?",
        "doc_type": "all",
        "threshold": 0.9  # Higher threshold
    }, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    
    # Test with low threshold
    response = client.post(url, {
        "question": "What is RNA?",
        "doc_type": "all",
        "threshold": 0.1  # Lower threshold
    }, format='json')
    
    assert response.status_code == status.HTTP_200_OK