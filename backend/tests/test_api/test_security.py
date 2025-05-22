"""
Tests for the security features of the API.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_rate_limiting(authenticated_client, settings):
    """Test that rate limiting is enforced."""
    # Enable rate limiting for test
    settings.ENABLE_RATE_LIMITING = True
    settings.RATE_LIMIT_DEFAULT = "2/minute"  # Set a very low limit for testing
    
    client, _ = authenticated_client
    url = reverse('query')
    
    data = {
        "question": "What is RNA?",
        "doc_type": "all"
    }
    
    # First request should succeed
    response1 = client.post(url, data, format='json')
    assert response1.status_code == status.HTTP_200_OK
    
    # Second request should succeed
    response2 = client.post(url, data, format='json')
    assert response2.status_code == status.HTTP_200_OK
    
    # Third request should be rate limited
    response3 = client.post(url, data, format='json')
    assert response3.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_waf_protection(authenticated_client, settings):
    """Test that WAF protection blocks malicious requests."""
    # Enable WAF for test
    settings.WAF_ENABLED = True
    settings.WAF_SECURITY_LEVEL = 'medium'
    
    client, _ = authenticated_client
    url = reverse('query')
    
    # Test SQL injection attempt
    sql_injection_data = {
        "question": "'; DROP TABLE users; --",
        "doc_type": "all"
    }
    
    response = client.post(url, sql_injection_data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Test XSS attempt
    xss_data = {
        "question": "<script>alert('XSS')</script>",
        "doc_type": "all"
    }
    
    response = client.post(url, xss_data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_jwt_token_auth(api_client, db):
    """Test JWT token authentication flow."""
    # Create a user
    from django.contrib.auth.models import User
    User.objects.create_user(username='testuser', password='testpassword')
    
    # Try to access a protected endpoint without authentication
    url = reverse('query-history-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Get JWT token
    token_url = reverse('token_obtain_pair')
    token_response = api_client.post(
        token_url, 
        {'username': 'testuser', 'password': 'testpassword'},
        format='json'
    )
    assert token_response.status_code == status.HTTP_200_OK
    assert 'access' in token_response.data
    
    # Access protected endpoint with token
    access_token = token_response.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_role_based_access_control(authenticated_client, admin_client):
    """Test role-based access control for admin endpoints."""
    # Regular user client
    regular_client, _ = authenticated_client
    
    # Admin client
    admin_api_client, _ = admin_client
    
    # Try to access an admin-only endpoint with regular user
    url = '/api/admin/metrics/'  # Example admin endpoint
    response = regular_client.get(url)
    assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    # Access with admin user should succeed
    response = admin_api_client.get(url)
    assert response.status_code != status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_security_headers(authenticated_client):
    """Test that security headers are properly set."""
    client, _ = authenticated_client
    url = reverse('health-check')
    
    response = client.get(url)
    
    # Check for security headers
    assert 'X-Content-Type-Options' in response.headers
    assert 'X-Frame-Options' in response.headers
    assert 'X-XSS-Protection' in response.headers
    
    # Check header values
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'


@pytest.mark.django_db
def test_csrf_protection(authenticated_client):
    """Test CSRF protection for browser-based requests."""
    client, _ = authenticated_client
    
    # Simulate a request from a browser
    client.defaults['HTTP_USER_AGENT'] = 'Mozilla/5.0'
    client.defaults['HTTP_ACCEPT'] = 'text/html'
    
    # This should return a CSRF cookie
    response = client.get('/')
    assert 'csrftoken' in response.cookies
    
    # Now try a POST without CSRF token
    url = reverse('query')
    client.defaults['HTTP_X_CSRFTOKEN'] = ''  # Invalid token
    
    response = client.post(url, {
        "question": "What is RNA?",
        "doc_type": "all"
    }, format='json')
    
    # Should be rejected due to CSRF protection
    assert response.status_code == status.HTTP_403_FORBIDDEN