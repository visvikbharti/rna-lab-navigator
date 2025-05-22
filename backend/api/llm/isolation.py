"""
Network isolation utilities for LLM operations.
Provides tools for monitoring and enforcing LLM network isolation.
"""

import os
import logging
import socket
import subprocess
import requests
from django.conf import settings
from django.core.cache import cache

# Set up logging
logger = logging.getLogger(__name__)

# Cache keys
ISOLATION_STATUS_CACHE_KEY = 'llm_isolation_status'
ISOLATION_CHECK_CACHE_TIMEOUT = 60 * 10  # 10 minutes

def check_isolation_status():
    """
    Check if LLM network isolation is properly configured and functioning.
    
    Returns:
        dict: Status information with fields:
            - isolated (bool): Whether isolation is active
            - local_available (bool): Whether local LLM is available
            - openai_blocked (bool): Whether OpenAI API is blocked
            - errors (list): Any error messages
    """
    # Check if result is cached
    cached_result = cache.get(ISOLATION_STATUS_CACHE_KEY)
    if cached_result:
        return cached_result
    
    result = {
        'isolated': False,
        'local_available': False,
        'openai_blocked': False,
        'errors': []
    }
    
    # Check if isolation is enabled in settings
    isolation_enabled = getattr(settings, 'LLM_NETWORK_ISOLATION', False)
    force_isolation = getattr(settings, 'LLM_FORCE_ISOLATION', False)
    
    if not isolation_enabled and not force_isolation:
        result['isolated'] = False
        result['errors'].append("Network isolation is not enabled in settings")
        cache.set(ISOLATION_STATUS_CACHE_KEY, result, ISOLATION_CHECK_CACHE_TIMEOUT)
        return result
    
    # Check if local LLM API is available
    local_llm_url = getattr(settings, 'OLLAMA_API_URL', None)
    if not local_llm_url:
        result['errors'].append("Local LLM URL not configured")
    else:
        try:
            response = requests.get(f"{local_llm_url.rstrip('/')}/api/version", timeout=5)
            if response.status_code == 200:
                result['local_available'] = True
                logger.info(f"Local LLM available at {local_llm_url}")
            else:
                result['errors'].append(f"Local LLM API returned status code {response.status_code}")
        except requests.RequestException as e:
            result['errors'].append(f"Failed to connect to local LLM API: {str(e)}")
    
    # Check if OpenAI API is blocked
    # In a real production environment, you would use network controls (e.g., firewall rules)
    # to block access. Here we're just checking connection capabilities.
    if isolation_enabled or force_isolation:
        openai_domains = ['api.openai.com', 'openai.com']
        openai_blocked = True
        
        for domain in openai_domains:
            try:
                # Try to resolve domain
                socket.gethostbyname(domain)
                
                # Try to connect to API endpoint
                test_response = requests.head(f"https://{domain}", timeout=5)
                
                if test_response.status_code < 500:  # Any response except server error
                    openai_blocked = False
                    result['errors'].append(f"Network isolation failure: {domain} is accessible")
                    break
            except (socket.gaierror, requests.RequestException):
                # This is actually good - it means the domain is blocked
                continue
        
        result['openai_blocked'] = openai_blocked
    
    # Determine overall isolation status
    if force_isolation:
        # If isolation is forced, both conditions must be met
        result['isolated'] = result['local_available'] and result['openai_blocked']
    else:
        # If isolation is enabled but not forced, local LLM must be available
        result['isolated'] = result['local_available']
    
    # Cache result
    cache.set(ISOLATION_STATUS_CACHE_KEY, result, ISOLATION_CHECK_CACHE_TIMEOUT)
    return result


