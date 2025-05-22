#!/usr/bin/env python
"""
Script to initialize the vector store with sample documents.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings')
django.setup()

# Now import and run the initialization
from api.search.real_rag import initialize_vectorstore_with_sample_data

def main():
    print("Initializing vector store with sample documents...")
    initialize_vectorstore_with_sample_data()
    print("Vector store initialization complete!")

if __name__ == "__main__":
    main()