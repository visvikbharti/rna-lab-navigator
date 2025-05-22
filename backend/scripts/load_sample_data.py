import os
import sys
import django
import json
from django.db import models

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rna_backend.settings")
django.setup()

from api.models import Document, QueryHistory
from django.utils import timezone

def load_sample_data():
    # Clear existing data
    Document.objects.all().delete()
    
    # Sample content for our documents
    documents = [
        {
            'title': 'RNA Extraction Protocol',
            'doc_type': 'protocol',
            'author': 'Lab Protocol',
            'year': 2023,
            'content': 'RNA extraction protocols typically involve cell lysis, RNA isolation using reagents like TRIzol, and purification steps to remove contaminants.'
        },
        {
            'title': 'TRIzol RNA Isolation Method',
            'doc_type': 'protocol',
            'author': 'Research Lab',
            'year': 2022,
            'content': 'The TRIzol method is a commonly used technique for RNA isolation that involves phase separation with chloroform, precipitation with isopropanol, and washing with ethanol.'
        },
        {
            'title': 'RNA Dynamics and Processing',
            'doc_type': 'thesis',
            'author': 'Phutela',
            'year': 2025,
            'content': 'Chapter 3 covers in depth analysis of in vitro cleavage assays and their applications in studying RNA processing mechanisms.'
        },
        {
            'title': 'CRISPR Ribonuclease Activity in RNA Processing',
            'doc_type': 'paper',
            'author': 'Chakraborty et al.',
            'year': 2024,
            'content': 'This paper describes applications of CRISPR systems in RNA cleavage assays and their implications for RNA biology research.'
        },
        {
            'title': 'In Vitro RNA Cleavage Protocol',
            'doc_type': 'protocol',
            'author': 'Kumar et al.',
            'year': 2023,
            'content': 'This protocol describes specific methods for in vitro RNA cleavage assays using purified enzymes. The assay is routinely used to evaluate ribozyme activity and RNA processing.'
        }
    ]

    # Create sample documents
    for doc_data in documents:
        doc = Document.objects.create(
            title=doc_data['title'],
            doc_type=doc_data['doc_type'],
            author=doc_data['author'],
            year=doc_data['year']
        )
        
        # Create sample query history referencing each document
        QueryHistory.objects.create(
            query_text=f"Tell me about {doc_data['title']}",
            answer=doc_data['content'],
            confidence_score=0.85,
            sources=json.dumps([{'title': doc_data['title'], 'id': doc.id}]),
            doc_type=doc_data['doc_type'],
            processing_time=0.5
        )

    print(f"Loaded {Document.objects.count()} sample documents with {QueryHistory.objects.count()} sample queries")

if __name__ == "__main__":
    load_sample_data()
