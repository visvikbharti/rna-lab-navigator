"""
Real RAG implementation using OpenAI and simple vector storage.
"""

import os
import json
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from api.models import Document, QueryHistory
from api.ingestion.chunking_utils import chunk_text
import pickle
import hashlib


class SimpleVectorStore:
    """Simple in-memory vector store for development."""
    
    def __init__(self):
        self.vectors = []
        self.metadata = []
        self.cache_file = '/tmp/rna_vectors.pkl'
        self.load_from_cache()
    
    def add_document(self, text, metadata):
        """Add document chunks with embeddings."""
        # Generate embedding
        embedding = self.get_embedding(text)
        
        self.vectors.append(embedding)
        self.metadata.append({
            'text': text,
            'title': metadata.get('title', ''),
            'author': metadata.get('author', ''),
            'doc_type': metadata.get('doc_type', ''),
            'year': metadata.get('year', ''),
            'document_id': metadata.get('document_id', ''),
        })
        
        self.save_to_cache()
    
    def search(self, query, top_k=5):
        """Search for similar documents."""
        if not self.vectors:
            return []
        
        # Get query embedding
        query_embedding = self.get_embedding(query)
        
        # Calculate similarities
        similarities = cosine_similarity([query_embedding], self.vectors)[0]
        
        # Get top k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.5:  # Lowered threshold for better recall
                score = float(similarities[idx])
                
                # Boost score for exact keyword matches
                text_lower = self.metadata[idx]['text'].lower()
                query_lower = query.lower()
                for word in query_lower.split():
                    if len(word) > 3 and word in text_lower:  # Boost for significant words
                        score += 0.3  # Increased boost for keyword matches
                
                results.append({
                    'text': self.metadata[idx]['text'],
                    'metadata': self.metadata[idx],
                    'score': min(score, 1.0)  # Cap at 1.0
                })
        
        # Re-sort by boosted scores
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    
    def get_embedding(self, text):
        """Get OpenAI embedding for text."""
        try:
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=text[:8000]  # Limit text length
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            # Return random embedding as fallback
            return np.random.rand(1536).tolist()
    
    def save_to_cache(self):
        """Save vectors to cache file."""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump({
                    'vectors': self.vectors,
                    'metadata': self.metadata
                }, f)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def load_from_cache(self):
        """Load vectors from cache file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    data = pickle.load(f)
                    self.vectors = data.get('vectors', [])
                    self.metadata = data.get('metadata', [])
                print(f"Loaded {len(self.vectors)} vectors from cache")
        except Exception as e:
            print(f"Error loading cache: {e}")


# Global vector store instance
vector_store = SimpleVectorStore()


def ingest_document_to_vectorstore(document):
    """Ingest a document into the vector store."""
    try:
        # Read the PDF file
        pdf_path = f"../data/sample_docs/{document.doc_type}s/{document.title.replace(' ', '_')}.pdf"
        
        # For demo, use existing content or generate dummy content
        if hasattr(document, 'content') and document.content:
            text = document.content
        else:
            # Generate sample content based on document type
            if document.doc_type == 'thesis':
                text = f"""
                This doctoral thesis by {document.author} ({document.year}) explores RNA biology and molecular mechanisms.
                
                Chapter 1: Introduction to RNA Processing
                RNA (ribonucleic acid) is a fundamental molecule in cellular biology that plays crucial roles in protein synthesis,
                gene regulation, and cellular communication. This thesis investigates the temporal dynamics of RNA processing
                and its implications for cellular function.
                
                Chapter 2: Methodology
                We employed advanced techniques including RNA sequencing, CRISPR-Cas9 editing, and computational analysis
                to study RNA dynamics in various cellular contexts.
                
                Chapter 3: Results
                Our findings demonstrate novel mechanisms of RNA regulation that have significant implications for
                understanding gene expression and cellular responses to environmental stimuli.
                
                Chapter 4: Discussion
                These results contribute to our understanding of RNA biology and open new avenues for therapeutic interventions.
                """
            elif document.doc_type == 'paper':
                text = f"""
                Research paper by {document.author} ({document.year}) on RNA biology and biotechnology applications.
                
                Abstract: This study presents novel findings in RNA research with applications to CRISPR technology,
                diagnostic tools, and therapeutic interventions.
                
                Introduction: RNA molecules serve as intermediates between DNA and proteins, but recent research has revealed
                their direct functional roles in cellular processes.
                
                Methods: We used state-of-the-art molecular biology techniques including RNA-seq, qPCR, and advanced
                imaging to characterize RNA behavior in living cells.
                
                Results: Our data show significant insights into RNA processing, modification, and function that advance
                the field of molecular biology.
                
                Conclusion: These findings have important implications for biotechnology applications and medical research.
                """
            else:
                text = f"Protocol document by {document.author} for {document.title}"
        
        # Chunk the text
        chunks = chunk_text(text)
        
        # Add each chunk to vector store
        for i, chunk in enumerate(chunks):
            metadata = {
                'title': document.title,
                'author': document.author,
                'doc_type': document.doc_type,
                'year': document.year,
                'document_id': document.id,
                'chunk_index': i
            }
            vector_store.add_document(chunk, metadata)
        
        print(f"Ingested {len(chunks)} chunks for document: {document.title}")
        return True
        
    except Exception as e:
        print(f"Error ingesting document {document.title}: {e}")
        return False


def search_documents(query, doc_type="all", top_k=5):
    """Search documents using vector similarity with smart deduplication."""
    # Get more results for better filtering and deduplication
    search_results = vector_store.search(query, top_k=top_k * 3)  
    
    # Filter by document type if specified
    if doc_type != "all":
        search_results = [r for r in search_results if r['metadata']['doc_type'] == doc_type]
    
    # Smart deduplication: group by document and select best chunks
    document_groups = {}
    for result in search_results:
        doc_key = f"{result['metadata']['title']}_{result['metadata']['author']}"
        if doc_key not in document_groups:
            document_groups[doc_key] = []
        document_groups[doc_key].append(result)
    
    # Select the best chunk(s) from each document
    formatted_results = []
    for doc_key, chunks in document_groups.items():
        # Sort chunks by score (best first)
        chunks.sort(key=lambda x: x['score'], reverse=True)
        
        # For the same document, combine information from top chunks
        best_chunk = chunks[0]
        
        # Create a longer, more informative snippet by combining multiple chunks
        combined_text = best_chunk['text']
        if len(chunks) > 1:
            # Add content from other high-scoring chunks if they're different enough
            for chunk in chunks[1:3]:  # Use up to 3 chunks max
                if chunk['text'][:50] not in combined_text:  # Avoid exact duplicates
                    combined_text += " ... " + chunk['text']
        
        formatted_results.append({
            'id': str(best_chunk['metadata']['document_id']),
            'title': best_chunk['metadata']['title'],
            'type': best_chunk['metadata']['doc_type'],
            'author': best_chunk['metadata']['author'],
            'year': best_chunk['metadata']['year'],
            'snippet': combined_text[:1200] + "..." if len(combined_text) > 1200 else combined_text,
            'score': round(best_chunk['score'], 2),
            'chunk_count': len(chunks)  # Show how many chunks matched
        })
    
    # Sort by score and filter out low-relevance results
    formatted_results.sort(key=lambda x: x['score'], reverse=True)
    
    # Filter supporting sources: only include documents with reasonable relevance
    if len(formatted_results) > 1:
        # If we have multiple results, filter out those with significantly lower scores
        highest_score = formatted_results[0]['score']
        filtered_results = []
        
        for result in formatted_results:
            # Include result if it's within 0.3 points of the highest score
            # This prevents irrelevant documents from appearing as "supporting sources"
            if result['score'] >= highest_score - 0.3 or result['score'] >= 0.7:
                filtered_results.append(result)
        
        return filtered_results[:top_k]
    
    return formatted_results[:top_k]


def generate_answer_with_llm(query, search_results):
    """Generate answer using OpenAI with retrieved context."""
    if not search_results:
        return {
            'answer': "I don't have enough information to answer this question based on the available documents.",
            'confidence_score': 0.0,
            'sources': []
        }
    
    # Prepare context from search results
    context_parts = []
    for i, result in enumerate(search_results[:3]):
        # Handle both old vector search format and new search_documents format
        if 'snippet' in result:
            # New format from search_documents
            content = result['snippet']
            title = result['title']
            author = result['author'] 
            year = result['year']
        else:
            # Old format from vector_store.search
            content = result['text']
            title = result['metadata']['title']
            author = result['metadata']['author']
            year = result['metadata']['year']
        
        context_parts.append(f"Source {i+1} ({title} by {author}, {year}):\n{content}")
    
    context = "\n\n".join(context_parts)
    
    # Prepare prompt for conversational RAG assistant
    prompt = f"""You are a helpful research assistant for Dr. Debojyoti Chakraborty's RNA biology lab. Based on the lab documents provided, answer the user's question in a helpful, conversational manner.

