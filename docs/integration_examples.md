# Integration Examples

This document provides practical examples of integrating with the RNA Lab Navigator API for common workflows.

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Query Examples](#query-examples)
4. [Batch Document Ingestion](#batch-document-ingestion)
5. [Search Integration](#search-integration)
6. [Feedback Collection](#feedback-collection)
7. [Protocol Workflows](#protocol-workflows)
8. [Laboratory Information Management System Integration](#laboratory-information-management-system-integration)
9. [Instrument Integration](#instrument-integration)
10. [External Tool Integration](#external-tool-integration)

## Introduction

The RNA Lab Navigator provides a comprehensive API that can be integrated with various laboratory systems and tools. This document shows practical examples using different programming languages and frameworks.

### Base URL

All examples assume the API is available at:

```
https://your-domain.com/api/
```

For local development:

```
http://localhost:8000/api/
```

## Authentication

Before using most API endpoints, you need to authenticate.

### Python Example

```python
import requests
import json

def get_auth_token(username, password):
    """Get JWT token for API authentication."""
    url = "http://localhost:8000/api/auth/token/"
    
    payload = {
        "username": username,
        "password": password
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        tokens = response.json()
        return tokens["access"], tokens["refresh"]
    else:
        print(f"Authentication failed: {response.text}")
        return None, None

# Usage
access_token, refresh_token = get_auth_token("lab_user", "secure_password")

# Add token to requests
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Example authenticated request
response = requests.get("http://localhost:8000/api/history/", headers=headers)
print(response.json())
```

### JavaScript Example

```javascript
async function getAuthToken(username, password) {
  try {
    const response = await fetch('http://localhost:8000/api/auth/token/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        password,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Authentication failed: ${response.statusText}`);
    }
    
    const data = await response.json();
    return {
      accessToken: data.access,
      refreshToken: data.refresh,
    };
  } catch (error) {
    console.error('Error during authentication:', error);
    return null;
  }
}

// Usage
(async () => {
  const tokens = await getAuthToken('lab_user', 'secure_password');
  
  if (tokens) {
    const headers = {
      'Authorization': `Bearer ${tokens.accessToken}`,
      'Content-Type': 'application/json',
    };
    
    // Example authenticated request
    const response = await fetch('http://localhost:8000/api/history/', {
      headers,
    });
    
    const data = await response.json();
    console.log(data);
  }
})();
```

## Query Examples

### Basic Query Example (Python)

```python
import requests

def query_rna_navigator(question, doc_type=None, access_token=None):
    """Query the RNA Lab Navigator for answers."""
    url = "http://localhost:8000/api/query/"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    
    payload = {
        "query": question,
        "use_hybrid": True
    }
    
    if doc_type:
        payload["doc_type"] = doc_type
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        return result
    else:
        print(f"Query failed: {response.text}")
        return None

# Example usage
result = query_rna_navigator("What's the protocol for RNA extraction using TRIzol?", doc_type="protocol")

if result:
    print(f"Answer: {result['answer']}")
    print("\nSources:")
    for i, source in enumerate(result['sources']['documents'], 1):
        print(f"{i}. {source['title']} ({source['doc_type']})")
```

### Streaming Query Example (JavaScript)

```javascript
function streamQuery(question, docType = null) {
  const url = new URL('http://localhost:8000/api/query/');
  url.searchParams.append('stream', 'true');
  
  const payload = {
    query: question,
    use_hybrid: true
  };
  
  if (docType) {
    payload.doc_type = docType;
  }
  
  // Result containers
  let answer = '';
  let sources = [];
  let figures = [];
  
  // Set up event source
  const eventSource = new EventSource(url);
  
  return new Promise((resolve, reject) => {
    // Handle metadata event (first event with sources)
    eventSource.addEventListener('message', function(event) {
      const data = JSON.parse(event.data);
      
      if (data.type === 'metadata') {
        sources = data.sources || [];
        figures = data.figures || [];
        
        // Update UI with sources
        displaySources(sources, figures);
      }
      else if (data.type === 'content') {
        // Append content chunk to answer
        answer += data.content;
        
        // Update UI with partial answer
        displayPartialAnswer(answer);
      }
      else if (data.type === 'final') {
        // Handle final message with confidence score
        const result = {
          answer,
          sources,
          figures,
          confidence_score: data.confidence_score,
          status: data.status,
          query_id: data.query_id
        };
        
        // Close the connection
        eventSource.close();
        resolve(result);
      }
    });
    
    // Handle errors
    eventSource.onerror = function(error) {
      eventSource.close();
      reject(error);
    };
  });
}

// Example usage with UI updates
async function askQuestion() {
  const question = document.getElementById('question-input').value;
  const docType = document.getElementById('doc-type-select').value || null;
  
  // Clear previous results
  document.getElementById('answer-container').innerText = '';
  document.getElementById('sources-container').innerHTML = '';
  
  try {
    const result = await streamQuery(question, docType);
    
    // Final UI update with complete result
    displayFinalAnswer(result);
    
    // Enable feedback UI
    enableFeedbackButtons(result.query_id);
  } catch (error) {
    console.error('Error during query:', error);
    document.getElementById('answer-container').innerText = 'An error occurred while processing your query.';
  }
}

// Helper functions for UI updates
function displayPartialAnswer(text) {
  document.getElementById('answer-container').innerText = text;
}

function displaySources(sources, figures) {
  const sourcesContainer = document.getElementById('sources-container');
  sourcesContainer.innerHTML = '';
  
  // Display document sources
  sources.forEach((source, index) => {
    const sourceElement = document.createElement('div');
    sourceElement.className = 'source-item';
    sourceElement.innerHTML = `
      <span class="source-number">[${index + 1}]</span>
      <span class="source-title">${source.title}</span>
      <span class="source-type">(${source.doc_type})</span>
      ${source.author ? `<span class="source-author">by ${source.author}</span>` : ''}
    `;
    sourcesContainer.appendChild(sourceElement);
  });
  
  // Display figures
  figures.forEach((figure) => {
    const figureElement = document.createElement('div');
    figureElement.className = 'figure-item';
    figureElement.innerHTML = `
      <div class="figure-header">
        <span class="figure-title">${figure.figure_type} from ${figure.doc_title}</span>
      </div>
      <div class="figure-caption">${figure.caption}</div>
      <img src="${figure.api_path}" alt="${figure.caption}" class="figure-preview">
    `;
    sourcesContainer.appendChild(figureElement);
  });
}
```

## Batch Document Ingestion

### Python Script for Batch Ingestion

```python
import os
import requests
import pandas as pd
import argparse
from tqdm import tqdm

def batch_ingest_documents(folder_path, metadata_csv, api_url, access_token):
    """
    Batch ingest documents from a folder using metadata from a CSV file.
    
    Parameters:
    - folder_path: Path to folder containing documents
    - metadata_csv: Path to CSV file with document metadata
    - api_url: Base URL for the RNA Lab Navigator API
    - access_token: JWT token for authentication
    """
    # Read metadata CSV
    metadata = pd.read_csv(metadata_csv)
    
    # Check required columns
    required_columns = ['filename', 'title', 'doc_type', 'author', 'year']
    for col in required_columns:
        if col not in metadata.columns:
            raise ValueError(f"Metadata CSV must contain column: {col}")
    
    # Set up headers
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    successful = 0
    failed = 0
    
    # Process each document
    for _, row in tqdm(metadata.iterrows(), total=len(metadata)):
        file_path = os.path.join(folder_path, row['filename'])
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            failed += 1
            continue
        
        # Prepare request data
        url = f"{api_url}/documents/upload/"
        
        data = {
            "title": row['title'],
            "doc_type": row['doc_type'],
            "author": row['author'],
            "year": int(row['year'])
        }
        
        # Add optional fields if present
        optional_fields = ['keywords', 'abstract', 'chapter', 'source']
        for field in optional_fields:
            if field in metadata.columns and not pd.isna(row[field]):
                data[field] = row[field]
        
        # Upload file
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            
            try:
                response = requests.post(url, data=data, files=files, headers=headers)
                
                if response.status_code == 201:
                    document_id = response.json()['id']
                    print(f"Successfully ingested: {row['filename']} (ID: {document_id})")
                    successful += 1
                else:
                    print(f"Failed to ingest {row['filename']}: {response.text}")
                    failed += 1
            except Exception as e:
                print(f"Error ingesting {row['filename']}: {str(e)}")
                failed += 1
    
    print(f"\nIngestion complete: {successful} successful, {failed} failed")
    return successful, failed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch ingest documents into RNA Lab Navigator")
    parser.add_argument("folder", help="Path to folder containing documents")
    parser.add_argument("metadata", help="Path to CSV file with document metadata")
    parser.add_argument("--api-url", default="http://localhost:8000/api", help="Base API URL")
    parser.add_argument("--token", required=True, help="JWT access token")
    
    args = parser.parse_args()
    
    batch_ingest_documents(args.folder, args.metadata, args.api_url, args.token)
```

### Metadata CSV Format

```csv
filename,title,doc_type,author,year,keywords,abstract,chapter,source
protocol_RNAextraction.pdf,RNA Extraction Protocol,protocol,Lab Manager,2023,RNA isolation;TRIzol;extraction,Standard protocol for RNA extraction using TRIzol reagent,,
western_blot.pdf,Western Blot Protocol,protocol,Sharma R.,2024,protein;western blot;detection,Detailed protocol for western blot analysis,,
2023_Ghosh_NatMed_SARS2_Variant_PaperStrip_Dx.pdf,SARS-CoV-2 Variant Detection via Paper Strip Diagnostics,paper,Ghosh A.,2023,CRISPR;diagnostics;COVID-19,Novel paper-based diagnostic for SARS-CoV-2 variants,,Nature Medicine
```

## Search Integration

### Advanced Search with Filters (Python)

```python
import requests

def advanced_search(query, filters=None, use_hybrid=True, include_figures=False, access_token=None):
    """
    Perform advanced search with filters in RNA Lab Navigator.
    
    Parameters:
    - query: Search query string
    - filters: Dictionary of filters to apply
    - use_hybrid: Whether to use hybrid search (vector + keyword)
    - include_figures: Whether to include figure results
    - access_token: JWT token for authentication
    
    Returns:
    - Search results dictionary
    """
    url = "http://localhost:8000/api/search/advanced/"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    
    payload = {
        "query": query,
        "use_hybrid": use_hybrid,
        "include_figures": include_figures,
        "limit": 20
    }
    
    if filters:
        payload["filters"] = filters
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Search failed: {response.text}")
        return None

# Example usage with filters
filters = {
    "doc_type": ["protocol", "troubleshooting"],
    "year": {"gte": 2023},  # Documents from 2023 or later
    "author": "Kumar"
}

results = advanced_search(
    "RNA extraction TRIzol",
    filters=filters,
    use_hybrid=True,
    include_figures=True
)

if results:
    print(f"Found {results['count']} results")
    
    print("\nDocuments:")
    for doc in results['results']:
        print(f"- {doc['title']} ({doc['doc_type']}, {doc.get('year', 'N/A')}) - Score: {doc['relevance_score']:.2f}")
    
    if 'figures' in results and results['figures']:
        print("\nFigures:")
        for fig in results['figures']:
            print(f"- {fig['figure_type']} from {fig['doc_title']} - {fig['caption'][:50]}...")
```

### Custom Search Component (React)

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const SearchComponent = () => {
  const [query, setQuery] = useState('');
  const [docType, setDocType] = useState('');
  const [yearRange, setYearRange] = useState({ min: 2000, max: 2025 });
  const [author, setAuthor] = useState('');
  const [includeFigures, setIncludeFigures] = useState(false);
  
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      // Build filters
      const filters = {};
      
      if (docType) {
        filters.doc_type = [docType];
      }
      
      if (yearRange.min || yearRange.max) {
        filters.year = {};
        if (yearRange.min) filters.year.gte = yearRange.min;
        if (yearRange.max) filters.year.lte = yearRange.max;
      }
      
      if (author) {
        filters.author = author;
      }
      
      // Make API request
      const response = await axios.post(`${API_URL}/search/advanced/`, {
        query,
        filters,
        use_hybrid: true,
        include_figures: includeFigures,
        limit: 20
      });
      
      setResults(response.data);
    } catch (err) {
      setError('Search failed: ' + (err.response?.data?.error || err.message));
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="search-container">
      <form onSubmit={handleSearch} className="search-form">
        <div className="search-input-group">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter search query..."
            className="search-input"
            required
          />
          <button type="submit" className="search-button" disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
        
        <div className="search-filters">
          <div className="filter-group">
            <label>Document Type:</label>
            <select value={docType} onChange={(e) => setDocType(e.target.value)}>
              <option value="">All Types</option>
              <option value="protocol">Protocols</option>
              <option value="paper">Papers</option>
              <option value="thesis">Theses</option>
              <option value="troubleshooting">Troubleshooting</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label>Year Range:</label>
            <div className="year-range">
              <input
                type="number"
                value={yearRange.min}
                onChange={(e) => setYearRange({ ...yearRange, min: parseInt(e.target.value) })}
                placeholder="Min Year"
                min="1900"
                max="2100"
              />
              <span>to</span>
              <input
                type="number"
                value={yearRange.max}
                onChange={(e) => setYearRange({ ...yearRange, max: parseInt(e.target.value) })}
                placeholder="Max Year"
                min="1900"
                max="2100"
              />
            </div>
          </div>
          
          <div className="filter-group">
            <label>Author:</label>
            <input
              type="text"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              placeholder="Author name"
            />
          </div>
          
          <div className="filter-group">
            <label>
              <input
                type="checkbox"
                checked={includeFigures}
                onChange={(e) => setIncludeFigures(e.target.checked)}
              />
              Include Figures
            </label>
          </div>
        </div>
      </form>
      
      {error && <div className="search-error">{error}</div>}
      
      {results && (
        <div className="search-results">
          <h2>Search Results ({results.count})</h2>
          
          <div className="document-results">
            <h3>Documents</h3>
            {results.results.length === 0 ? (
              <p>No documents found.</p>
            ) : (
              results.results.map((doc) => (
                <div key={doc.id} className="document-result">
                  <h4>{doc.title}</h4>
                  <div className="result-meta">
                    <span className="doc-type">{doc.doc_type}</span>
                    {doc.author && <span className="author">by {doc.author}</span>}
                    {doc.year && <span className="year">{doc.year}</span>}
                  </div>
                  <div className="result-preview">{doc.content_preview}</div>
                  <div className="result-score">
                    Relevance: {(doc.relevance_score * 100).toFixed(1)}%
                  </div>
                </div>
              ))
            )}
          </div>
          
          {includeFigures && results.figures && results.figures.length > 0 && (
            <div className="figure-results">
              <h3>Figures</h3>
              <div className="figure-grid">
                {results.figures.map((figure) => (
                  <div key={figure.figure_id} className="figure-card">
                    <img src={`${API_URL}${figure.image_url}`} alt={figure.caption} />
                    <div className="figure-info">
                      <p className="figure-caption">{figure.caption}</p>
                      <p className="figure-source">
                        From: {figure.doc_title}
                        {figure.page_number && ` (p.${figure.page_number})`}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchComponent;
```

## Feedback Collection

### Feedback Widget (JavaScript)

```javascript
class RNANavigatorFeedback {
  constructor(options = {}) {
    this.apiUrl = options.apiUrl || 'http://localhost:8000/api';
    this.token = options.token || null;
    this.containerSelector = options.containerSelector || '#feedback-container';
    this.autoAttach = options.autoAttach !== false;
    
    this.container = null;
    this.currentQueryId = null;
    
    if (this.autoAttach) {
      document.addEventListener('DOMContentLoaded', () => this.init());
    }
  }
  
  init() {
    this.container = document.querySelector(this.containerSelector);
    if (!this.container) {
      console.error(`Feedback container not found: ${this.containerSelector}`);
      return;
    }
    
    this.render();
    this.attachEvents();
  }
  
  setQueryId(queryId) {
    this.currentQueryId = queryId;
    this.container.setAttribute('data-query-id', queryId);
    this.enableFeedbackButtons();
  }
  
  enableFeedbackButtons() {
    const buttons = this.container.querySelectorAll('.feedback-button');
    buttons.forEach(btn => {
      btn.disabled = !this.currentQueryId;
    });
  }
  
  render() {
    this.container.innerHTML = `
      <div class="feedback-widget">
        <div class="feedback-question">Was this answer helpful?</div>
        <div class="feedback-buttons">
          <button class="feedback-button" data-rating="thumbs_up" disabled>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
            </svg>
            Helpful
          </button>
          <button class="feedback-button" data-rating="thumbs_down" disabled>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path>
            </svg>
            Not Helpful
          </button>
        </div>
        <div class="feedback-form" style="display: none;">
          <div class="feedback-rating-details">
            <div class="rating-group">
              <label>Retrieval Quality:</label>
              <div class="star-rating">
                <input type="radio" name="retrieval_quality" value="1" id="retrieval-1"><label for="retrieval-1">1</label>
                <input type="radio" name="retrieval_quality" value="2" id="retrieval-2"><label for="retrieval-2">2</label>
                <input type="radio" name="retrieval_quality" value="3" id="retrieval-3"><label for="retrieval-3">3</label>
                <input type="radio" name="retrieval_quality" value="4" id="retrieval-4" checked><label for="retrieval-4">4</label>
                <input type="radio" name="retrieval_quality" value="5" id="retrieval-5"><label for="retrieval-5">5</label>
              </div>
            </div>
            <div class="rating-group">
              <label>Answer Relevance:</label>
              <div class="star-rating">
                <input type="radio" name="answer_relevance" value="1" id="relevance-1"><label for="relevance-1">1</label>
                <input type="radio" name="answer_relevance" value="2" id="relevance-2"><label for="relevance-2">2</label>
                <input type="radio" name="answer_relevance" value="3" id="relevance-3"><label for="relevance-3">3</label>
                <input type="radio" name="answer_relevance" value="4" id="relevance-4" checked><label for="relevance-4">4</label>
                <input type="radio" name="answer_relevance" value="5" id="relevance-5"><label for="relevance-5">5</label>
              </div>
            </div>
            <div class="rating-group">
              <label>Citation Accuracy:</label>
              <div class="star-rating">
                <input type="radio" name="citation_accuracy" value="1" id="citation-1"><label for="citation-1">1</label>
                <input type="radio" name="citation_accuracy" value="2" id="citation-2"><label for="citation-2">2</label>
                <input type="radio" name="citation_accuracy" value="3" id="citation-3"><label for="citation-3">3</label>
                <input type="radio" name="citation_accuracy" value="4" id="citation-4" checked><label for="citation-4">4</label>
                <input type="radio" name="citation_accuracy" value="5" id="citation-5"><label for="citation-5">5</label>
              </div>
            </div>
          </div>
          <div class="issues-section">
            <label>Issues (select all that apply):</label>
            <div class="issue-checkboxes">
              <label><input type="checkbox" name="specific_issues" value="missing_information"> Missing important information</label>
              <label><input type="checkbox" name="specific_issues" value="incorrect_information"> Incorrect information</label>
              <label><input type="checkbox" name="specific_issues" value="missing_citation"> Missing citation</label>
              <label><input type="checkbox" name="specific_issues" value="wrong_citation"> Wrong citation</label>
              <label><input type="checkbox" name="specific_issues" value="outdated_information"> Outdated information</label>
              <label><input type="checkbox" name="specific_issues" value="incomplete_answer"> Incomplete answer</label>
            </div>
          </div>
          <div class="feedback-comments">
            <label for="feedback-comment">Additional comments:</label>
            <textarea id="feedback-comment" rows="3" placeholder="Please provide any additional feedback..."></textarea>
          </div>
          <div class="feedback-actions">
            <button class="feedback-submit">Submit Feedback</button>
            <button class="feedback-cancel">Cancel</button>
          </div>
        </div>
        <div class="feedback-thankyou" style="display: none;">
          Thank you for your feedback!
        </div>
      </div>
    `;
  }
  
  attachEvents() {
    // Initial rating buttons
    const ratingButtons = this.container.querySelectorAll('.feedback-button');
    ratingButtons.forEach(button => {
      button.addEventListener('click', () => {
        const rating = button.getAttribute('data-rating');
        this.showFeedbackForm(rating);
      });
    });
    
    // Submit button
    const submitButton = this.container.querySelector('.feedback-submit');
    submitButton.addEventListener('click', () => this.submitFeedback());
    
    // Cancel button
    const cancelButton = this.container.querySelector('.feedback-cancel');
    cancelButton.addEventListener('click', () => this.hideFeedbackForm());
  }
  
  showFeedbackForm(rating) {
    this.selectedRating = rating;
    
    // Hide buttons, show form
    this.container.querySelector('.feedback-buttons').style.display = 'none';
    this.container.querySelector('.feedback-form').style.display = 'block';
  }
  
  hideFeedbackForm() {
    // Show buttons, hide form
    this.container.querySelector('.feedback-buttons').style.display = 'flex';
    this.container.querySelector('.feedback-form').style.display = 'none';
  }
  
  async submitFeedback() {
    if (!this.currentQueryId) {
      console.error('No query ID set');
      return;
    }
    
    // Collect form data
    const retrievalQuality = parseInt(
      this.container.querySelector('input[name="retrieval_quality"]:checked').value
    );
    
    const answerRelevance = parseInt(
      this.container.querySelector('input[name="answer_relevance"]:checked').value
    );
    
    const citationAccuracy = parseInt(
      this.container.querySelector('input[name="citation_accuracy"]:checked').value
    );
    
    const specificIssues = Array.from(
      this.container.querySelectorAll('input[name="specific_issues"]:checked')
    ).map(cb => cb.value);
    
    const comments = this.container.querySelector('#feedback-comment').value;
    
    // Prepare payload
    const payload = {
      query_id: this.currentQueryId,
      rating: this.selectedRating,
      retrieval_quality: retrievalQuality,
      answer_relevance: answerRelevance,
      citation_accuracy: citationAccuracy,
      specific_issues: specificIssues,
      comments: comments
    };
    
    try {
      // Set up headers
      const headers = {
        'Content-Type': 'application/json'
      };
      
      if (this.token) {
        headers['Authorization'] = `Bearer ${this.token}`;
      }
      
      // Send feedback
      const response = await fetch(`${this.apiUrl}/feedback/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        throw new Error(`Feedback submission failed: ${response.statusText}`);
      }
      
      // Show thank you message
      this.container.querySelector('.feedback-form').style.display = 'none';
      this.container.querySelector('.feedback-thankyou').style.display = 'block';
      
      // Reset after 3 seconds
      setTimeout(() => {
        this.container.querySelector('.feedback-thankyou').style.display = 'none';
        this.container.querySelector('.feedback-buttons').style.display = 'flex';
        this.container.querySelector('.feedback-form').style.reset();
      }, 3000);
      
    } catch (error) {
      console.error('Error submitting feedback:', error);
      alert('Failed to submit feedback. Please try again.');
    }
  }
}

