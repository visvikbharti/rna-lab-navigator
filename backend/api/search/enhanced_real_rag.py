"""
Enhanced RAG implementation using hybrid search and advanced PDF processing.
"""

import os
import json
from openai import OpenAI
import numpy as np
from django.conf import settings
from api.models import Document, QueryHistory
from api.ingestion.advanced_pdf_processor_simple import AdvancedPDFProcessor, EnhancedChunker
from api.search.hybrid_search_simple import SimpleHybridSearchEngine as HybridSearchEngine, LocalEmbeddingModel
from api.rag.enhanced_answer_validator import get_answer_validator, get_answer_enhancer
from pathlib import Path
from typing import List, Dict, Any


class EnhancedRAGSystem:
    """Enhanced RAG system with hybrid search and advanced document processing."""
    
    def __init__(self, use_local_embeddings: bool = False):
        # Initialize components
        self.pdf_processor = AdvancedPDFProcessor()
        self.chunker = EnhancedChunker(chunk_size=400, overlap=100)
        self.search_engine = HybridSearchEngine()
        
        # Embedding model
        if use_local_embeddings:
            self.embedding_model = LocalEmbeddingModel()
        else:
            self.embedding_model = None
        
        # Initialize if empty
        if len(self.search_engine.documents) == 0:
            self.initialize_with_documents()
    
    def ingest_document(self, document: Document) -> bool:
        """
        Ingest a document with advanced processing.
        
        Args:
            document: Document model instance
            
        Returns:
            bool: Success status
        """
        try:
            # Get PDF path
            pdf_path = self._get_pdf_path(document)
            if not pdf_path or not os.path.exists(pdf_path):
                print(f"PDF not found for {document.title}")
                return False
            
            # Process PDF with advanced extractor
            print(f"Processing {document.title} with advanced PDF processor...")
            doc_data = self.pdf_processor.process_pdf(str(pdf_path))
            
            # Add document metadata
            doc_data['metadata'].update({
                'doc_id': document.id,
                'doc_type': document.doc_type,
                'author': document.author,
                'year': document.year
            })
            
            # Chunk the document
            chunks = self.chunker.chunk_document(doc_data)
            
            # Process each chunk
            documents_to_add = []
            for i, chunk in enumerate(chunks):
                # Create chunk text with context
                chunk_text = self._create_chunk_text(chunk, doc_data['metadata'])
                
                # Get embedding
                if self.embedding_model:
                    embedding = self.embedding_model.get_embedding(chunk_text)
                else:
                    embedding = self._get_openai_embedding(chunk_text)
                
                # Prepare document for indexing
                doc_to_add = {
                    'text': chunk_text,
                    'embedding': embedding,
                    'metadata': {
                        'title': document.title,
                        'author': document.author,
                        'doc_type': document.doc_type,
                        'year': document.year,
                        'document_id': document.id,
                        'chunk_index': i,
                        'chunk_type': chunk['type'],
                        'section': chunk.get('metadata', {}).get('section', ''),
                        'page': chunk.get('metadata', {}).get('page', 0)
                    }
                }
                documents_to_add.append(doc_to_add)
            
            # Add to search engine
            self.search_engine.add_documents(documents_to_add)
            
            print(f"Successfully ingested {len(chunks)} chunks from {document.title}")
            print(f"  - Text chunks: {sum(1 for c in chunks if c['type'] == 'text')}")
            print(f"  - Tables: {sum(1 for c in chunks if c['type'] == 'table')}")
            print(f"  - Figures: {sum(1 for c in chunks if c['type'] == 'figure')}")
            print(f"  - Equations: {sum(1 for c in chunks if c['type'] == 'equation')}")
            
            return True
            
        except Exception as e:
            print(f"Error ingesting document {document.title}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def search(self, query: str, doc_type: str = "all", top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search with post-filtering.
        
        Args:
            query: Search query
            doc_type: Document type filter
            top_k: Number of results
            
        Returns:
            List of search results
        """
        # Search with more candidates for filtering
        search_k = top_k * 3 if doc_type != "all" else top_k
        
        # Perform hybrid search
        results = self.search_engine.search(
            query, 
            top_k=search_k,
            semantic_weight=0.7,
            keyword_weight=0.3
        )
        
        # Filter by document type if specified
        if doc_type != "all":
            results = [r for r in results if r['metadata']['doc_type'] == doc_type]
        
        # Format results
        formatted_results = []
        seen_docs = set()
        
        for result in results:
            doc_key = f"{result['metadata']['title']}_{result['metadata']['author']}"
            
            if doc_key not in seen_docs:
                seen_docs.add(doc_key)
                formatted_results.append({
                    'id': str(result['metadata']['document_id']),
                    'title': result['metadata']['title'],
                    'type': result['metadata']['doc_type'],
                    'author': result['metadata']['author'],
                    'year': result['metadata']['year'],
                    'snippet': result['text'][:800] + "..." if len(result['text']) > 800 else result['text'],
                    'score': round(result['score'], 3),
                    'semantic_score': round(result['semantic_score'], 3),
                    'keyword_score': round(result['keyword_score'], 3),
                    'boost': round(result.get('boost', 0), 3),
                    'chunk_type': result['metadata'].get('chunk_type', 'text'),
                    'section': result['metadata'].get('section', ''),
                    'page': result['metadata'].get('page', 0)
                })
        
        return formatted_results[:top_k]
    
    def generate_answer(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate answer with enhanced context."""
        validator = get_answer_validator()
        enhancer = get_answer_enhancer()
        
        if not search_results:
            return {
                'answer': "I don't have enough information to answer this question based on the available documents.",
                'confidence_score': 0.0,
                'sources': []
            }
        
        # Prepare enhanced context
        context_parts = []
        for i, result in enumerate(search_results[:3]):
            context_part = f"Source {i+1} ({result['title']} by {result['author']}, {result['year']}):\n"
            
            # Add section info if available
            if result.get('section'):
                context_part += f"Section: {result['section']}\n"
            
            # Add chunk type info
            if result['chunk_type'] == 'table':
                context_part += "[TABLE DATA]\n"
            elif result['chunk_type'] == 'figure':
                context_part += "[FIGURE CAPTION]\n"
            elif result['chunk_type'] == 'equation':
                context_part += "[EQUATION]\n"
            
            context_part += result['snippet']
            context_parts.append(context_part)
        
        context = "\n\n".join(context_parts)
        
        # Enhanced prompt
        prompt = self._create_enhanced_prompt(query, context, search_results)
        
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.1
            )
            
            answer = response.choices[0].message.content
            
            # Calculate confidence
            confidence_score = self._calculate_confidence(search_results)
            
            # Extract unique sources
            sources = self._extract_sources(search_results)
            
            # Validate and enhance answer
            validation_results = validator.validate_answer(
                query, answer, confidence_score, sources
            )
            
            if not validation_results['is_valid'] or validation_results['enhanced_answer'] != answer:
                answer = validation_results['enhanced_answer']
            
            # Apply answer formatting
            answer_type = enhancer.detect_answer_type(query)
            answer = enhancer.enhance_answer(query, answer, answer_type)
            
            # Update confidence based on validation
            if validation_results['quality_score'] > 0:
                confidence_score = (confidence_score + validation_results['quality_score']) / 2
            
            return {
                'answer': answer,
                'confidence_score': confidence_score,
                'sources': sources,
                'search_metadata': {
                    'top_score': search_results[0]['score'] if search_results else 0,
                    'result_types': list(set(r['chunk_type'] for r in search_results))
                }
            }
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return {
                'answer': "I apologize, but I encountered an error while processing your question.",
                'confidence_score': 0.0,
                'sources': []
            }
    
    def _get_pdf_path(self, document: Document) -> Path:
        """Get PDF path for a document."""
        base_path = Path(__file__).parent.parent.parent.parent
        
        # Map document type to directory
        dir_mapping = {
            'thesis': 'theses',
            'protocol': 'community_protocols',
            'paper': 'papers'
        }
        
        dir_name = dir_mapping.get(document.doc_type, f"{document.doc_type}s")
        doc_dir = base_path / 'data' / 'sample_docs' / dir_name
        
        if not doc_dir.exists():
            return None
        
        # Try to find PDF file
        pdf_files = list(doc_dir.glob("*.pdf"))
        
        # Clean title for matching
        clean_title = document.title.replace(' - Real Content', '').lower()
        clean_title = clean_title.replace(' ', '').replace('-', '').replace('_', '').replace('.', '')
        
        for pdf_file in pdf_files:
            pdf_name = pdf_file.stem.lower().replace(' ', '').replace('-', '').replace('_', '').replace('.', '')
            if clean_title in pdf_name or pdf_name in clean_title:
                return pdf_file
        
        return None
    
    def _create_chunk_text(self, chunk: Dict[str, Any], doc_metadata: Dict[str, Any]) -> str:
        """Create searchable text from chunk with metadata."""
        parts = []
        
        # Add document context
        parts.append(f"Document: {doc_metadata.get('title', '')}")
        parts.append(f"Author: {doc_metadata.get('author', '')}")
        parts.append(f"Year: {doc_metadata.get('year', '')}")
        
        # Add chunk-specific context
        if chunk['type'] == 'text' and chunk.get('metadata', {}).get('section'):
            parts.append(f"Section: {chunk['metadata']['section']}")
        elif chunk['type'] == 'table':
            parts.append("Content Type: Table")
        elif chunk['type'] == 'figure':
            parts.append("Content Type: Figure")
        elif chunk['type'] == 'equation':
            parts.append("Content Type: Equation")
        
        # Add main content
        parts.append("")  # Empty line
        parts.append(chunk['content'])
        
        return "\n".join(parts)
    
    def _get_openai_embedding(self, text: str) -> np.ndarray:
        """Get OpenAI embedding."""
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text[:8000]
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return np.random.rand(1536)
    
    def _create_enhanced_prompt(self, query: str, context: str, search_results: List[Dict[str, Any]]) -> str:
        """Create enhanced prompt with metadata."""
        # Check if we have tables or figures
        has_tables = any(r['chunk_type'] == 'table' for r in search_results)
        has_figures = any(r['chunk_type'] == 'figure' for r in search_results)
        has_equations = any(r['chunk_type'] == 'equation' for r in search_results)
        
        prompt = f"""You are an expert research assistant for Dr. Debojyoti Chakraborty's RNA biology lab at CSIR-IGIB.

Context from lab documents:
{context}

Additional Information:
- The search found {len(search_results)} relevant sections
- Document types include: {', '.join(set(r['type'] for r in search_results))}
"""
        
        if has_tables:
            prompt += "- The results include table data that may contain experimental results or protocols\n"
        if has_figures:
            prompt += "- The results include figure captions that describe experimental data or methods\n"
        if has_equations:
            prompt += "- The results include mathematical equations relevant to the research\n"
        
        prompt += f"""
Question: {query}

Instructions:
1. Provide a comprehensive answer based on the documents
2. Include specific details from tables, figures, or equations if relevant
3. Cite sources naturally in your response
4. If the documents don't fully answer the question, provide helpful context from general knowledge while being clear about the source

Answer:"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the LLM."""
        return """You are an expert RNA biology research assistant with deep knowledge of:
- CRISPR technology and genome editing
- DNA repair mechanisms (NHEJ, HDR, alt-EJ)
- RNA biology and molecular techniques
- Laboratory protocols and troubleshooting
- Scientific paper analysis and interpretation

Provide comprehensive, practical answers that help researchers solve real problems. 
When referencing tables or figures, explain their significance.
Always maintain scientific accuracy while being accessible."""
    
    def _calculate_confidence(self, search_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on search results."""
        if not search_results:
            return 0.0
        
        # Get top score
        top_score = search_results[0]['score']
        
        # Base confidence on hybrid score
        if top_score >= 0.9:
            base_confidence = 0.95
        elif top_score >= 0.8:
            base_confidence = 0.90
        elif top_score >= 0.7:
            base_confidence = 0.85
        elif top_score >= 0.6:
            base_confidence = 0.75
        elif top_score >= 0.5:
            base_confidence = 0.65
        else:
            base_confidence = 0.50
        
        # Boost for multiple high-quality results
        high_quality_results = sum(1 for r in search_results[:3] if r['score'] >= 0.7)
        if high_quality_results >= 3:
            base_confidence = min(0.95, base_confidence + 0.05)
        
        # Boost for exact chunk type matches
        if any(r['chunk_type'] == 'table' for r in search_results) and 'table' in search_results[0]['snippet'].lower():
            base_confidence = min(0.95, base_confidence + 0.05)
        
        return base_confidence
    
    def _extract_sources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract unique sources from search results."""
        unique_sources = {}
        
        for result in search_results[:5]:
            key = f"{result['title']}_{result['author']}_{result['year']}"
            if key not in unique_sources:
                unique_sources[key] = {
                    'title': result['title'],
                    'author': result['author'],
                    'year': result['year'],
                    'type': result['type']
                }
        
        return list(unique_sources.values())[:3]
    
    def initialize_with_documents(self):
        """Initialize the system with all documents in the database."""
        documents = Document.objects.all()
        
        if not documents.exists():
            print("No documents found in database")
            return
        
        print(f"Initializing enhanced RAG system with {documents.count()} documents...")
        
        for doc in documents:
            success = self.ingest_document(doc)
            if not success:
                print(f"Failed to ingest: {doc.title}")
        
        print("Initialization complete!")


# Global instance
enhanced_rag_system = None

def get_enhanced_rag_system(use_local_embeddings: bool = False) -> EnhancedRAGSystem:
    """Get or create the enhanced RAG system instance."""
    global enhanced_rag_system
    if enhanced_rag_system is None:
        enhanced_rag_system = EnhancedRAGSystem(use_local_embeddings=use_local_embeddings)
    return enhanced_rag_system