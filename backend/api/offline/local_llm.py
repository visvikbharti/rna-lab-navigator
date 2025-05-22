"""
Local LLM inference module for offline/air-gapped operation.
Uses llama.cpp and sentence-transformers for embedding generation in offline mode.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import json

from django.conf import settings
from sentence_transformers import SentenceTransformer

# Try to import llama_cpp, with graceful fallback
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logging.warning("llama_cpp not available. Install with: pip install llama-cpp-python")

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Message class to mimic OpenAI API structure"""
    role: str
    content: str


@dataclass
class Choice:
    """Choice class to mimic OpenAI API structure"""
    message: Message
    index: int = 0
    finish_reason: str = "stop"


@dataclass
class LLMResponse:
    """Response class to mimic OpenAI API structure"""
    id: str = "local-llm"
    choices: List[Choice] = None
    created: int = 0
    model: str = "local-model"
    usage: Dict[str, int] = None


class LocalLLM:
    """
    Local LLM wrapper for offline operation.
    Provides API compatible with OpenAI client for easy swapping.
    """
    
    def __init__(self):
        """Initialize the local LLM with config from settings"""
        self.config = getattr(settings, 'LOCAL_LLM_CONFIG', {})
        self.model_path = self.config.get('model_path', '')
        self.model_name = self.config.get('model_name', '')
        self.ctx_size = self.config.get('ctx_size', 4096)
        self.n_gpu_layers = self.config.get('n_gpu_layers', -1)
        self.model = None
        self.embedding_model = None
        
        # Load embedding model
        self._load_embedding_model()
        
    def _load_embedding_model(self):
        """Load the local embedding model"""
        embedding_path = self.config.get('embedding_model_path', '')
        if not embedding_path or not os.path.exists(embedding_path):
            logger.error(f"Embedding model path not found: {embedding_path}")
            return
        
        try:
            self.embedding_model = SentenceTransformer(embedding_path)
            logger.info(f"Loaded embedding model from {embedding_path}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            
    def _load_llm(self):
        """Load the LLM on first use to save memory"""
        if self.model is not None:
            return
            
        if not LLAMA_CPP_AVAILABLE:
            logger.error("Cannot load LLM: llama_cpp not available")
            return
            
        full_path = os.path.join(self.model_path, self.model_name)
        if not os.path.exists(full_path):
            logger.error(f"LLM model path not found: {full_path}")
            return
            
        try:
            self.model = Llama(
                model_path=full_path,
                n_ctx=self.ctx_size,
                n_gpu_layers=self.n_gpu_layers
            )
            logger.info(f"Loaded LLM model from {full_path}")
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            
    def _format_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format messages into a prompt the local model can understand"""
        prompt = ""
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt += f"<|system|>\n{content}\n"
            elif role == "user":
                prompt += f"<|user|>\n{content}\n"
            elif role == "assistant":
                prompt += f"<|assistant|>\n{content}\n"
                
        # Add final assistant prompt to indicate where to generate
        prompt += "<|assistant|>\n"
        return prompt
    
    def embeddings(self):
        """Return an embeddings interface compatible with OpenAI embeddings API"""
        return LocalEmbeddingEngine(self.embedding_model)

    def chat(self):
        """Return a chat interface compatible with OpenAI chat completions API"""
        return LocalChatEngine(self)
        
    
class LocalChatEngine:
    """Provides a compatible interface with OpenAI chat completions API"""
    
    def __init__(self, llm: LocalLLM):
        self.llm = llm
            
    def completions(self):
        """Return a completions interface"""
        return self
        
    def create(self, model: str = None, messages: List[Dict[str, str]] = None, 
               temperature: float = 0.7, max_tokens: int = 512, stream: bool = False,
               **kwargs) -> Union[LLMResponse, Any]:
        """Generate a completion from the local model"""
        # Ensure the model is loaded
        if self.llm.model is None:
            self.llm._load_llm()
            if self.llm.model is None:
                logger.error("Failed to load LLM model")
                return self._create_error_response()
        
        # Format the prompt
        prompt = self.llm._format_prompt(messages)
        
        # Generate from the model
        try:
            if stream:
                return self._generate_stream(prompt, temperature, max_tokens)
            else:
                return self._generate(prompt, temperature, max_tokens)
        except Exception as e:
            logger.error(f"Error generating from local model: {e}")
            return self._create_error_response()
    
    def _generate(self, prompt: str, temperature: float, max_tokens: int) -> LLMResponse:
        """Generate a response from the model"""
        result = self.llm.model(
            prompt, 
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["<|user|>", "<|system|>"],
            echo=False
        )
        
        # Format response to match OpenAI
        text = result.get("choices", [{}])[0].get("text", "").strip()
        response = LLMResponse(
            choices=[Choice(message=Message(role="assistant", content=text))],
            usage={
                "prompt_tokens": len(prompt) // 4,  # Rough estimate
                "completion_tokens": len(text) // 4,  # Rough estimate
                "total_tokens": (len(prompt) + len(text)) // 4  # Rough estimate
            }
        )
        return response
    
    def _generate_stream(self, prompt: str, temperature: float, max_tokens: int) -> Any:
        """Generate a streaming response"""
        # This simulates the OpenAI streaming interface
        class StreamWrapper:
            def __init__(self, llm_model, prompt, temp, max_t):
                self.model = llm_model
                self.prompt = prompt
                self.temp = temp
                self.max_tokens = max_t
                self.finished = False
                
            def __iter__(self):
                return self
                
            def __next__(self):
                if self.finished:
                    raise StopIteration
                
                # Generate the full response first (not truly streaming, but simulates it)
                result = self.model(
                    self.prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temp,
                    stop=["<|user|>", "<|system|>"],
                    echo=False
                )
                
                text = result.get("choices", [{}])[0].get("text", "").strip()
                self.finished = True
                
                # Return a dictionary similar to what OpenAI streaming returns
                return type('obj', (object,), {
                    'choices': [
                        type('obj', (object,), {
                            'delta': type('obj', (object,), {
                                'content': text
                            }),
                            'finish_reason': 'stop',
                            'index': 0
                        })
                    ]
                })
        
        return StreamWrapper(self.llm.model, prompt, temperature, max_tokens)
    
    def _create_error_response(self) -> LLMResponse:
        """Create an error response when model generation fails"""
        return LLMResponse(
            choices=[Choice(message=Message(
                role="assistant", 
                content="I'm sorry, I encountered an error processing your request in offline mode."
            ))],
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        )


class LocalEmbeddingEngine:
    """Provides a compatible interface with OpenAI embeddings API"""
    
    def __init__(self, model: SentenceTransformer):
        self.model = model
        
    def create(self, model: str = None, input: Union[str, List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Generate embeddings from the local model"""
        if self.model is None:
            logger.error("Embedding model not available")
            return self._create_error_response()
            
        try:
            # Handle single string or list of strings
            inputs = [input] if isinstance(input, str) else input
            
            # Generate embeddings
            embeddings = self.model.encode(inputs, convert_to_numpy=True).tolist()
            
            # Format response to match OpenAI
            return {
                "data": [
                    {"embedding": emb, "index": i, "object": "embedding"} 
                    for i, emb in enumerate(embeddings)
                ],
                "model": "local-embedding-model",
                "usage": {
                    "prompt_tokens": sum(len(text.split()) for text in inputs),
                    "total_tokens": sum(len(text.split()) for text in inputs)
                }
            }
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return self._create_error_response()
            
    def _create_error_response(self) -> Dict[str, Any]:
        """Create an error response when embedding generation fails"""
        return {
            "data": [],
            "model": "local-embedding-model",
            "usage": {"prompt_tokens": 0, "total_tokens": 0}
        }


def get_local_llm() -> LocalLLM:
    """Factory function to get a local LLM instance"""
    return LocalLLM()