// Usage
const feedbackWidget = new RNANavigatorFeedback({
  apiUrl: 'http://localhost:8000/api',
  containerSelector: '#rna-feedback'
});

// When you get a query response:
feedbackWidget.setQueryId(response.query_id);
```

## Protocol Workflows

### Protocol Steps Extractor (Python)

```python
import requests
import re

def extract_protocol_steps(protocol_query, access_token=None):
    """
    Extract protocol steps from RNA Lab Navigator for use in lab procedures.
    
    Parameters:
    - protocol_query: Specific protocol to search for
    - access_token: JWT token for authentication (optional)
    
    Returns:
    - Dictionary with protocol steps and metadata
    """
    # First, query the navigator for the protocol
    url = "http://localhost:8000/api/query/"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    
    payload = {
        "query": f"What are the detailed steps for {protocol_query}?",
        "doc_type": "protocol",
        "use_hybrid": True
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        print(f"Query failed: {response.text}")
        return None
    
    result = response.json()
    
    # Extract steps from the answer
    answer = result['answer']
    
    # Extract numbered steps using regex
    steps = []
    
    # Common patterns for numbered steps
    patterns = [
        r'(\d+)\.\s+(.*?)(?=\d+\.\s+|$)',  # Format: 1. Step one
        r'Step\s+(\d+)[:\.\)]\s+(.*?)(?=Step\s+\d+|$)',  # Format: Step 1: Do this
        r'(\d+)\)\s+(.*?)(?=\d+\)|$)'  # Format: 1) Do this
    ]
    
    # Try each pattern
    for pattern in patterns:
        matches = re.findall(pattern, answer, re.DOTALL)
        if matches:
            steps = [(int(num), step.strip()) for num, step in matches]
            break
    
    # If no structured steps found, create a single step with the whole answer
    if not steps:
        steps = [(1, answer)]
    
    # Sort steps by number
    steps.sort(key=lambda x: x[0])
    
    # Extract sources
    sources = []
    for source in result.get('sources', {}).get('documents', []):
        sources.append({
            'title': source.get('title', 'Unknown protocol'),
            'doc_type': source.get('doc_type', 'protocol'),
            'author': source.get('author', 'Unknown'),
            'year': source.get('year', 'Unknown')
        })
    
    # Format output
    protocol_data = {
        'protocol_name': protocol_query,
        'confidence_score': result.get('confidence_score', 0),
        'steps': [step[1] for step in steps],
        'raw_answer': answer,
        'sources': sources,
        'query_id': result.get('query_id'),
        'model_used': result.get('model_used', 'unknown')
    }
    
    return protocol_data

def generate_protocol_checklist(protocol_data, format='markdown'):
    """Generate a protocol checklist in various formats."""
    if format == 'markdown':
        checklist = f"# {protocol_data['protocol_name']}\n\n"
        
        checklist += "## Protocol Steps\n\n"
        for i, step in enumerate(protocol_data['steps'], 1):
            checklist += f"- [ ] Step {i}: {step}\n"
        
        checklist += "\n## Sources\n\n"
        for source in protocol_data['sources']:
            checklist += f"- {source['title']} ({source['author']}, {source['year']})\n"
            
        return checklist
    
    elif format == 'html':
        checklist = f"<h1>{protocol_data['protocol_name']}</h1>\n"
        
        checklist += "<h2>Protocol Steps</h2>\n<ul class='protocol-checklist'>\n"
        for i, step in enumerate(protocol_data['steps'], 1):
            checklist += f"<li><input type='checkbox' id='step-{i}'> <label for='step-{i}'>Step {i}: {step}</label></li>\n"
        checklist += "</ul>\n"
        
        checklist += "<h2>Sources</h2>\n<ul>\n"
        for source in protocol_data['sources']:
            checklist += f"<li>{source['title']} ({source['author']}, {source['year']})</li>\n"
        checklist += "</ul>\n"
            
        return checklist
    
    else:
        raise ValueError(f"Unsupported format: {format}")

# Example usage
protocol_data = extract_protocol_steps("RNA extraction using TRIzol")
if protocol_data:
    markdown_checklist = generate_protocol_checklist(protocol_data)
    print(markdown_checklist)
    
    # Save to file
    with open("rna_extraction_protocol.md", "w") as f:
        f.write(markdown_checklist)
```

## Laboratory Information Management System Integration

### Python LIMS Integration Example

```python
import requests
import json
import os
import time
import hashlib
from datetime import datetime

class RNANavigatorLIMSIntegration:
    """
    Integration between RNA Lab Navigator and Laboratory Information Management Systems (LIMS).
    This class provides functionality to:
    1. Query protocols based on experiment IDs
    2. Sync inventory data
    3. Generate experiment reports with protocol citations
    """
    
    def __init__(self, api_url, lims_api_url, api_key=None, lims_api_key=None):
        self.api_url = api_url
        self.lims_api_url = lims_api_url
        self.api_key = api_key
        self.lims_api_key = lims_api_key
        
        # Set up headers
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
            
        self.lims_headers = {"Content-Type": "application/json"}
        if lims_api_key:
            self.lims_headers["API-Key"] = lims_api_key
    
    def get_protocol_for_experiment(self, experiment_id):
        """Get relevant protocol for an experiment from LIMS and RNA Navigator."""
        # 1. Fetch experiment details from LIMS
        try:
            lims_response = requests.get(
                f"{self.lims_api_url}/experiments/{experiment_id}",
                headers=self.lims_headers
            )
            lims_response.raise_for_status()
            experiment = lims_response.json()
            
            # 2. Extract protocol information from experiment
            protocol_name = experiment.get('protocol_name')
            experiment_type = experiment.get('experiment_type')
            sample_type = experiment.get('sample_type')
            
            if not protocol_name:
                return {"error": "No protocol name found in experiment data"}
            
            # 3. Query RNA Navigator for protocol details
            query = f"What is the protocol for {protocol_name} for {sample_type} samples?"
            
            nav_response = requests.post(
                f"{self.api_url}/query/",
                headers=self.headers,
                json={
                    "query": query,
                    "doc_type": "protocol",
                    "use_hybrid": True
                }
            )
            nav_response.raise_for_status()
            protocol_data = nav_response.json()
            
            # 4. Format response
            return {
                "experiment_id": experiment_id,
                "experiment_type": experiment_type,
                "sample_type": sample_type,
                "protocol_name": protocol_name,
                "protocol_steps": self._extract_steps(protocol_data['answer']),
                "protocol_sources": protocol_data.get('sources', {}).get('documents', []),
                "confidence_score": protocol_data.get('confidence_score', 0)
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def sync_inventory_data(self, force_update=False):
        """Sync inventory data from LIMS to RNA Navigator."""
        try:
            # 1. Get last sync timestamp
            sync_file = "inventory_sync.json"
            last_sync = 0
            
            if os.path.exists(sync_file) and not force_update:
                with open(sync_file, 'r') as f:
                    sync_data = json.load(f)
                    last_sync = sync_data.get('last_sync', 0)
            
            # 2. Fetch updated inventory from LIMS
            lims_response = requests.get(
                f"{self.lims_api_url}/inventory/updated?since={last_sync}",
                headers=self.lims_headers
            )
            lims_response.raise_for_status()
            inventory_items = lims_response.json()
            
            if not inventory_items:
                return {"status": "success", "message": "No inventory updates found"}
            
            # 3. Prepare data for import to RNA Navigator
            reagents = []
            
            for item in inventory_items:
                reagents.append({
                    "name": item['name'],
                    "catalog_number": item.get('catalog_number', ''),
                    "manufacturer": item.get('manufacturer', ''),
                    "location": item.get('location', ''),
                    "quantity": item.get('quantity', 0),
                    "unit": item.get('unit', ''),
                    "expiration_date": item.get('expiration_date', ''),
                    "last_updated": item.get('last_updated', '')
                })
            
            # 4. Upload to RNA Navigator
            csv_content = self._create_reagent_csv(reagents)
            
            # Generate file checksum
            file_hash = hashlib.md5(csv_content.encode()).hexdigest()
            
            files = {
                'file': ('reagent_inventory.csv', csv_content, 'text/csv')
            }
            
            data = {
                'update_type': 'inventory',
                'source': 'lims',
                'checksum': file_hash
            }
            
            # Upload inventory data
            upload_response = requests.post(
                f"{self.api_url}/documents/batch-import/",
                headers={k: v for k, v in self.headers.items() if k != 'Content-Type'},
                data=data,
                files=files
            )
            upload_response.raise_for_status()
            
            # 5. Update sync timestamp
            with open(sync_file, 'w') as f:
                json.dump({
                    'last_sync': int(time.time()),
                    'items_synced': len(reagents)
                }, f)
            
            return {
                "status": "success", 
                "message": f"Synced {len(reagents)} inventory items",
                "details": upload_response.json()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def generate_experiment_report(self, experiment_id):
        """Generate a comprehensive experiment report with protocol references."""
        try:
            # 1. Get experiment details from LIMS
            lims_response = requests.get(
                f"{self.lims_api_url}/experiments/{experiment_id}",
                headers=self.lims_headers
            )
            lims_response.raise_for_status()
            experiment = lims_response.json()
            
            # 2. Get protocol details from RNA Navigator
            protocol_data = self.get_protocol_for_experiment(experiment_id)
            
            # 3. Get relevant literature from RNA Navigator
            lit_response = requests.post(
                f"{self.api_url}/search/advanced/",
                headers=self.headers,
                json={
                    "query": f"{experiment['protocol_name']} {experiment['sample_type']}",
                    "filters": {
                        "doc_type": ["paper"],
                        "year": {"gte": datetime.now().year - 5}  # Last 5 years
                    },
                    "limit": 5
                }
            )
            lit_response.raise_for_status()
            literature = lit_response.json()
            
            # 4. Generate the report
            report = {
                "experiment_id": experiment_id,
                "title": experiment.get('title', f"Experiment {experiment_id}"),
                "researcher": experiment.get('researcher', 'Unknown'),
                "date": experiment.get('date', datetime.now().strftime("%Y-%m-%d")),
                "experiment_type": experiment.get('experiment_type', 'Unknown'),
                "sample_type": experiment.get('sample_type', 'Unknown'),
                "protocol": {
                    "name": experiment.get('protocol_name', 'Unknown'),
                    "steps": protocol_data.get('protocol_steps', []),
                    "sources": protocol_data.get('protocol_sources', []),
                },
                "materials": experiment.get('materials', []),
                "results": experiment.get('results', {}),
                "relevant_literature": [
                    {
                        "title": doc.get('title', 'Unknown'),
                        "author": doc.get('author', 'Unknown'),
                        "year": doc.get('year', 'Unknown'),
                        "relevance_score": doc.get('relevance_score', 0)
                    }
                    for doc in literature.get('results', [])
                ]
            }
            
            # 5. Format report as HTML and Markdown
            html_report = self._format_report_html(report)
            md_report = self._format_report_markdown(report)
            
            return {
                "report_data": report,
                "html_report": html_report,
                "markdown_report": md_report
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_steps(self, protocol_text):
        """Extract numbered steps from protocol text."""
        import re
        
        # Look for numbered steps (1. Step description)
        step_pattern = r'(\d+)[\.\)]\s+(.*?)(?=\s*\d+[\.\)]|$)'
        steps = re.findall(step_pattern, protocol_text, re.DOTALL)
        
        if steps:
            return [step.strip() for _, step in steps]
        
        # If no numbered steps found, split by newlines
        return [line.strip() for line in protocol_text.split('\n') if line.strip()]
    
    def _create_reagent_csv(self, reagents):
        """Create CSV content from reagent list."""
        header = "name,catalog_number,manufacturer,location,quantity,unit,expiration_date,last_updated\n"
        rows = []
        
        for reagent in reagents:
            row = (
                f"{reagent['name']},"
                f"{reagent['catalog_number']},"
                f"{reagent['manufacturer']},"
                f"{reagent['location']},"
                f"{reagent['quantity']},"
                f"{reagent['unit']},"
                f"{reagent['expiration_date']},"
                f"{reagent['last_updated']}"
            )
            rows.append(row)
        
        return header + "\n".join(rows)
    
    def _format_report_html(self, report):
        """Format experiment report as HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Experiment Report: {report['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .meta {{ display: flex; flex-wrap: wrap; gap: 10px; background: #f5f5f5; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
                .meta div {{ flex: 1; min-width: 200px; }}
                .protocol-steps {{ counter-reset: step; }}
                .protocol-steps li {{ list-style-type: none; margin-bottom: 10px; }}
                .protocol-steps li:before {{ counter-increment: step; content: "Step " counter(step) ": "; font-weight: bold; }}
                .sources, .literature {{ background: #f9f9f9; padding: 10px; border-radius: 5px; }}
                .sources li, .literature li {{ margin-bottom: 5px; }}
            </style>
        </head>
        <body>
            <h1>{report['title']}</h1>
            
            <div class="meta">
                <div><strong>Experiment ID:</strong> {report['experiment_id']}</div>
                <div><strong>Researcher:</strong> {report['researcher']}</div>
                <div><strong>Date:</strong> {report['date']}</div>
                <div><strong>Type:</strong> {report['experiment_type']}</div>
                <div><strong>Sample:</strong> {report['sample_type']}</div>
            </div>
            
            <h2>Protocol: {report['protocol']['name']}</h2>
            <ol class="protocol-steps">
        """
        
        for step in report['protocol']['steps']:
            html += f"<li>{step}</li>\n"
        
        html += """
            </ol>
            
            <h3>Protocol Sources</h3>
            <ul class="sources">
        """
        
        for source in report['protocol']['sources']:
            html += f"<li>{source.get('title', 'Unknown')} ({source.get('doc_type', 'protocol')}) by {source.get('author', 'Unknown')}</li>\n"
        
        html += """
            </ul>
            
            <h2>Materials Used</h2>
            <ul>
        """
        
        for material in report['materials']:
            html += f"<li>{material.get('name', 'Unknown')} ({material.get('amount', 'Unknown')} {material.get('unit', '')})</li>\n"
        
        html += """
            </ul>
            
            <h2>Results</h2>
            <p>Summary: {}</p>
        """.format(report['results'].get('summary', 'No results recorded'))
        
        if report['relevant_literature']:
            html += """
                <h2>Relevant Literature</h2>
                <ul class="literature">
            """
            
            for lit in report['relevant_literature']:
                relevance = int(lit['relevance_score'] * 100) if 'relevance_score' in lit else 'N/A'
                html += f"<li>{lit['title']} - {lit['author']} ({lit['year']}) - Relevance: {relevance}%</li>\n"
            
            html += "</ul>\n"
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _format_report_markdown(self, report):
        """Format experiment report as Markdown."""
        md = f"# {report['title']}\n\n"
        
        md += f"**Experiment ID:** {report['experiment_id']}  \n"
        md += f"**Researcher:** {report['researcher']}  \n"
        md += f"**Date:** {report['date']}  \n"
        md += f"**Type:** {report['experiment_type']}  \n"
        md += f"**Sample:** {report['sample_type']}  \n\n"
        
        md += f"## Protocol: {report['protocol']['name']}\n\n"
        
        for i, step in enumerate(report['protocol']['steps'], 1):
            md += f"{i}. {step}\n"
        
        md += "\n### Protocol Sources\n\n"
        
        for source in report['protocol']['sources']:
            md += f"- {source.get('title', 'Unknown')} ({source.get('doc_type', 'protocol')}) by {source.get('author', 'Unknown')}\n"
        
        md += "\n## Materials Used\n\n"
        
        for material in report['materials']:
            md += f"- {material.get('name', 'Unknown')} ({material.get('amount', 'Unknown')} {material.get('unit', '')})\n"
        
        md += "\n## Results\n\n"
        md += f"Summary: {report['results'].get('summary', 'No results recorded')}\n"
        
        if report['relevant_literature']:
            md += "\n## Relevant Literature\n\n"
            
            for lit in report['relevant_literature']:
                relevance = int(lit['relevance_score'] * 100) if 'relevance_score' in lit else 'N/A'
                md += f"- {lit['title']} - {lit['author']} ({lit['year']}) - Relevance: {relevance}%\n"
        
        return md

# Example usage
if __name__ == "__main__":
    rna_lims = RNANavigatorLIMSIntegration(
        api_url="http://localhost:8000/api",
        lims_api_url="https://lims.your-lab.com/api",
        api_key="your-rna-navigator-api-key",
        lims_api_key="your-lims-api-key"
    )
    
    # Get protocol for an experiment
    protocol = rna_lims.get_protocol_for_experiment("EXP-20250601-001")
    print(json.dumps(protocol, indent=2))
    
    # Sync inventory data
    sync_result = rna_lims.sync_inventory_data()
    print(json.dumps(sync_result, indent=2))
    
    # Generate experiment report
    report = rna_lims.generate_experiment_report("EXP-20250601-001")
    
    # Save report files
    with open("experiment_report.html", "w") as f:
        f.write(report["html_report"])
    
    with open("experiment_report.md", "w") as f:
        f.write(report["markdown_report"])
```

## Instrument Integration

### R Script for Data Analysis with RNA Navigator

```r
# RNA Lab Navigator Integration for R Analysis
# This script demonstrates integrating RNA Lab Navigator with R data analysis

library(httr)
library(jsonlite)
library(ggplot2)
library(dplyr)

# Configuration
rna_nav_url <- "http://localhost:8000/api"
token <- "your-api-token-here"  # Optional

#' Query RNA Lab Navigator API
#'
#' @param endpoint API endpoint (without leading slash)
#' @param method HTTP method ('GET', 'POST', etc.)
#' @param data Request payload for POST/PUT requests
#' @return Parsed JSON response
query_rna_navigator <- function(endpoint, method = "GET", data = NULL) {
  url <- paste0(rna_nav_url, "/", endpoint)
  
  headers <- c(
    "Content-Type" = "application/json"
  )
  
  if (!is.null(token) && token != "") {
    headers <- c(headers, "Authorization" = paste("Bearer", token))
  }
  
  if (method == "GET") {
    response <- GET(url, add_headers(.headers = headers))
  } else if (method == "POST") {
    response <- POST(url, add_headers(.headers = headers), body = data, encode = "json")
  } else {
    stop(paste("Unsupported HTTP method:", method))
  }
  
  if (http_status(response)$category != "Success") {
    stop(paste("API request failed:", http_status(response)$message))
  }
  
  parsed <- content(response, "parsed")
  return(parsed)
}

#' Get protocol details from RNA Lab Navigator
#'
#' @param protocol_name Name of the protocol to search for
#' @return List containing protocol information
get_protocol_details <- function(protocol_name) {
  data <- list(
    query = paste("What is the protocol for", protocol_name, "?"),
    doc_type = "protocol",
    use_hybrid = TRUE
  )
  
  result <- query_rna_navigator("query", "POST", data)
  
  # Extract steps using regex
  steps_text <- result$answer
  steps <- extract_protocol_steps(steps_text)
  
  # Format response
  protocol <- list(
    name = protocol_name,
    steps = steps,
    sources = result$sources$documents,
    confidence_score = result$confidence_score,
    query_id = result$query_id
  )
  
  return(protocol)
}

#' Extract protocol steps from text
#'
#' @param text Protocol text to parse
#' @return Character vector of protocol steps
extract_protocol_steps <- function(text) {
  # Try to match numbered steps (1. Step description)
  step_pattern <- "\\d+\\.\\s+(.*?)(?=\\s*\\d+\\.|$)"
  steps <- regmatches(text, gregexpr(step_pattern, text, perl = TRUE))
  
  if (length(steps[[1]]) > 0) {
    # Clean up the steps
    steps <- gsub("^\\d+\\.\\s+", "", steps[[1]])
    return(steps)
  }
  
  # If no numbered steps found, split by newlines
  steps <- strsplit(text, "\n")[[1]]
  steps <- trimws(steps)
  steps <- steps[steps != ""]
  
  return(steps)
}

#' Search for related papers in RNA Lab Navigator
#'
#' @param query Search query
#' @param min_year Minimum publication year
#' @param max_results Maximum number of results to return
#' @return Data frame of papers
search_related_papers <- function(query, min_year = NULL, max_results = 5) {
  filters <- list(
    doc_type = list("paper")
  )
  
  if (!is.null(min_year)) {
    filters$year <- list(gte = min_year)
  }
  
  data <- list(
    query = query,
    filters = filters,
    limit = max_results,
    use_hybrid = TRUE
  )
  
  result <- query_rna_navigator("search/advanced", "POST", data)
  
  if (length(result$results) == 0) {
    return(data.frame())
  }
  
  # Convert to data frame
  papers <- lapply(result$results, function(paper) {
    list(
      title = paper$title,
      author = paper$author,
      year = paper$year,
      doc_type = paper$doc_type,
      relevance_score = paper$relevance_score
    )
  })
  
  papers_df <- do.call(rbind, lapply(papers, as.data.frame))
  return(papers_df)
}

#' Generate protocol citations for R Markdown/paper
#'
#' @param protocol Protocol details from get_protocol_details()
#' @param format Citation format ('apa', 'mla', or 'chicago')
#' @return Character vector of formatted citations
generate_protocol_citations <- function(protocol, format = "apa") {
  if (length(protocol$sources) == 0) {
    return(character(0))
  }
  
  citations <- lapply(protocol$sources, function(source) {
    title <- source$title
    author <- source$author
    year <- source$year
    doc_type <- source$doc_type
    
    if (format == "apa") {
      if (!is.null(author) && author != "") {
        citation <- paste0(author, " (", year, "). ", title, ". ", toupper(substr(doc_type, 1, 1)), tolower(substr(doc_type, 2, nchar(doc_type))), ".")
      } else {
        citation <- paste0(title, " (", year, "). ", toupper(substr(doc_type, 1, 1)), tolower(substr(doc_type, 2, nchar(doc_type))), ".")
      }
    } else if (format == "mla") {
      if (!is.null(author) && author != "") {
        citation <- paste0(author, ". \"", title, ".\" ", toupper(substr(doc_type, 1, 1)), tolower(substr(doc_type, 2, nchar(doc_type))), ", ", year, ".")
      } else {
        citation <- paste0("\"", title, ".\" ", toupper(substr(doc_type, 1, 1)), tolower(substr(doc_type, 2, nchar(doc_type))), ", ", year, ".")
      }
    } else if (format == "chicago") {
      if (!is.null(author) && author != "") {
        citation <- paste0(author, ". ", year, ". \"", title, ".\" ", toupper(substr(doc_type, 1, 1)), tolower(substr(doc_type, 2, nchar(doc_type))), ".")
      } else {
        citation <- paste0(title, ". ", year, ". ", toupper(substr(doc_type, 1, 1)), tolower(substr(doc_type, 2, nchar(doc_type))), ".")
      }
    } else {
      stop("Unsupported citation format")
    }
    
    return(citation)
  })
  
  return(unlist(citations))
}

# Example: Integrate RNA-Seq analysis with protocol documentation
# This demonstrates analyzing RNA-Seq data and documenting methodology
# with protocol details from RNA Lab Navigator

# 1. Get RNA extraction protocol
rna_extraction <- get_protocol_details("RNA extraction using TRIzol for RNA-Seq")
print(paste("Protocol confidence score:", rna_extraction$confidence_score))

# 2. Search for related RNA-Seq analysis papers
papers <- search_related_papers("RNA-Seq analysis methods differential expression", min_year = 2020)

# 3. Generate citations
citations <- generate_protocol_citations(rna_extraction, format = "apa")
cat("Protocol Citations:\n")
cat(paste("- ", citations), sep = "\n")

# 4. Generate example RNA-Seq analysis data (normally you'd load real data)
set.seed(42)
gene_counts <- data.frame(
  gene_id = paste0("GENE", 1:1000),
  control_1 = rpois(1000, lambda = 100),
  control_2 = rpois(1000, lambda = 100),
  control_3 = rpois(1000, lambda = 100),
  treatment_1 = rpois(1000, lambda = 100) * rbinom(1000, 1, 0.2) * runif(1000, 1.5, 5),
  treatment_2 = rpois(1000, lambda = 100) * rbinom(1000, 1, 0.2) * runif(1000, 1.5, 5),
  treatment_3 = rpois(1000, lambda = 100) * rbinom(1000, 1, 0.2) * runif(1000, 1.5, 5)
)

# 5. Calculate average expression and log2 fold change
gene_data <- gene_counts %>%
  mutate(
    control_avg = (control_1 + control_2 + control_3) / 3,
    treatment_avg = (treatment_1 + treatment_2 + treatment_3) / 3,
    log2fc = log2((treatment_avg + 1) / (control_avg + 1)),
    significant = abs(log2fc) > 1.5
  )

# 6. Plot results
p <- ggplot(gene_data, aes(x = log2(control_avg + 1), y = log2(treatment_avg + 1), color = significant)) +
  geom_point(alpha = 0.5) +
  scale_color_manual(values = c("black", "red")) +
  labs(
    title = "RNA-Seq Differential Expression Analysis",
    subtitle = paste("Based on protocol:", rna_extraction$name),
    x = "log2(Mean Control Counts)",
    y = "log2(Mean Treatment Counts)",
    color = "Significant"
  ) +
  theme_minimal()

# Save the plot
ggsave("rna_seq_analysis.pdf", p, width = 8, height = 6)

# 7. Save methodology documentation
methodology <- paste0(
  "# RNA-Seq Analysis Methodology\n\n",
  "## RNA Extraction Protocol\n\n",
  paste(seq_along(rna_extraction$steps), rna_extraction$steps, sep = ". ", collapse = "\n"),
  "\n\n## Data Analysis\n\n",
  "1. Raw reads were quality-checked using FastQC\n",
  "2. Reads were aligned to the reference genome using STAR aligner\n",
  "3. Gene counts were quantified using featureCounts\n",
  "4. Differential expression analysis was performed in R\n",
  "5. Genes with absolute log2 fold change > 1.5 were considered significant\n\n",
  "## References\n\n",
  paste("- ", citations, collapse = "\n")
)

write(methodology, file = "rna_seq_methodology.md")

cat("Analysis complete. Results saved to rna_seq_analysis.pdf and methodology to rna_seq_methodology.md\n")
```

## External Tool Integration

### Node.js Electron App Integration

```javascript
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const axios = require('axios');
const fs = require('fs');
const { spawn } = require('child_process');

// RNA Lab Navigator API configuration
const RNA_NAV_API = 'http://localhost:8000/api';
let API_TOKEN = null;

// Create the main window
function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile('index.html');
  
  // Load saved token if exists
  try {
    const config = JSON.parse(fs.readFileSync(path.join(app.getPath('userData'), 'config.json')));
    API_TOKEN = config.token;
  } catch (error) {
    console.log('No saved token found');
  }
}

app.whenReady().then(() => {
  createWindow();
  
  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// IPC Handlers for RNA Lab Navigator API interactions

// Authentication
ipcMain.handle('login', async (event, { username, password }) => {
  try {
    const response = await axios.post(`${RNA_NAV_API}/auth/token/`, {
      username,
      password
    });
    
    API_TOKEN = response.data.access;
    
    // Save token
    fs.writeFileSync(
      path.join(app.getPath('userData'), 'config.json'),
      JSON.stringify({ token: API_TOKEN })
    );
    
    return { success: true };
  } catch (error) {
    return { 
      success: false, 
      error: error.response?.data?.detail || 'Authentication failed'
    };
  }
});

// Query API
ipcMain.handle('query', async (event, { question, docType }) => {
  try {
    const headers = API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {};
    
    const response = await axios.post(
      `${RNA_NAV_API}/query/`,
      {
        query: question,
        doc_type: docType || '',
        use_hybrid: true
      },
      { headers }
    );
    
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || 'Query failed'
    };
  }
});

// Protocol export
ipcMain.handle('export-protocol', async (event, { protocol, format }) => {
  try {
    // Extract steps from protocol answer
    const steps = extractProtocolSteps(protocol.answer);
    
    let content = '';
    const fileName = `protocol_${Date.now()}`;
    
    if (format === 'pdf') {
      // Create markdown first
      content = formatProtocolMarkdown(protocol.query, steps, protocol.sources.documents);
      const mdPath = path.join(app.getPath('temp'), `${fileName}.md`);
      fs.writeFileSync(mdPath, content);
      
      // Convert to PDF using pandoc (must be installed)
      const pdfPath = path.join(app.getPath('documents'), `${fileName}.pdf`);
      
      return new Promise((resolve, reject) => {
        const pandoc = spawn('pandoc', [
          mdPath,
          '-o', pdfPath,
          '--pdf-engine=xelatex',
          '-V', 'geometry:margin=1in'
        ]);
        
        pandoc.on('close', (code) => {
          if (code === 0) {
            resolve({
              success: true,
              path: pdfPath
            });
          } else {
            reject({
              success: false,
              error: `PDF conversion failed with code ${code}`
            });
          }
        });
      });
    } else if (format === 'markdown') {
      content = formatProtocolMarkdown(protocol.query, steps, protocol.sources.documents);
      const mdPath = path.join(app.getPath('documents'), `${fileName}.md`);
      fs.writeFileSync(mdPath, content);
      
      return {
        success: true,
        path: mdPath
      };
    } else if (format === 'html') {
      content = formatProtocolHtml(protocol.query, steps, protocol.sources.documents);
      const htmlPath = path.join(app.getPath('documents'), `${fileName}.html`);
      fs.writeFileSync(htmlPath, content);
      
      return {
        success: true,
        path: htmlPath
      };
    } else {
      throw new Error(`Unsupported format: ${format}`);
    }
  } catch (error) {
    return {
      success: false,
      error: error.message || 'Export failed'
    };
  }
});

// Document upload
ipcMain.handle('upload-document', async (event, { filePath, metadata }) => {
  try {
    const headers = API_TOKEN ? { 
      Authorization: `Bearer ${API_TOKEN}`,
      'Content-Type': 'multipart/form-data'
    } : {
      'Content-Type': 'multipart/form-data'
    };
    
    const formData = new FormData();
    formData.append('file', fs.createReadStream(filePath));
    
    for (const [key, value] of Object.entries(metadata)) {
      formData.append(key, value);
    }
    
    const response = await axios.post(
      `${RNA_NAV_API}/documents/upload/`,
      formData,
      { headers }
    );
    
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || 'Upload failed'
    };
  }
});

// Helper functions

function extractProtocolSteps(text) {
  // Try to find numbered steps (1. Step description)
  const stepPattern = /(\d+)[\.\)]\s+(.*?)(?=\s*\d+[\.\)]|$)/g;
  const matches = [...text.matchAll(stepPattern)];
  
  if (matches.length > 0) {
    return matches.map(match => match[2].trim());
  }
  
  // If no numbered steps found, split by newlines
  return text.split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0);
}

