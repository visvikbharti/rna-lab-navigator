"""
Local LLM integration for network-isolated environments.
Provides access to on-premises language models through Ollama or other providers.
"""

import os
import json
import logging
import requests
from django.conf import settings

# Set up logging
logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Client for interacting with Ollama LLM API.
    Provides an interface compatible with the OpenAI client.
    """
    
    def __init__(self, base_url=None):
        """
        Initialize Ollama client.
        
        Args:
            base_url (str, optional): Ollama API base URL. Defaults to settings.OLLAMA_API_URL.
        """
        self.base_url = base_url or settings.OLLAMA_API_URL
        self.default_model = settings.OLLAMA_DEFAULT_MODEL
        self.timeout = getattr(settings, 'OLLAMA_TIMEOUT', 60)
        logger.info(f"Initialized Ollama client with base_url={self.base_url}")
    
    def _request(self, endpoint, method="POST", data=None, params=None):
        """
        Make a request to the Ollama API.
        
        Args:
            endpoint (str): API endpoint to call
            method (str, optional): HTTP method. Defaults to "POST".
            data (dict, optional): Request body data. Defaults to None.
            params (dict, optional): URL parameters. Defaults to None.
        
        Returns:
            dict: API response
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=self.timeout)
            else:
                response = requests.post(url, json=data, params=params, timeout=self.timeout)
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error calling Ollama API at {url}: {str(e)}")
            raise
    
    def chat(self):
        """
        Create a ChatCompletion object, similar to OpenAI's client.
        """
        return OllamaChatCompletion(self)


class OllamaChatCompletion:
    """
    ChatCompletion class for Ollama, providing an interface similar to OpenAI's.
    """
    
    def __init__(self, client):
        """
        Initialize ChatCompletion with Ollama client.
        
        Args:
            client (OllamaClient): Ollama client instance
        """
        self.client = client
    
    def create(self, model=None, messages=None, temperature=0.7, max_tokens=None, stream=False, **kwargs):
        """
        Create a chat completion with Ollama.
        
        Args:
            model (str, optional): Model to use. Defaults to client's default_model.
            messages (list, optional): List of message dictionaries. Defaults to None.
            temperature (float, optional): Sampling temperature. Defaults to 0.7.
            max_tokens (int, optional): Maximum tokens to generate. Defaults to None.
            stream (bool, optional): Whether to stream the response. Defaults to False.
            **kwargs: Additional parameters to pass to the API.
        
        Returns:
            dict: API response
        """
        model = model or self.client.default_model
        
        # Format messages for Ollama
        formatted_messages = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            # Handle system messages as a special case
            if role == 'system':
                # Ollama doesn't support system messages directly, so we'll add it as context
                kwargs['system'] = content
                continue
            
            formatted_messages.append({
                'role': role,
                'content': content
            })
        
        # Prepare request data
        data = {
            'model': model,
            'messages': formatted_messages,
            'stream': stream,
            'options': {
                'temperature': temperature,
            }
        }
        
        # Add max_tokens if specified
        if max_tokens:
            data['options']['num_predict'] = max_tokens
        
        # Add additional options from kwargs
        for key, value in kwargs.items():
            if key != 'system':  # Already handled
                data['options'][key] = value
        
        # Make the request
        try:
            if stream:
                # For streaming, we need to handle differently
                return OllamaStreamingResponse(self.client, data)
            else:
                response = self.client._request('/api/chat', data=data)
                return OllamaResponse(response)
        except Exception as e:
            logger.error(f"Error creating chat completion: {str(e)}")
            raise


class OllamaResponse:
    """
    Response object for Ollama API, mimicking OpenAI's response structure.
    """
    
    def __init__(self, raw_response):
        """
        Initialize with raw Ollama response.
        
        Args:
            raw_response (dict): Raw response from Ollama API
        """
        self.raw_response = raw_response
        self.id = raw_response.get('id', 'ollama-response')
        self.created = raw_response.get('created', 0)
        self.model = raw_response.get('model', 'unknown')
        
        # Format choices to match OpenAI's structure
        self.choices = [{
            'index': 0,
            'message': {
                'role': 'assistant',
                'content': raw_response.get('message', {}).get('content', '')
            },
            'finish_reason': 'stop'
        }]
        
        # Add usage information if available
        self.usage = {
            'prompt_tokens': raw_response.get('prompt_eval_count', 0),
            'completion_tokens': raw_response.get('eval_count', 0),
            'total_tokens': raw_response.get('prompt_eval_count', 0) + raw_response.get('eval_count', 0)
        }
    
    def model_dump_json(self):
        """Serialize to JSON, mimicking OpenAI's pydantic models."""
        return json.dumps({
            'id': self.id,
            'created': self.created,
            'model': self.model,
            'choices': self.choices,
            'usage': self.usage
        })


class OllamaStreamingResponse:
    """
    Streaming response iterator for Ollama API.
    """
    
    def __init__(self, client, data):
        """
        Initialize streaming response.
        
        Args:
            client (OllamaClient): Ollama client instance
            data (dict): Request data
        """
        self.client = client
        self.data = data
        
        # Prepare the streaming request
        url = f"{client.base_url.rstrip('/')}/api/chat"
        self.response = requests.post(url, json=data, stream=True)
        self.response.raise_for_status()
        self.iterator = self.response.iter_lines()
    
    def __iter__(self):
        return self
    
    def __next__(self):
        """Get next chunk from streaming response."""
        try:
            line = next(self.iterator)
            if line:
                chunk = json.loads(line)
                
                # Format chunk to match OpenAI's streaming format
                return {
                    'id': chunk.get('id', 'ollama-response'),
                    'created': chunk.get('created', 0),
                    'model': chunk.get('model', 'unknown'),
                    'choices': [{
                        'index': 0,
                        'delta': {
                            'role': 'assistant' if 'role' in chunk else None,
                            'content': chunk.get('message', {}).get('content', '')
                        },
                        'finish_reason': 'stop' if chunk.get('done', False) else None
                    }]
                }
            return None
        except StopIteration:
            self.response.close()
            raise
        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}")
            self.response.close()
            raise


def get_ollama_client():
    """
    Get an Ollama client instance.
    
    Returns:
        OllamaClient: Configured client instance
    """
    return OllamaClient()