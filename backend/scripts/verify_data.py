import os
import sys
import django

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rna_backend.settings")
django.setup()

from api.models import Document, QueryHistory

def verify_data():
    print(f"Documents: {Document.objects.count()}")
    print("Documents list:")
    for doc in Document.objects.all():
        print(f"- {doc.title} ({doc.doc_type}, {doc.author}, {doc.year})")
    
    print(f"\nQuery History: {QueryHistory.objects.count()}")
    print("Recent Queries:")
    for query in QueryHistory.objects.all()[:5]:  # Show only first 5
        print(f"- Query: {query.query_text}")
        print(f"  Answer: {query.answer[:50]}...")

if __name__ == "__main__":
    verify_data()