#!/usr/bin/env python
"""
Fix Weaviate schema to ensure all required fields are present.
This will update the existing schema or create a new one.
"""

import weaviate
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings')
import django
django.setup()

from api.ingestion.embeddings_utils import get_weaviate_client


def fix_weaviate_schema():
    """Fix or recreate Weaviate schema with all required fields."""
    print("Connecting to Weaviate...")
    client = get_weaviate_client()
    
    try:
        # First, check current schema
        schema = client.schema.get()
        existing_classes = {c['class']: c for c in schema.get('classes', [])}
        
        print(f"Found {len(existing_classes)} existing classes: {list(existing_classes.keys())}")
        
        # Check if Document class exists and has all fields
        if 'Document' in existing_classes:
            doc_class = existing_classes['Document']
            existing_props = {p['name'] for p in doc_class.get('properties', [])}
            print(f"Document class has properties: {existing_props}")
            
            # Check if chapter field is missing
            if 'chapter' not in existing_props:
                print("WARNING: 'chapter' field is missing from Document schema!")
                print("Deleting and recreating Document class...")
                
                # Delete the existing Document class
                client.schema.delete_class('Document')
                print("Deleted existing Document class")
            else:
                print("Document schema looks correct. All fields present.")
                return
        
        # Create or recreate the Document class with correct schema
        document_schema = {
            "class": "Document",
            "description": "A chunk of text from a document with metadata",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "text-embedding-3-small",
                    "type": "text"
                }
            },
            "properties": [
                {
                    "name": "content",
                    "description": "The text content of the chunk",
                    "dataType": ["text"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": False,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "doc_type",
                    "description": "Type of document (thesis, protocol, paper, etc.)",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "title",
                    "description": "Title of the source document",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "author",
                    "description": "Author of the document",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "year",
                    "description": "Year of publication",
                    "dataType": ["int"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "chapter",
                    "description": "Chapter number or name (for theses)",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "source",
                    "description": "Source file path",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                }
            ]
        }
        
        print("Creating Document class with correct schema...")
        client.schema.create_class(document_schema)
        print("✅ Document class created successfully!")
        
        # Verify the schema
        new_schema = client.schema.get()
        for c in new_schema.get('classes', []):
            if c['class'] == 'Document':
                props = {p['name'] for p in c.get('properties', [])}
                print(f"Verified Document properties: {props}")
                if 'chapter' in props:
                    print("✅ Chapter field confirmed in schema!")
                break
                
    except Exception as e:
        print(f"Error fixing schema: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    fix_weaviate_schema()