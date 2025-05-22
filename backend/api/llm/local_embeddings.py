"""
Local embeddings model for network-isolated environments.
Provides vector embeddings using on-prem models through ONNX Runtime.
"""

import os
import numpy as np
import logging
from django.conf import settings

# Set up logging
logger = logging.getLogger(__name__)

class LocalEmbeddingModel:
    """
    Local embedding model using ONNX Runtime.
    Provides an interface compatible with OpenAI's embedding API.
    """
    
    def __init__(self):
        """Initialize local embedding model."""
        self.model_path = getattr(settings, 'LOCAL_EMBEDDING_MODEL_PATH', None)
        self.tokenizer_path = getattr(settings, 'LOCAL_EMBEDDING_TOKENIZER_PATH', None)
        self.embedding_dim = getattr(settings, 'LOCAL_EMBEDDING_DIMENSION', 768)
        self.model = None
        self.tokenizer = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Load the embedding model and tokenizer."""
        try:
            if not self.model_path or not self.tokenizer_path:
                raise ValueError("Missing required paths for local embedding model or tokenizer")
            
            # Check if paths exist
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Embedding model not found at {self.model_path}")
            
            if not os.path.exists(self.tokenizer_path):
                raise FileNotFoundError(f"Tokenizer not found at {self.tokenizer_path}")
            
            # Import here to avoid loading these libraries unless needed
            import onnxruntime as ort
            from transformers import AutoTokenizer
            
            # Load tokenizer
            logger.info(f"Loading tokenizer from {self.tokenizer_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_path)
            
            # Create ONNX Runtime session
            logger.info(f"Loading embedding model from {self.model_path}")
            self.model = ort.InferenceSession(self.model_path)
            
            logger.info("Local embedding model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing local embedding model: {str(e)}")
            raise
    
    def create(self, input=None, model=None, encoding_format=None):
        """
        Create embeddings for the given input.
        
        Args:
            input (str or list): Text to embed
            model (str, optional): Model name (ignored, uses local model)
            encoding_format (str, optional): Output format (ignored)
        
        Returns:
            dict: Embeddings response with OpenAI-compatible structure
        """
        if self.model is None or self.tokenizer is None:
            logger.error("Embedding model not initialized")
            raise RuntimeError("Embedding model not initialized")
        
        # Handle both string and list inputs
        if isinstance(input, str):
            inputs = [input]
        else:
            inputs = input
        
        embeddings = []
        total_tokens = 0
        
        try:
            for text in inputs:
                # Tokenize the input
                encoded_input = self.tokenizer(
                    text,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="np"
                )
                
                # Count tokens
                token_count = len(encoded_input['input_ids'][0])
                total_tokens += token_count
                
                # Get model inputs
                model_inputs = {
                    'input_ids': encoded_input['input_ids'].astype(np.int64),
                    'attention_mask': encoded_input['attention_mask'].astype(np.int64),
                    'token_type_ids': encoded_input.get('token_type_ids', np.zeros_like(encoded_input['input_ids'])).astype(np.int64)
                }
                
                # Run inference
                outputs = self.model.run(None, model_inputs)
                
                # Get embeddings (using mean pooling)
                attention_mask = encoded_input['attention_mask']
                mask = attention_mask.astype(np.float32)
                mask_expanded = np.expand_dims(mask, axis=-1)
                
                # Get the hidden states from the model output
                hidden_states = outputs[0]
                
                # Apply mask and calculate mean
                masked_embeddings = hidden_states * mask_expanded
                sum_embeddings = np.sum(masked_embeddings, axis=1)
                sum_mask = np.sum(mask, axis=1, keepdims=True)
                sum_mask = np.clip(sum_mask, a_min=1e-9, a_max=None)  # Avoid division by zero
                
                # Calculate mean embeddings
                mean_embeddings = sum_embeddings / sum_mask
                
                # Normalize the embeddings
                norm = np.linalg.norm(mean_embeddings, axis=1, keepdims=True)
                normalized_embeddings = mean_embeddings / norm
                
                embeddings.append(normalized_embeddings[0].tolist())
            
            # Format response to match OpenAI's structure
            response = {
                'object': 'list',
                'data': [
                    {
                        'object': 'embedding',
                        'embedding': embedding,
                        'index': i
                    } for i, embedding in enumerate(embeddings)
                ],
                'model': os.path.basename(self.model_path),
                'usage': {
                    'prompt_tokens': total_tokens,
                    'total_tokens': total_tokens
                }
            }
            
            return EmbeddingResponse(response)
        
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            raise


class EmbeddingResponse:
    """
    Response object for local embeddings, mimicking OpenAI's response structure.
    """
    
    def __init__(self, data):
        """
        Initialize with embedding data.
        
        Args:
            data (dict): Embedding response data
        """
        self.data = data.get('data', [])
        self.model = data.get('model', 'local-embeddings')
        self.usage = data.get('usage', {})
        self.object = data.get('object', 'list')
    
    def __getitem__(self, key):
        """Allow dictionary-like access."""
        if key == 'data':
            return self.data
        elif key == 'model':
            return self.model
        elif key == 'usage':
            return self.usage
        elif key == 'object':
            return self.object
        raise KeyError(key)
    
    def __contains__(self, key):
        """Check if key exists."""
        return key in ['data', 'model', 'usage', 'object']