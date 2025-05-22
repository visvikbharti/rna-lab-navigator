#!/usr/bin/env python
"""
Test script for mTLS connection to Weaviate.
This script will attempt to connect to Weaviate using mTLS certificates.

Usage:
    python test_mtls_connection.py [--url https://localhost:8080]

Requirements:
    pip install weaviate-client
"""

import argparse
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def test_weaviate_mtls_connection(url):
    """Test the mTLS connection to Weaviate."""
    try:
        import weaviate
    except ImportError:
        logger.error("Error: This script requires the 'weaviate-client' package.")
        logger.error("Install it with: pip install weaviate-client")
        sys.exit(1)
    
    # Check for certificate files
    client_cert = os.environ.get("WEAVIATE_CLIENT_CERT")
    client_key = os.environ.get("WEAVIATE_CLIENT_KEY")
    ca_cert = os.environ.get("WEAVIATE_CA_CERT")
    
    if not client_cert or not client_key:
        logger.error("Error: WEAVIATE_CLIENT_CERT and WEAVIATE_CLIENT_KEY environment variables must be set.")
        logger.error("Run the generate_mtls_certs.py script first and source the mtls.env file.")
        sys.exit(1)
    
    logger.info(f"Testing mTLS connection to Weaviate at {url}")
    logger.info(f"Using client certificate: {client_cert}")
    logger.info(f"Using client key: {client_key}")
    if ca_cert:
        logger.info(f"Using CA certificate: {ca_cert}")
    
    # Verify certificate files exist
    for cert_file in [client_cert, client_key]:
        if not os.path.exists(cert_file):
            logger.error(f"Error: Certificate file not found: {cert_file}")
            sys.exit(1)
    
    if ca_cert and not os.path.exists(ca_cert):
        logger.error(f"Error: CA certificate file not found: {ca_cert}")
        sys.exit(1)
    
    try:
        # Configure Weaviate client with mTLS
        client_config = weaviate.Config(
            url=url,
            trust_env=False,
            client_cert_path=client_cert,
            client_key_path=client_key,
            ca_cert_path=ca_cert if ca_cert else None,
        )
        
        client = weaviate.Client(client_config)
        
        # Test the connection
        meta = client.get_meta()
        version = meta.get("version", "unknown")
        
        logger.info(f"✅ Successfully connected to Weaviate version {version} using mTLS")
        
        # Check for existing schema
        schema = client.schema.get()
        classes = schema.get("classes", [])
        
        if classes:
            logger.info(f"Found {len(classes)} classes in schema:")
            for cls in classes:
                logger.info(f"  - {cls.get('class')}")
        else:
            logger.info("No classes found in schema")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Failed to connect to Weaviate: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test mTLS connection to Weaviate")
    parser.add_argument("--url", default="https://localhost:8080", help="Weaviate URL")
    args = parser.parse_args()
    
    success = test_weaviate_mtls_connection(args.url)
    sys.exit(0 if success else 1)