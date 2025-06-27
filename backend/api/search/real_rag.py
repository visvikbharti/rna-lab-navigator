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
from api.rag.enhanced_answer_validator import get_answer_validator, get_answer_enhancer
import pdfplumber
from pathlib import Path


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
        """Search for similar documents with improved recall."""
        if not self.vectors:
            print(f"[SEARCH DEBUG] No vectors available for query: {query}")
            return []
        
        # Get query embedding
        query_embedding = self.get_embedding(query)
        
        # Calculate similarities
        similarities = cosine_similarity([query_embedding], self.vectors)[0]
        
        # Get top k*3 results to ensure better coverage
        top_indices = np.argsort(similarities)[::-1][:top_k * 3]
        
        results = []
        for idx in top_indices:
            # Lower threshold from 0.5 to 0.3 for better recall
            if similarities[idx] > 0.3:
                score = float(similarities[idx])
                
                # Boost score for exact keyword matches
                text_lower = self.metadata[idx]['text'].lower()
                query_lower = query.lower()
                
                # Extract key terms from query (split on common delimiters)
                query_terms = []
                # Special handling for author queries
                if 'work' in query_lower or 'paper' in query_lower or 'research' in query_lower:
                    # Extract potential author names (typically proper nouns)
                    for word in query.split():  # Use original case for names
                        if word[0].isupper() and len(word) > 2:  # Likely a name
                            query_terms.append(word.lower())
                
                # Extract all significant terms
                for word in query_lower.replace('-', ' ').replace('_', ' ').replace("'s", "").split():
                    if len(word) > 2 and word not in ['the', 'and', 'for', 'from', 'about', 'work', 'paper', 'research']:
                        query_terms.append(word)
                
                
                # Initialize match counters
                exact_matches = 0
                partial_matches = 0
                
                # Check for author name matches (high priority)
                author_name = self.metadata[idx].get('author', '').lower()
                all_authors = self.metadata[idx].get('all_authors', '').lower()
                title = self.metadata[idx].get('title', '').lower()
                
                # Strong boost for author name matches
                for term in query_terms:
                    # Check both single author and all authors fields
                    if term in author_name or term in all_authors:
                        score += 2.0  # MASSIVE boost for author match
                        exact_matches += 5  # Count as multiple matches
                    if term in title:
                        score += 1.0  # Strong boost for title match
                
                # Check for exact and partial matches in content
                for term in query_terms:
                    if term in text_lower:
                        exact_matches += 1
                        score += 0.2  # Boost for exact match
                    else:
                        # Check for partial matches (e.g., "cas9" in "fncas9")
                        for text_word in text_lower.split():
                            if term in text_word or text_word in term:
                                partial_matches += 1
                                score += 0.1  # Smaller boost for partial match
                                break
                
                # Additional boost if multiple terms match
                if exact_matches >= 2:
                    score += 0.2
                
                # Check for relevant technical terms
                tech_terms = ['rna', 'cas9', 'crispr', 'protocol', 'thesis', 'paper', 
                             'gene', 'editing', 'sequencing', 'pcr', 'western', 'blot']
                for term in tech_terms:
                    if term in text_lower and term in query_lower:
                        score += 0.1
                
                result_data = {
                    'text': self.metadata[idx]['text'],
                    'metadata': self.metadata[idx],
                    'score': score,  # Don't cap score for author matches
                    'exact_matches': exact_matches,
                    'partial_matches': partial_matches
                }
                
                results.append(result_data)
        
        # Re-sort by boosted scores
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top k results after boosting
        return results[:top_k]
    
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


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n\n"
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
    return text