def enforce_isolation():
    """
    Enforce LLM network isolation if configured.
    Throws exception if isolation is required but conditions are not met.
    """
    force_isolation = getattr(settings, 'LLM_FORCE_ISOLATION', False)
    
    if not force_isolation:
        return
    
    # Check isolation status
    status = check_isolation_status()
    
    if not status['isolated']:
        errors = status['errors']
        error_msg = "LLM network isolation is required but not properly configured."
        if errors:
            error_msg += f" Errors: {', '.join(errors)}"
        
        logger.error(error_msg)
        raise SecurityError(error_msg)


class SecurityError(Exception):
    """Exception raised for security policy violations."""
    pass


def get_recommended_isolation_settings():
    """
    Get recommended network isolation settings for the current environment.
    
    Returns:
        dict: Recommended settings
    """
    recommendations = {
        'LLM_NETWORK_ISOLATION': 'True',
        'LLM_FORCE_ISOLATION': 'True',
        'OLLAMA_API_URL': 'http://localhost:11434',
        'OLLAMA_DEFAULT_MODEL': 'llama3:8b',
        'LOCAL_EMBEDDING_MODEL_PATH': '/path/to/embedding_model.onnx',
        'LOCAL_EMBEDDING_TOKENIZER_PATH': '/path/to/tokenizer',
        'OLLAMA_TIMEOUT': '120',
        'network_rules': [
            'Block outbound connections to api.openai.com',
            'Block outbound connections to openai.com',
            'Allow localhost connections to Ollama API port 11434',
        ]
    }
    
    # Check if Ollama is installed
    try:
        result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
        if result.returncode == 0:
            ollama_path = result.stdout.strip()
            recommendations['ollama_installed'] = True
            recommendations['ollama_path'] = ollama_path
            
            # Check if any models are available
            models_result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if models_result.returncode == 0 and models_result.stdout.strip():
                models = [line.split()[0] for line in models_result.stdout.strip().split('\n')[1:]]
                recommendations['available_models'] = models
                if models:
                    recommendations['OLLAMA_DEFAULT_MODEL'] = models[0]
        else:
            recommendations['ollama_installed'] = False
            recommendations['installation_instructions'] = [
                'curl -fsSL https://ollama.com/install.sh | sh',
                'ollama serve &',
                'ollama pull llama3:8b'
            ]
    except (subprocess.SubprocessError, FileNotFoundError):
        recommendations['ollama_installed'] = False
        recommendations['installation_instructions'] = [
            'curl -fsSL https://ollama.com/install.sh | sh',
            'ollama serve &',
            'ollama pull llama3:8b'
        ]
    
    # Check for local embedding models
    sentencepiece_installed = False
    try:
        import onnxruntime
        import transformers
        sentencepiece_installed = True
        
        # Check for all-MiniLM-L6-v2 model
        model_dir = os.path.join(settings.BASE_DIR, 'models', 'all-MiniLM-L6-v2')
        if os.path.exists(model_dir):
            recommendations['LOCAL_EMBEDDING_MODEL_PATH'] = os.path.join(model_dir, 'model.onnx')
            recommendations['LOCAL_EMBEDDING_TOKENIZER_PATH'] = model_dir
        else:
            recommendations['embedding_model_instructions'] = [
                'mkdir -p models/all-MiniLM-L6-v2',
                'cd models/all-MiniLM-L6-v2',
                'python -c "from transformers import AutoTokenizer, AutoModel; tokenizer = AutoTokenizer.from_pretrained(\'sentence-transformers/all-MiniLM-L6-v2\'); model = AutoModel.from_pretrained(\'sentence-transformers/all-MiniLM-L6-v2\'); tokenizer.save_pretrained(\'.\'); model.save_pretrained(\'.\');"',
                'python -c "from transformers import AutoModel; from transformers.onnx import export; model = AutoModel.from_pretrained(\'.\'); export(tokenizer_or_preprocessor=None, model=model, opset=12, output=\'model.onnx\');"'
            ]
    except ImportError:
        recommendations['embedding_dependencies'] = [
            'pip install onnxruntime transformers sentencepiece torch'
        ]
    
    return recommendations