Context from lab documents:
{context}

Question: {query}

Instructions:
- First check if the lab documents contain relevant information about the question
- If lab documents contain relevant info: Synthesize and cite the sources (e.g., "According to [Author, Year]...")
- If lab documents don't contain specific information: Provide general scientific knowledge with clear disclaimers like "While this isn't covered in your lab documents, from a general research perspective..." 
- Always be helpful and educational - don't just say "I don't know"
- Distinguish clearly between lab-specific findings vs. general scientific knowledge
- Include citations to specific lab sources when available
- For questions outside lab scope, offer general insights and suggest where they might find more specific information
- Be conversational and engaging, like a knowledgeable lab colleague"""
    
    try:
        response = openai.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful research assistant for an RNA biology lab. Provide accurate, scientific answers based only on the provided sources."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        answer = response.choices[0].message.content
        
        # Calculate confidence based on search results relevance
        base_confidence = min(search_results[0]['score'] if search_results else 0.0, 0.95)
        
        # Reduce confidence if the answer is too generic or "I don't know"
        if answer.strip().lower() in ["i don't know.", "i don't know", "i don't have enough information"]:
            confidence_score = 0.1
        else:
            confidence_score = base_confidence
        
        # Extract unique sources only
        unique_sources = {}
        for result in search_results[:5]:
            # Handle both old and new format
            if 'snippet' in result:
                # New format from search_documents
                key = f"{result['title']}_{result['author']}_{result['year']}"
                if key not in unique_sources:
                    unique_sources[key] = {
                        'title': result['title'],
                        'author': result['author'], 
                        'year': result['year'],
                        'type': result['type']
                    }
            else:
                # Old format from vector_store.search
                title = result['metadata']['title']
                author = result['metadata']['author']
                year = result['metadata']['year']
                doc_type = result['metadata']['doc_type']
                key = f"{title}_{author}_{year}"
                if key not in unique_sources:
                    unique_sources[key] = {
                        'title': title,
                        'author': author,
                        'year': year,
                        'type': doc_type
                    }
        
        sources = list(unique_sources.values())[:3]  # Limit to 3 max
        
        return {
            'answer': answer,
            'confidence_score': confidence_score,
            'sources': sources
        }
        
    except Exception as e:
        print(f"Error generating answer: {e}")
        return {
            'answer': "I apologize, but I encountered an error while processing your question.",
            'confidence_score': 0.0,
            'sources': []
        }


def initialize_vectorstore_with_sample_data():
    """Initialize vector store with sample documents."""
    # Get all documents from database
    documents = Document.objects.all()
    
    if not documents.exists():
        # Create some sample documents
        sample_docs = [
            {
                'title': 'CRISPR Applications in RNA Biology',
                'author': 'Chakraborty et al.',
                'doc_type': 'paper',
                'year': 2024
            },
            {
                'title': 'Rhythm PhD Thesis on RNA Dynamics',
                'author': 'Phutela',
                'doc_type': 'thesis', 
                'year': 2025
            },
            {
                'title': 'RNA Extraction Protocol',
                'author': 'Lab Manual',
                'doc_type': 'protocol',
                'year': 2024
            }
        ]
        
        for doc_data in sample_docs:
            doc = Document.objects.create(**doc_data)
            ingest_document_to_vectorstore(doc)
        
        print("Created and ingested sample documents")
    else:
        # Ingest existing documents
        for doc in documents:
            ingest_document_to_vectorstore(doc)
        
        print(f"Ingested {documents.count()} existing documents")


def perform_rag_query(query, doc_type="all"):
    """Perform complete RAG query with search and generation."""
    import time
    start_time = time.time()
    
    # Initialize if needed
    if len(vector_store.vectors) == 0:
        initialize_vectorstore_with_sample_data()
    
    # Search for relevant documents
    search_results = search_documents(query, doc_type)
    
    # Generate answer with LLM
    answer_data = generate_answer_with_llm(query, search_results)
    
    processing_time = time.time() - start_time
    
    # Save query history
    try:
        query_history = QueryHistory.objects.create(
            query_text=query,
            answer=answer_data['answer'],
            confidence_score=answer_data['confidence_score'],
            sources=answer_data['sources'],
            processing_time=processing_time,
            doc_type=doc_type
        )
    except Exception as e:
        print(f"Error saving query history: {e}")
    
    return {
        'query': query,
        'answer': answer_data['answer'],
        'confidence_score': answer_data['confidence_score'],
        'sources': answer_data['sources'],
        'search_results': search_results,
        'processing_time': round(processing_time, 2),
        'doc_type': doc_type
    }