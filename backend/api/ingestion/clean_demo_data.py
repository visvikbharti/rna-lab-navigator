"""
Script to remove demo/fake data and ensure only real research documents are in the system
"""

import os
import sys
import django

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings')
django.setup()

from api.models import Document, QueryHistory
from django.db import transaction

def clean_demo_data():
    """Remove all demo/fake data from the system"""
    
    print("🧹 Cleaning demo data from the system...")
    
    # List of known demo/fake document patterns
    demo_patterns = [
        'dummy',
        'sample',
        'test',
        'fake',
        'demo'
    ]
    
    with transaction.atomic():
        # Find and remove demo documents
        removed_count = 0
        for doc in Document.objects.all():
            # Check if document title or content contains demo patterns
            is_demo = False
            
            for pattern in demo_patterns:
                if pattern.lower() in doc.title.lower():
                    is_demo = True
                    break
                    
            # Keep real thesis and papers
            if doc.doc_type == 'thesis' and 'phutela' in doc.author.lower():
                is_demo = False  # This is the real thesis
                
            if is_demo:
                print(f"  ❌ Removing demo document: {doc.title}")
                doc.delete()
                removed_count += 1
            else:
                print(f"  ✅ Keeping real document: {doc.title} by {doc.author}")
        
        print(f"\n📊 Summary:")
        print(f"  - Removed {removed_count} demo documents")
        print(f"  - Kept {Document.objects.count()} real documents")
        
        # Clean up test queries
        test_queries = QueryHistory.objects.filter(
            query_text__icontains='test'
        ) | QueryHistory.objects.filter(
            query_text__icontains='example'
        )
        
        test_query_count = test_queries.count()
        test_queries.delete()
        print(f"  - Removed {test_query_count} test queries")
        
    print("\n✨ Demo data cleanup complete!")
    
    # List remaining documents
    print("\n📚 Current documents in the system:")
    for doc in Document.objects.all().order_by('doc_type', 'year'):
        print(f"  - [{doc.doc_type.upper()}] {doc.title} by {doc.author} ({doc.year})")

if __name__ == "__main__":
    clean_demo_data()