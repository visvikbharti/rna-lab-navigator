# Search API

The RNA Lab Navigator provides advanced search capabilities through a dedicated search API. This API allows for more granular control over the search process compared to the standard query endpoint.

## Search Endpoints

### Basic Search

Perform a basic search across all document collections.

```http
GET /api/search/basic/?q=RNA extraction
```

**Parameters**:

| Parameter | Type   | Required | Description                    |
|-----------|--------|----------|--------------------------------|
| q         | string | Yes      | Search query                   |
| limit     | int    | No       | Maximum number of results (default: 10) |
| offset    | int    | No       | Result offset for pagination   |
| doc_type  | string | No       | Filter by document type        |

**Example Response**:

```json
{
  "count": 24,
  "next": "/api/search/basic/?q=RNA%20extraction&offset=10",
  "previous": null,
  "results": [
    {
      "id": "doc123",
      "title": "Protocol: RNA Extraction using TRIzol",
      "doc_type": "protocol",
      "author": "Lab Manager",
      "year": 2024,
      "relevance_score": 0.92,
      "content_preview": "This protocol describes the step-by-step process for extracting RNA using TRIzol reagent...",
      "highlight": ["RNA extraction", "TRIzol reagent"],
      "source_file": "protocol_RNAextraction.pdf"
    },
    ...
  ]
}
```

### Advanced Search

Perform an advanced search with more control over search parameters.

```http
POST /api/search/advanced/
```

**Parameters**:

| Parameter       | Type    | Required | Description                            |
|-----------------|---------|----------|----------------------------------------|
| query           | string  | Yes      | Search query                           |
| limit           | int     | No       | Maximum number of results (default: 10) |
| filters         | object  | No       | Filters to apply to search             |
| use_hybrid      | boolean | No       | Use hybrid search (default: true)      |
| hybrid_alpha    | float   | No       | Weight between vector and BM25 (default: 0.75) |
| reranking       | boolean | No       | Apply reranking to results (default: true) |
| include_figures | boolean | No       | Include figure results (default: false) |

**Example Request**:

```json
{
  "query": "RNA extraction TRIzol",
  "limit": 15,
  "filters": {
    "doc_type": ["protocol", "troubleshooting"],
    "year": {"gte": 2020},
    "author": "Kumar"
  },
  "use_hybrid": true,
  "hybrid_alpha": 0.6,
  "reranking": true,
  "include_figures": true
}
```

**Example Response**:

```json
{
  "count": 8,
  "results": [
    {
      "id": "doc123",
      "title": "Protocol: RNA Extraction using TRIzol",
      "doc_type": "protocol",
      "author": "Kumar",
      "year": 2023,
      "relevance_score": 0.95,
      "rerank_score": 0.89,
      "content_preview": "This protocol describes the step-by-step process for extracting RNA using TRIzol reagent...",
      "highlight": ["RNA extraction", "TRIzol reagent"],
      "source_file": "protocol_RNAextraction.pdf"
    },
    ...
  ],
  "figures": [
    {
      "figure_id": "fig123",
      "doc_title": "Protocol: RNA Extraction using TRIzol",
      "figure_type": "diagram",
      "caption": "Figure 1: Workflow diagram of RNA extraction process using TRIzol",
      "relevance_score": 0.85,
      "image_url": "/api/figures/fig123/",
      "page_number": 3
    },
    ...
  ],
  "search_metadata": {
    "search_time_ms": 120,
    "vector_search_time_ms": 45,
    "bm25_search_time_ms": 25,
    "reranking_time_ms": 50,
    "model_used": "multilingual-e5-large"
  }
}
```

### Semantic Search

Perform a pure semantic (vector) search without keyword matching.

```http
GET /api/search/semantic/?q=RNA extraction process
```

**Parameters**:

| Parameter | Type   | Required | Description                    |
|-----------|--------|----------|--------------------------------|
| q         | string | Yes      | Search query                   |
| limit     | int    | No       | Maximum number of results (default: 10) |
| doc_type  | string | No       | Filter by document type        |

### Keyword Search

Perform a pure keyword (BM25) search without vector matching.

```http
GET /api/search/keyword/?q=TRIzol RNA
```

**Parameters**:

| Parameter | Type   | Required | Description                    |
|-----------|--------|----------|--------------------------------|
| q         | string | Yes      | Search query                   |
| limit     | int    | No       | Maximum number of results (default: 10) |
| doc_type  | string | No       | Filter by document type        |

### Faceted Search

Perform a search with facet counts for filtering.

```http
GET /api/search/facets/?q=RNA
```

**Example Response**:

```json
{
  "count": 45,
  "results": [...],
  "facets": {
    "doc_type": {
      "protocol": 15,
      "paper": 18,
      "thesis": 7,
      "troubleshooting": 5
    },
    "year": {
      "2024": 12,
      "2023": 18,
      "2022": 10,
      "2021": 5
    },
    "author": {
      "Kumar": 10,
      "Sharma": 8,
      "Phutela": 6,
      "Agarwal": 5,
      "Others": 16
    }
  }
}
```

## Search Autocomplete

Get search query suggestions based on partial input.

```http
GET /api/search/autocomplete/?q=RNA ex
```

**Example Response**:

```json
{
  "suggestions": [
    "RNA extraction",
    "RNA extraction TRIzol",
    "RNA extraction protocol",
    "RNA expression analysis",
    "RNA experimental design"
  ]
}
```

## Search Relevance Feedback

Submit feedback about search result relevance to improve future searches.

```http
POST /api/search/feedback/
```

**Parameters**:

| Parameter     | Type   | Required | Description                 |
|---------------|--------|----------|-----------------------------|
| query         | string | Yes      | Original search query       |
| document_id   | string | Yes      | ID of the document rated    |
| relevance     | int    | Yes      | Rating from 0-2 (0: not relevant, 1: somewhat relevant, 2: very relevant) |
| comments      | string | No       | Optional user comments      |

**Example Request**:

```json
{
  "query": "RNA extraction TRIzol",
  "document_id": "doc123",
  "relevance": 2,
  "comments": "This document was exactly what I was looking for"
}
```

## Tips for Effective Searching

### Query Syntax

The search API supports several special query syntax features:

- **Phrase matching**: Use quotes for exact phrase matching: `"RNA extraction protocol"`
- **Field-specific search**: Target specific fields: `title:"RNA extraction" AND author:Kumar`
- **Boolean operators**: Combine terms with AND, OR, NOT: `RNA AND (extraction OR isolation) NOT protein`
- **Grouping**: Use parentheses to group expressions: `(RNA OR DNA) AND extraction`
- **Wildcards**: Use `*` for wildcards: `RNA extrac*` (matches extraction, extracting, etc.)

### Filtering

When using advanced search, you can apply filters to narrow down results:

- **Exact match**: `{"author": "Kumar"}`
- **Multiple values**: `{"doc_type": ["protocol", "troubleshooting"]}`
- **Numeric ranges**: `{"year": {"gte": 2020, "lte": 2024}}`
- **Date ranges**: `{"created_at": {"gte": "2024-01-01", "lte": "2024-06-30"}}`

### Optimizing Search Performance

For best search performance:

1. Be specific in your queries
2. Use field-specific search when possible
3. For exploratory searches, start with faceted search
4. For known-item searches, use advanced search with specific filters
5. Adjust the hybrid_alpha parameter based on your query type:
   - For conceptual queries (e.g., "how does RNA splicing work"), use lower alpha (0.3-0.5)
   - For specific terms or names (e.g., "TRIzol protocol"), use higher alpha (0.7-0.9)