def ingest_document_to_vectorstore(document):
    """Ingest a document into the vector store."""
    try:
        # Construct the PDF path
        base_path = Path(__file__).parent.parent.parent.parent  # Go up to project root
        # Handle plural forms correctly
        if document.doc_type == 'thesis':
            dir_name = 'theses'
        elif document.doc_type == 'protocol':
            dir_name = 'community_protocols'  # Based on actual directory name
        else:
            dir_name = f"{document.doc_type}s"
        doc_dir = base_path / 'data' / 'sample_docs' / dir_name
        
        # List all PDFs in the directory for debugging
        if doc_dir.exists():
            pdf_files = list(doc_dir.glob("*.pdf"))
            print(f"Available PDFs in {doc_dir.name}: {[f.name for f in pdf_files]}")
        else:
            print(f"Directory does not exist: {doc_dir}")
        
        # Try different filename patterns
        text = ""
        pdf_path = None
        
        # For thesis with "Real Content" suffix, try without it
        if document.doc_type == 'thesis' and 'Real Content' in document.title:
            clean_title = document.title.replace(' - Real Content', '')
            pdf_filename = clean_title.replace(' ', '_') + '.pdf'
            pdf_path = doc_dir / pdf_filename
            if pdf_path.exists():
                print(f"Found thesis PDF: {pdf_path}")
                text = extract_text_from_pdf(str(pdf_path))
        
        # Try exact match with underscores
        if not text:
            pdf_filename = document.title.replace(' ', '_').replace('.', '_') + '.pdf'
            pdf_path = doc_dir / pdf_filename
            if pdf_path.exists():
                print(f"Reading PDF from: {pdf_path}")
                text = extract_text_from_pdf(str(pdf_path))
        
        # Try with hyphens instead of underscores
        if not text:
            pdf_filename = document.title.replace(' ', '-').replace('.', '-') + '.pdf'
            pdf_path = doc_dir / pdf_filename
            if pdf_path.exists():
                print(f"Reading PDF from: {pdf_path}")
                text = extract_text_from_pdf(str(pdf_path))
        
        # For protocols, try exact filename matches from the listing
        if not text and doc_dir.exists():
            # Try case-insensitive match
            doc_title_lower = document.title.lower().replace(' ', '').replace('-', '').replace('_', '').replace('.', '')
            for pdf_file in pdf_files:
                pdf_name_lower = pdf_file.stem.lower().replace(' ', '').replace('-', '').replace('_', '').replace('.', '')
                if doc_title_lower in pdf_name_lower or pdf_name_lower in doc_title_lower:
                    print(f"Found matching PDF by fuzzy match: {pdf_file}")
                    text = extract_text_from_pdf(str(pdf_file))
                    if text:
                        break
        
        if text:
            print(f"Successfully extracted {len(text)} characters from PDF")
        
        # Only use minimal fallback if PDF reading failed
        if not text:
            print(f"ERROR: Could not read PDF for {document.title}")
            # Return False to indicate failure - don't ingest fake content
            return False
        
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
    # Increase search size to ensure we get enough relevant documents
    search_results = vector_store.search(query, top_k=max(top_k * 5, 25))
    
    print(f"\n[SEARCH DEBUG] Initial results: {len(search_results)}")
    if search_results:
        print(f"[SEARCH DEBUG] Top 5 raw results:")
        for i, r in enumerate(search_results[:5]):
            print(f"  {i+1}. {r['metadata']['title']} by {r['metadata']['author']} (score: {r['score']:.3f})")  
    
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
    """Generate answer using OpenAI with retrieved context and quality validation."""
    validator = get_answer_validator()
    enhancer = get_answer_enhancer()
    
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
    
    # Prepare prompt for conversational RAG assistant with research intelligence
    prompt = f"""You are an expert research assistant for Dr. Debojyoti Chakraborty's RNA biology lab at CSIR-IGIB. Your role is to help lab members with their research by providing accurate, detailed, and practical information based on the lab's documents and your scientific expertise.

Context from lab documents:
{context}

Question: {query}

Instructions:
1. **Primary Response**: If the lab documents contain relevant information:
   - Provide a comprehensive answer synthesizing information from the sources
   - Include specific details, protocols, concentrations, timings, etc.
   - Cite sources naturally in the flow (e.g., "According to Rhythm Phutela's thesis (2025)...")
   - Add practical tips or troubleshooting advice if applicable

2. **Secondary Response**: If lab documents don't have specific information:
   - Still provide a helpful, educational response based on general RNA biology knowledge
   - Be transparent: "While not specifically covered in your lab's documents, here's what's generally known..."
   - Suggest relevant techniques, protocols, or approaches
   - Recommend where to find more specific information

3. **Research Intelligence** (ALWAYS include this section after your answer):
   Start with "### Research Intelligence:" then provide:
   
   🧪 **Experiment Suggestion**: Based on this information, design a specific experiment they could try. Include:
      - Hypothesis to test
      - Key steps with specific conditions (concentrations, times, temperatures)
      - Expected timeline and approximate cost
   
   🤔 **Critical Questions**: 2-3 questions they should consider but might not have thought of:
      - Alternative interpretations
      - Potential confounding factors
      - Related areas to explore
   
   ⚡ **Quick Win**: A simple pilot experiment they could do TODAY or this week:
      - Should take <1 day
      - Use existing lab resources
      - Give actionable results
   
   ⚠️ **Watch Out**: Common pitfalls or contradictions:
      - What could go wrong
      - Conflicting findings in literature
      - Technical challenges to anticipate
   
   💡 **Novel Idea**: Creative approach combining insights:
      - Connect findings from different papers/sources
      - Suggest innovative methodology
      - Identify unexplored angles

4. **Style Guidelines**:
   - Be conversational yet professional, like a knowledgeable senior lab member
   - Use clear, accessible language while maintaining scientific accuracy
   - Be specific with ALL suggestions (no vague advice)
   - Reference the provided sources when making suggestions

5. **Never**:
   - Give a simple "I don't know" - always try to be helpful
   - Make up specific data or results not in the documents
   - Confuse general knowledge with lab-specific findings
   - Provide generic suggestions - be specific to their research context

Remember: You're not just answering questions - you're actively helping design the next experiment!"""
    
    try:
        response = openai.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert RNA biology research assistant with deep knowledge of molecular biology, CRISPR technology, and laboratory techniques. Provide comprehensive, practical answers that help researchers solve real problems."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.1
        )
        
        answer = response.choices[0].message.content
        
        # Calculate confidence based on search results relevance
        if search_results:
            # Get the top score and normalize it
            top_score = search_results[0]['score']
            
            # Scores above 2.0 are very good matches
            if top_score >= 5.0:
                base_confidence = 0.95  # Excellent match
            elif top_score >= 3.0:
                base_confidence = 0.90  # Very good match
            elif top_score >= 2.0:
                base_confidence = 0.85  # Good match
            elif top_score >= 1.5:
                base_confidence = 0.75  # Decent match
            elif top_score >= 1.0:
                base_confidence = 0.65  # Fair match
            else:
                base_confidence = 0.50  # Weak match
        else:
            base_confidence = 0.0
        
        # Reduce confidence if the answer is too generic or "I don't know"
        if "I don't have" in answer or "not specifically mentioned" in answer or "documents provided do not" in answer:
            confidence_score = base_confidence * 0.7  # Reduce by 30% for uncertain answers
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
        
        # Validate answer quality
        validation_results = validator.validate_answer(
            query, answer, confidence_score, sources
        )
        
        # Use enhanced answer if validation found issues
        if not validation_results['is_valid'] or validation_results['enhanced_answer'] != answer:
            answer = validation_results['enhanced_answer']
        
        # Apply answer formatting based on type
        answer_type = enhancer.detect_answer_type(query)
        answer = enhancer.enhance_answer(query, answer, answer_type)
        
        # Update confidence based on validation
        if validation_results['quality_score'] > 0:
            confidence_score = (confidence_score + validation_results['quality_score']) / 2
        
        return {
            'answer': answer,
            'confidence_score': confidence_score,
            'sources': sources,
            'validation': validation_results
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
        # DISABLED: initialize_vectorstore_with_sample_data()  # Use Weaviate instead
        pass  # Use Weaviate vectors loaded externally
    
    # Search for relevant documents
    search_results = search_documents(query, doc_type)
    
    # Debug: Log search results
    print(f"\n[DEBUG] Query: {query}")
    print(f"[DEBUG] Found {len(search_results)} search results:")
    for i, result in enumerate(search_results):
        print(f"  {i+1}. {result['title']} by {result['author']} (score: {result['score']})")
    
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