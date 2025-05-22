#!/usr/bin/env python
"""
Script to generate secure values for environment configuration.
This generates random values for secrets in the .env.production file.
"""

import secrets
import string
import sys
import os
from datetime import datetime

# Define character sets for different types of secrets
ALPHANUM = string.ascii_letters + string.digits
SPECIAL_CHARS = "!@#$%^&*()-_=+[]{}|;:,.<>?"
ALL_CHARS = ALPHANUM + SPECIAL_CHARS

def generate_password(length=32, use_special=True):
    """Generate a secure random password."""
    if use_special:
        charset = ALL_CHARS
    else:
        charset = ALPHANUM
    
    return ''.join(secrets.choice(charset) for _ in range(length))

def generate_secret_key(length=64):
    """Generate a Django secret key."""
    return generate_password(length, use_special=True)

def generate_api_key(length=48):
    """Generate an API key (alphanumeric only)."""
    return ''.join(secrets.choice(ALPHANUM) for _ in range(length))

def main():
    """Generate and print secure values for environment variables."""
    print("\nRNA Lab Navigator - Secure Environment Value Generator")
    print("=" * 60)
    print("Copy these values to your .env.production file")
    print("=" * 60)
    
    print(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n# Security Keys")
    print(f"SECRET_KEY={generate_secret_key()}")
    
    print("\n# Database Credentials")
    print(f"POSTGRES_PASSWORD={generate_password(20)}")
    
    print("\n# Redis Credentials")
    print(f"REDIS_PASSWORD={generate_password(16)}")
    
    print("\n# API Keys")
    print(f"WEAVIATE_API_KEY={generate_api_key()}")
    print(f"# OPENAI_API_KEY=sk-...  # Get this from your OpenAI account")
    
    print("\n# AWS Credentials (if used)")
    print(f"# AWS_ACCESS_KEY_ID=  # Get this from your AWS account")
    print(f"# AWS_SECRET_ACCESS_KEY=  # Get this from your AWS account")
    
    print("\n# Other Credentials")
    print(f"GRAFANA_PASSWORD={generate_password(12, use_special=False)}")
    print("\nIMPORTANT: Keep these values secure and never commit them to version control!")

if __name__ == "__main__":
    main()