function formatProtocolMarkdown(title, steps, sources) {
  let md = `# ${title}\n\n`;
  
  md += `## Protocol Steps\n\n`;
  
  steps.forEach((step, index) => {
    md += `${index + 1}. ${step}\n`;
  });
  
  md += `\n## Sources\n\n`;
  
  sources.forEach(source => {
    md += `- ${source.title} (${source.doc_type})`;
    if (source.author) md += ` by ${source.author}`;
    if (source.year) md += ` (${source.year})`;
    md += `\n`;
  });
  
  md += `\n---\n\nGenerated from RNA Lab Navigator on ${new Date().toLocaleDateString()}`;
  
  return md;
}

function formatProtocolHtml(title, steps, sources) {
  let html = `
  <!DOCTYPE html>
  <html>
  <head>
    <title>${title}</title>
    <style>
      body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
      h1, h2 { color: #333; }
      .protocol-steps { counter-reset: step; }
      .protocol-steps li { list-style-type: none; margin-bottom: 10px; }
      .protocol-steps li:before { counter-increment: step; content: "Step " counter(step) ": "; font-weight: bold; }
      .sources { background: #f9f9f9; padding: 10px; border-radius: 5px; }
      .sources li { margin-bottom: 5px; }
      .footer { margin-top: 30px; font-size: 0.8em; color: #666; border-top: 1px solid #eee; padding-top: 10px; }
    </style>
  </head>
  <body>
    <h1>${title}</h1>
    
    <h2>Protocol Steps</h2>
    <ol class="protocol-steps">
  `;
  
  steps.forEach(step => {
    html += `<li>${step}</li>\n`;
  });
  
  html += `
    </ol>
    
    <h2>Sources</h2>
    <ul class="sources">
  `;
  
  sources.forEach(source => {
    html += `<li>${source.title} (${source.doc_type})`;
    if (source.author) html += ` by ${source.author}`;
    if (source.year) html += ` (${source.year})`;
    html += `</li>\n`;
  });
  
  html += `
    </ul>
    
    <div class="footer">
      Generated from RNA Lab Navigator on ${new Date().toLocaleDateString()}
    </div>
  </body>
  </html>
  `;
  
  return html;
}
```