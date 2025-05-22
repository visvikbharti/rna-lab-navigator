"""
Offline mode package initialization.
This module provides methods for detecting offline mode and 
dynamically switching between online and offline dependencies.
"""

import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def is_offline_mode() -> bool:
    """
    Check if the system is running in offline mode.
    Offline mode can be set via OFFLINE_MODE setting or RNA_OFFLINE environment variable.
    """
    if hasattr(settings, 'OFFLINE_MODE') and settings.OFFLINE_MODE:
        return True
    
    # Also check environment variable for command-line control
    if os.environ.get('RNA_OFFLINE', '').lower() in ('true', '1', 'yes'):
        return True
        
    return False

def get_llm_client():
    """
    Get the appropriate LLM client based on offline mode and network isolation settings.
    Returns appropriate client based on configuration.
    """
    if is_offline_mode():
        # In offline mode, always use local LLM
        from .local_llm import get_local_llm
        return get_local_llm()
    else:
        # Check network isolation settings
        if getattr(settings, 'LLM_NETWORK_ISOLATION', False):
            # Use isolated LLM client
            from api.llm import get_llm_client as get_isolated_client
            return get_isolated_client(isolation_level="isolated")
        else:
            # Use OpenAI client
            from openai import OpenAI
            return OpenAI(api_key=settings.OPENAI_API_KEY)

def get_vector_db_client():
    """
    Get the appropriate vector DB client based on offline mode.
    Returns Weaviate client in online mode or LocalVectorDB in offline mode.
    With mTLS support when WEAVIATE_TLS_ENABLED is True.
    """
    if is_offline_mode():
        from .local_vector_db import get_local_vector_db
        return get_local_vector_db()
    else:
        import weaviate
        from django.conf import settings
        import os
        
        auth_config = None
        if settings.WEAVIATE_API_KEY:
            auth_config = weaviate.auth.AuthApiKey(api_key=settings.WEAVIATE_API_KEY)
        
        # Use v4 client connection
        import weaviate.connect as weaviate_connect
        if settings.WEAVIATE_API_KEY:
            auth_config = weaviate.auth.ApiKey(settings.WEAVIATE_API_KEY)
            client = weaviate.connect_to_local(
                host="localhost",
                port=8080,
                auth_credentials=auth_config
            )
        else:
            client = weaviate.connect_to_local(
                host="localhost", 
                port=8080
            )
        
        # Configure mTLS if enabled
        if settings.WEAVIATE_TLS_ENABLED:
            logger.info("mTLS is enabled for Weaviate connection")
            
            if not all([settings.WEAVIATE_CLIENT_CERT, settings.WEAVIATE_CLIENT_KEY]):
                logger.error("mTLS is enabled but client certificates are missing")
                raise ValueError("Client certificate and key are required for mTLS")
            
            # Ensure certificates exist
            if not os.path.exists(settings.WEAVIATE_CLIENT_CERT):
                logger.error(f"Client certificate not found: {settings.WEAVIATE_CLIENT_CERT}")
                raise FileNotFoundError(f"Client certificate not found: {settings.WEAVIATE_CLIENT_CERT}")
                
            if not os.path.exists(settings.WEAVIATE_CLIENT_KEY):
                logger.error(f"Client key not found: {settings.WEAVIATE_CLIENT_KEY}")
                raise FileNotFoundError(f"Client key not found: {settings.WEAVIATE_CLIENT_KEY}")
            
            # Optional CA certificate validation
            ca_path = None
            if settings.WEAVIATE_CA_CERT and os.path.exists(settings.WEAVIATE_CA_CERT):
                ca_path = settings.WEAVIATE_CA_CERT
                logger.info(f"Using CA certificate: {ca_path}")
            
            # Configure TLS with client certificates
            client_config = weaviate.Config(
                url=settings.WEAVIATE_URL,
                auth_client_secret=auth_config,
                trust_env=False,  # Don't use environment proxies
                additional_headers={},
                startup_period=5,  # Wait for Weaviate to be ready
                grpc_port_experimental=None,  # Default GRPC port
                # mTLS config
                client_cert_path=settings.WEAVIATE_CLIENT_CERT,
                client_key_path=settings.WEAVIATE_CLIENT_KEY,
                ca_cert_path=ca_path,
            )
            
        return weaviate.Client(client_config)

def get_cross_encoder():
    """
    Get the appropriate cross-encoder based on offline mode.
    Returns online cross-encoder in online mode or local cross-encoder in offline mode.
    """
    from sentence_transformers import CrossEncoder
    
    if is_offline_mode() and hasattr(settings, 'CROSS_ENCODER_CONFIG'):
        config = settings.CROSS_ENCODER_CONFIG
        model_path = config.get('model_path', '')
        if model_path and os.path.exists(model_path):
            return CrossEncoder(model_path)
    
    # Default to online model
    return CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')