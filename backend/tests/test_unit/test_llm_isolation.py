"""
Unit tests for LLM network isolation functionality.
"""

import pytest
from unittest.mock import patch, MagicMock

from api.llm import get_llm_client, is_llm_isolated, get_embedding_model
from api.llm.isolation import check_isolation_status, enforce_isolation, SecurityError


@patch('api.llm.isolation.settings')
def test_is_llm_isolated(mock_settings):
    """Test checking if LLM is running in isolated mode."""
    # Test with isolation enabled
    mock_settings.LLM_NETWORK_ISOLATION = True
    assert is_llm_isolated() is True
    
    # Test with isolation disabled
    mock_settings.LLM_NETWORK_ISOLATION = False
    assert is_llm_isolated() is False


@patch('api.llm.isolation.settings')
@patch('api.llm.settings')
def test_get_llm_client(mock_settings, mock_isolation_settings):
    """Test getting appropriate LLM client based on settings."""
    # Test with isolation enabled
    mock_settings.LLM_NETWORK_ISOLATION = True
    mock_settings.OLLAMA_API_URL = "http://localhost:11434"
    mock_settings.OLLAMA_DEFAULT_MODEL = "llama3:8b"
    mock_isolation_settings.LLM_NETWORK_ISOLATION = True
    
    with patch('api.llm.local_llm.OllamaClient') as mock_ollama:
        client = get_llm_client(isolation_level="auto")
        # Verify Ollama client was used
        mock_ollama.assert_called_once()
    
    # Test with isolation disabled
    mock_settings.LLM_NETWORK_ISOLATION = False
    mock_isolation_settings.LLM_NETWORK_ISOLATION = False
    
    with patch('api.llm.openai.OpenAI') as mock_openai:
        client = get_llm_client(isolation_level="auto")
        # Verify OpenAI client was used
        mock_openai.assert_called_once()
    
    # Test with forced isolation
    with patch('api.llm.local_llm.OllamaClient') as mock_ollama:
        client = get_llm_client(isolation_level="isolated")
        # Verify Ollama client was used
        mock_ollama.assert_called_once()
    
    # Test with forced public API
    with patch('api.llm.openai.OpenAI') as mock_openai:
        client = get_llm_client(isolation_level="public")
        # Verify OpenAI client was used
        mock_openai.assert_called_once()


@patch('api.llm.isolation.requests.get')
@patch('api.llm.isolation.settings')
def test_check_isolation_status(mock_settings, mock_requests_get):
    """Test checking isolation status."""
    # Mock settings
    mock_settings.LLM_NETWORK_ISOLATION = True
    mock_settings.LLM_FORCE_ISOLATION = False
    mock_settings.OLLAMA_API_URL = "http://localhost:11434"
    
    # Mock successful Ollama API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_requests_get.return_value = mock_response
    
    # Test with local LLM available
    with patch('api.llm.isolation.socket.gethostbyname', side_effect=Exception("Domain blocked")):
        status = check_isolation_status()
        
        # Verify status
        assert status['isolated'] is True
        assert status['local_available'] is True
        assert status['openai_blocked'] is True
    
    # Test with local LLM unavailable
    mock_requests_get.side_effect = Exception("Connection failed")
    
    with patch('api.llm.isolation.socket.gethostbyname', side_effect=Exception("Domain blocked")):
        status = check_isolation_status()
        
        # Verify status
        assert status['isolated'] is False
        assert status['local_available'] is False
        assert status['openai_blocked'] is True
        assert len(status['errors']) > 0
    
    # Test with OpenAI accessible (not blocked)
    mock_requests_get.side_effect = None
    mock_requests_get.return_value = mock_response
    
    with patch('api.llm.isolation.socket.gethostbyname', return_value="127.0.0.1"):
        with patch('api.llm.isolation.requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            
            status = check_isolation_status()
            
            # Verify status
            assert status['isolated'] is False
            assert status['local_available'] is True
            assert status['openai_blocked'] is False
            assert len(status['errors']) > 0


@patch('api.llm.isolation.check_isolation_status')
@patch('api.llm.isolation.settings')
def test_enforce_isolation(mock_settings, mock_check_status):
    """Test enforcing isolation."""
    # Test with isolation not forced
    mock_settings.LLM_FORCE_ISOLATION = False
    
    # Should not raise error
    enforce_isolation()
    
    # Test with isolation forced and compliant
    mock_settings.LLM_FORCE_ISOLATION = True
    mock_check_status.return_value = {
        'isolated': True,
        'local_available': True,
        'openai_blocked': True,
        'errors': []
    }
    
    # Should not raise error
    enforce_isolation()
    
    # Test with isolation forced but not compliant
    mock_check_status.return_value = {
        'isolated': False,
        'local_available': False,
        'openai_blocked': False,
        'errors': ['Local LLM unavailable', 'OpenAI accessible']
    }
    
    # Should raise SecurityError
    with pytest.raises(SecurityError):
        enforce_isolation()


@patch('api.llm.settings')
def test_get_embedding_model(mock_settings):
    """Test getting appropriate embedding model based on settings."""
    # Test with isolation enabled
    mock_settings.LLM_NETWORK_ISOLATION = True
    
    with patch('api.llm.local_embeddings.LocalEmbeddingModel') as mock_local_model:
        model = get_embedding_model()
        # Verify local model was used
        mock_local_model.assert_called_once()
    
    # Test with isolation disabled
    mock_settings.LLM_NETWORK_ISOLATION = False
    
    with patch('api.llm.openai_embeddings.OpenAIEmbeddingModel') as mock_openai_model:
        model = get_embedding_model()
        # Verify OpenAI model was used
        mock_openai_model.assert_called_once()