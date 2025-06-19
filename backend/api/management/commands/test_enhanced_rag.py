"""
Management command to test the enhanced RAG system.
"""

from django.core.management.base import BaseCommand
from api.models import Document
from api.search.enhanced_real_rag import get_enhanced_rag_system
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
import time


class Command(BaseCommand):
    help = 'Test the enhanced RAG system with advanced features'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reingest',
            action='store_true',
            help='Re-ingest all documents with enhanced processing'
        )
        parser.add_argument(
            '--local-embeddings',
            action='store_true',
            help='Use local embedding model instead of OpenAI'
        )
        parser.add_argument(
            '--query',
            type=str,
            help='Test query to run'
        )

    def handle(self, *args, **options):
        console = Console()
        
        # Initialize enhanced RAG system
        console.print("[bold blue]Initializing Enhanced RAG System...[/bold blue]")
        rag_system = get_enhanced_rag_system(use_local_embeddings=options['local_embeddings'])
        
        if options['reingest']:
            self.reingest_documents(console, rag_system)
        
        if options['query']:
            self.test_query(console, rag_system, options['query'])
        else:
            self.run_test_suite(console, rag_system)
    
    def reingest_documents(self, console, rag_system):
        """Re-ingest all documents with enhanced processing."""
        console.print("\n[bold yellow]Re-ingesting all documents...[/bold yellow]")
        
        documents = Document.objects.all()
        
        for doc in track(documents, description="Processing documents..."):
            success = rag_system.ingest_document(doc)
            if success:
                console.print(f"✓ {doc.title}", style="green")
            else:
                console.print(f"✗ {doc.title}", style="red")
    
    def test_query(self, console, rag_system, query):
        """Test a single query."""
        console.print(f"\n[bold]Testing query:[/bold] {query}")
        
        start_time = time.time()
        
        # Search
        search_results = rag_system.search(query, top_k=5)
        search_time = time.time() - start_time
        
        # Display search results
        if search_results:
            table = Table(title="Search Results")
            table.add_column("Score", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Type", style="yellow")
            table.add_column("Chunk Type", style="blue")
            
            for result in search_results:
                table.add_row(
                    f"{result['score']:.3f}",
                    result['title'][:50] + "..." if len(result['title']) > 50 else result['title'],
                    result['type'],
                    result['chunk_type']
                )
            
            console.print(table)
        
        # Generate answer
        answer_data = rag_system.generate_answer(query, search_results)
        total_time = time.time() - start_time
        
        # Display answer
        console.print(Panel(
            answer_data['answer'],
            title=f"Answer (Confidence: {answer_data['confidence_score']:.1%})",
            border_style="green"
        ))
        
        # Display sources
        if answer_data['sources']:
            console.print("\n[bold]Sources:[/bold]")
            for source in answer_data['sources']:
                console.print(f"  • {source['title']} by {source['author']} ({source['year']})")
        
        # Display timing
        console.print(f"\n[dim]Search time: {search_time:.2f}s | Total time: {total_time:.2f}s[/dim]")
    
    def run_test_suite(self, console, rag_system):
        """Run a comprehensive test suite."""
        test_queries = [
            # Thesis queries
            "What DNA repair mechanisms are studied in Rhythm Phutela thesis regarding Cas9 cleavage?",
            "Extract the key findings from tables in Rhythm's thesis about NHEJ efficiency",
            
            # Paper queries
            "What is the RAPID FnCas9 system developed by Kumar for COVID detection?",
            "Show me the experimental results from Kumar's 2022 paper tables",
            
            # Protocol queries
            "What is the detailed protocol for RNA extraction using Trizol?",
            "Find the PCR cycling conditions from the lab protocols",
            
            # Complex queries
            "Compare NHEJ and HDR repair mechanisms across all documents",
            "What equations describe CRISPR targeting efficiency?"
        ]
        
        console.print("\n[bold cyan]Running Enhanced RAG Test Suite[/bold cyan]\n")
        
        for i, query in enumerate(test_queries, 1):
            console.print(f"\n[bold]Test {i}/{len(test_queries)}[/bold]")
            self.test_query(console, rag_system, query)
            console.print("\n" + "="*80 + "\n")