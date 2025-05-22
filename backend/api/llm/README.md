# LLM Network Isolation for RNA Lab Navigator

This module provides network isolation capabilities for Language Models (LLMs) in RNA Lab Navigator, enhancing security by keeping language model operations contained within your private network.

## Overview

The LLM network isolation system enables:

1. **Local LLM Inference** - Using Ollama for text generation
2. **Local Embeddings** - Using ONNX Runtime for vector embeddings
3. **Network Isolation** - Preventing external API calls for sensitive data
4. **Transparent Switching** - Compatible API with OpenAI for seamless integration

## Features

- **Fallback Capability**: Gracefully falls back to OpenAI if local models are unavailable
- **Compatibility Layer**: Uses the same interface as OpenAI's client for easy integration
- **Admin Interface**: Django admin panel for monitoring and managing isolation
- **Audit Logging**: Comprehensive logging of all LLM operations

## Configuration

Network isolation is configured via environment variables:

```
# LLM network isolation settings
LLM_NETWORK_ISOLATION=True            # Enable network isolation
LLM_FORCE_ISOLATION=True              # Force isolation (error if local LLM unavailable)
OLLAMA_API_URL=http://localhost:11434  # Ollama API URL
OLLAMA_DEFAULT_MODEL=llama3:8b         # Default Ollama model
OLLAMA_TIMEOUT=60                      # Request timeout in seconds

# Local embedding model settings
LOCAL_EMBEDDING_MODEL_PATH=/path/to/embedding_model.onnx
LOCAL_EMBEDDING_TOKENIZER_PATH=/path/to/tokenizer
LOCAL_EMBEDDING_DIMENSION=768
```

## Installation

### 1. Ollama Setup

Install and start Ollama:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server
ollama serve &

# Pull required models
ollama pull llama3:8b     # For text generation
```

### 2. Local Embedding Model

Set up a local embedding model:

```bash
# Install dependencies
pip install onnxruntime transformers sentencepiece torch

# Create model directory
mkdir -p models/all-MiniLM-L6-v2
cd models/all-MiniLM-L6-v2

# Download and save the model and tokenizer
python -c "from transformers import AutoTokenizer, AutoModel; tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2'); model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2'); tokenizer.save_pretrained('.'); model.save_pretrained('.');"

# Convert to ONNX format
python -c "from transformers import AutoModel; from transformers.onnx import export; model = AutoModel.from_pretrained('.'); export(tokenizer_or_preprocessor=None, model=model, opset=12, output='model.onnx');"
```

### 3. Network Configuration

For complete isolation, configure your firewall to:

1. Block outbound connections to `api.openai.com` and `openai.com`
2. Allow localhost connections to Ollama API (default port: 11434)

## Usage

### Basic Usage

```python
from api.llm import get_llm_client

# Get appropriate client (local or OpenAI based on settings)
client = get_llm_client()

# Use like OpenAI's client
response = client.chat.create(
    model="llama3:8b",  # Will be mapped to appropriate model
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is RNA?"}
    ]
)

print(response.choices[0].message.content)
```

### Embedding Creation

```python
from api.llm import get_embedding_model

# Get appropriate embedding model
embedding_model = get_embedding_model()

# Create embeddings
response = embedding_model.create(
    input="What is RNA?",
    model="all-MiniLM-L6-v2"  # Will be mapped to appropriate model
)

embeddings = response.data[0].embedding
```

### Checking Isolation Status

```python
from api.llm.isolation import check_isolation_status

# Check if LLM operations are properly isolated
status = check_isolation_status()

if status['isolated']:
    print("Network isolation is active")
else:
    print("Network isolation is not active")
    for error in status['errors']:
        print(f"- {error}")
```

## Admin Interface

The Django admin interface (`/admin/api/llmisolation/`) provides:

1. Current isolation status
2. Toggle for enabling/disabling isolation
3. Configuration recommendations
4. Troubleshooting information

## Implementation Details

- `local_llm.py` - Ollama integration for text generation
- `local_embeddings.py` - ONNX Runtime for embeddings
- `isolation.py` - Utilities for checking and enforcing isolation
- `admin.py` - Django admin interface

## Troubleshooting

If you encounter issues:

1. Check Ollama is running: `curl http://localhost:11434/api/version`
2. Verify model availability: `ollama list`
3. Test embedding model access
4. Check network connectivity rules
5. Review Django logs for detailed error messages

## Security Considerations

- **Data Privacy**: Local inference prevents sensitive data from leaving your network
- **Air-gapped Operation**: Can operate in environments without internet access
- **Defense-in-depth**: Part of a comprehensive security strategy
- **Audit Trail**: All operations are logged for security compliance