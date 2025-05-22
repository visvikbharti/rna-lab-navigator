#!/usr/bin/env python
"""
Script to download and prepare models for offline mode.
This downloads embedding models, cross-encoder models, and
optionally LLM models for completely offline operation.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import shutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add path to Django project
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
sys.path.append(backend_dir)

# Import after setting up path
from django.conf import settings

def download_sentence_transformers(model_name, output_dir):
    """Download a sentence transformers model for offline use"""
    try:
        from sentence_transformers import SentenceTransformer
        
        logger.info(f"Downloading {model_name}...")
        model = SentenceTransformer(model_name)
        
        # Save the model
        output_path = os.path.join(output_dir, model_name)
        os.makedirs(output_path, exist_ok=True)
        model.save(output_path)
        
        logger.info(f"Model saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error downloading model {model_name}: {e}")
        return False

def download_cross_encoder(model_name, output_dir):
    """Download a cross-encoder model for offline use"""
    try:
        from sentence_transformers import CrossEncoder
        
        logger.info(f"Downloading cross-encoder {model_name}...")
        model = CrossEncoder(model_name)
        
        # Save the model
        output_path = os.path.join(output_dir, model_name)
        os.makedirs(output_path, exist_ok=True)
        model.save(output_path)
        
        logger.info(f"Cross-encoder saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error downloading cross-encoder {model_name}: {e}")
        return False

def download_llm(model_name, output_dir, use_hf=True):
    """Download an LLM for offline use"""
    try:
        if use_hf:
            # Use Hugging Face to download model
            from huggingface_hub import snapshot_download
            
            logger.info(f"Downloading LLM {model_name} from Hugging Face...")
            output_path = os.path.join(output_dir, model_name)
            os.makedirs(output_path, exist_ok=True)
            
            snapshot_download(
                repo_id=model_name,
                local_dir=output_path,
                local_dir_use_symlinks=False
            )
            
            logger.info(f"LLM saved to {output_path}")
            return True
        else:
            # Download GGUF file from direct URL
            import requests
            from tqdm import tqdm
            
            models_map = {
                "llama2-7b": "https://huggingface.co/TheBloke/Llama-2-7B-GGUF/resolve/main/llama-2-7b.Q4_K_M.gguf",
                "llama2-7b-chat": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"
            }
            
            if model_name not in models_map:
                logger.error(f"Model {model_name} not found in models map")
                return False
            
            url = models_map[model_name]
            filename = url.split("/")[-1]
            output_path = os.path.join(output_dir, filename)
            
            logger.info(f"Downloading {model_name} from {url}...")
            
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f, tqdm(
                desc=filename,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    size = f.write(data)
                    bar.update(size)
            
            logger.info(f"Model saved to {output_path}")
            return True
            
    except Exception as e:
        logger.error(f"Error downloading LLM {model_name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Download models for offline mode")
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.path.join(backend_dir, "models"),
        help="Output directory for downloaded models"
    )
    
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Embedding model to download"
    )
    
    parser.add_argument(
        "--cross-encoder",
        type=str,
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        help="Cross-encoder model to download"
    )
    
    parser.add_argument(
        "--download-llm",
        action="store_true",
        help="Download LLM model (may be large)"
    )
    
    parser.add_argument(
        "--llm-model",
        type=str,
        default="llama2-7b-chat",
        help="LLM model to download (llama2-7b or llama2-7b-chat)"
    )
    
    args = parser.parse_args()
    
    # Create output directories
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "embeddings"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "cross-encoder"), exist_ok=True)
    
    # Download embedding model
    embedding_success = download_sentence_transformers(
        args.embedding_model,
        os.path.join(output_dir, "embeddings")
    )
    
    # Download cross-encoder model
    cross_encoder_success = download_cross_encoder(
        args.cross_encoder,
        os.path.join(output_dir, "cross-encoder")
    )
    
    # Download LLM if requested
    llm_success = True
    if args.download_llm:
        os.makedirs(os.path.join(output_dir, "llm"), exist_ok=True)
        llm_success = download_llm(
            args.llm_model,
            os.path.join(output_dir, "llm"),
            use_hf=False  # Use direct GGUF download
        )
    
    # Report success
    if embedding_success and cross_encoder_success and llm_success:
        logger.info("All models downloaded successfully!")
        
        # Create .env.offline with offline settings
        env_path = os.path.join(backend_dir, ".env.offline")
        with open(env_path, 'w') as f:
            f.write("# Offline mode environment variables\n")
            f.write("RNA_OFFLINE=true\n")
            f.write(f"LOCAL_EMBEDDING_MODEL={args.embedding_model}\n")
            f.write(f"LOCAL_CROSS_ENCODER={args.cross_encoder.split('/')[-1]}\n")
            if args.download_llm:
                f.write(f"LOCAL_LLM={args.llm_model}\n")
            
        logger.info(f"Created offline environment file at {env_path}")
        logger.info("To run in offline mode, use: export RNA_OFFLINE=true")
    else:
        logger.error("Some models failed to download. Check the logs.")

if __name__ == "__main__":
    main()