# RNA Lab Navigator API Reference

This document provides comprehensive documentation for the RNA Lab Navigator API endpoints, enabling integration with other systems or custom clients.

## Base URL

All API endpoints are accessed through the base URL for your deployment:

```
https://your-deployment-url.com/api/
```

For local development, the base URL is:

```
http://localhost:8000/api/
```

## Authentication

Most endpoints support anonymous access to facilitate easy integration, but this can be configured to require authentication in production. When authentication is required, use the JWT token-based authentication:

```http
GET /api/query/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Authentication tokens can be obtained through the `/api/auth/token/` endpoint.

## Core Endpoints

### Health Check

Verify API availability with a simple health check.

```http
GET /api/health/
```

**Response**:

```json
{
  "status": "ok"
}
```

### Query

The main endpoint for retrieving answers from the RNA Lab Navigator.

```http
POST /api/query/
```

**Parameters**:

| Parameter    | Type    | Required | Description                                      |
|--------------|---------|----------|--------------------------------------------------|
| query        | string  | Yes      | The question to be answered                      |
| doc_type     | string  | No       | Filter results by document type                  |
| use_hybrid   | boolean | No       | Use hybrid search (vector + keyword). Default: true |
| hybrid_alpha | float   | No       | Balance between vector and keyword. Default: 0.75 |
| use_cache    | boolean | No       | Check query cache before generating new answer. Default: true |
| model_tier   | string  | No       | Model tier to use. Options: small, default, large |

**Example Request**:

```json
{
  "query": "What's the protocol for RNA extraction using TRIzol?",
  "doc_type": "protocol",
  "use_hybrid": true,
  "model_tier": "default"
}
```

**Example Response**:

```json
{
  "answer": "The protocol for RNA extraction using TRIzol involves the following steps:\n\n1. Add 1 ml of TRIzol reagent per 50-100 mg of tissue sample or 10^7 cells [1].\n2. Homogenize the sample using a homogenizer or by passing through a needle several times [1].\n3. Incubate at room temperature for 5 minutes to permit complete dissociation of nucleoprotein complexes [2].\n4. Add 0.2 ml of chloroform per 1 ml of TRIzol reagent used, cap the tube securely, and shake vigorously for 15 seconds [1].\n5. Incubate at room temperature for 2-3 minutes [1].\n6. Centrifuge at 12,000 × g for 15 minutes at 4°C [1].\n7. Transfer the aqueous phase (containing RNA) to a fresh tube [1, 2].\n8. Precipitate the RNA by mixing with isopropyl alcohol (0.5 ml per 1 ml of TRIzol) [1].\n9. Incubate at room temperature for 10 minutes, then centrifuge at 12,000 × g for 10 minutes at 4°C [1].\n10. Remove the supernatant and wash the RNA pellet with 75% ethanol [1, 2].\n11. Vortex briefly and centrifuge at 7,500 × g for 5 minutes at 4°C [1].\n12. Air-dry the RNA pellet for 5-10 minutes [2].\n13. Dissolve the RNA in RNase-free water by passing the solution up and down several times through a pipette tip [1, 2].",
  "sources": [
    {
      "title": "Protocol: RNA Extraction",
      "doc_type": "protocol",
      "author": "Lab Manager"
    },
    {
      "title": "Trizol Reagent User Guide",
      "doc_type": "protocol",
      "author": "Manufacturer"
    }
  ],
  "figures": [],
  "confidence_score": 0.89,
  "status": "success",
  "query_id": 1234,
  "model_used": "gpt-4o"
}
```

### Streaming Response

You can request a streaming response by adding the `?stream=true` query parameter:

```http
POST /api/query/?stream=true
```

The response will be a server-sent event (SSE) stream with the following event types:

1. `metadata` - Initial metadata about sources and figures
2. `content` - Content chunks as they're generated
3. `final` - Final event with confidence score and status

### Document Preview

Retrieve a preview of a specific document.

```http
GET /api/documents/{document_id}/preview/
```

**Response**:

```json
{
  "id": 42,
  "title": "Protocol: RNA Extraction",
  "doc_type": "protocol",
  "author": "Lab Manager",
  "content": "...",
  "highlights": [
    {
      "page": 2,
      "text": "Add 1 ml of TRIzol reagent per 50-100 mg of tissue sample",
      "bounding_box": [0.1, 0.2, 0.8, 0.3]
    }
  ]
}
```

## Feedback and History

### Feedback

Submit feedback about query answers.

```http
POST /api/feedback/
```

**Parameters**:

| Parameter         | Type   | Required | Description                           |
|-------------------|--------|----------|---------------------------------------|
| query_id          | int    | Yes      | ID of the query to provide feedback for |
| rating            | string | Yes      | Either "thumbs_up" or "thumbs_down"   |
| comments          | string | No       | Optional user comments                |
| retrieval_quality | int    | No       | Rating from 1-5 for retrieval quality |
| answer_relevance  | int    | No       | Rating from 1-5 for answer relevance  |
| citation_accuracy | int    | No       | Rating from 1-5 for citation accuracy |
| specific_issues   | array  | No       | List of specific issues encountered   |

**Example Request**:

```json
{
  "query_id": 1234,
  "rating": "thumbs_up",
  "comments": "Very helpful and accurate protocol information",
  "retrieval_quality": 5,
  "answer_relevance": 5,
  "citation_accuracy": 4,
  "specific_issues": []
}
```

**Example Response**:

```json
{
  "id": 42,
  "query_id": 1234,
  "rating": "thumbs_up",
  "comments": "Very helpful and accurate protocol information",
  "retrieval_quality": 5,
  "answer_relevance": 5,
  "citation_accuracy": 4,
  "specific_issues": [],
  "created_at": "2025-06-01T14:30:00Z"
}
```

### Feedback Statistics

Retrieve feedback statistics.

```http
GET /api/feedback/stats/
```

**Example Response**:

```json
{
  "total_feedback": 150,
  "positive_feedback": 120,
  "negative_feedback": 30,
  "positive_ratio": 0.8,
  "retrieval_quality_avg": 4.2,
  "answer_relevance_avg": 4.5,
  "citation_accuracy_avg": 4.1,
  "recent_positive": 15,
  "recent_negative": 5
}
```

### Common Issues

Identify common issues based on feedback.

```http
GET /api/feedback/common_issues/
```

**Example Response**:

```json
{
  "common_issues": [
    ["missing_source", 12],
    ["incorrect_citation", 8],
    ["incomplete_answer", 7],
    ["outdated_information", 5],
    ["wrong_protocol", 3]
  ],
  "total_issues": 35
}
```

### Query History

Retrieve historical queries.

```http
GET /api/history/
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| page      | int  | Page number |
| page_size | int  | Items per page |

**Example Response**:

```json
{
  "count": 250,
  "next": "http://example.com/api/history/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1234,
      "query_text": "What's the protocol for RNA extraction using TRIzol?",
      "answer": "...",
      "confidence_score": 0.89,
      "sources": [...],
      "created_at": "2025-06-01T14:00:00Z"
    },
    ...
  ]
}
```

### Query History Statistics

Retrieve statistics about queries.

```http
GET /api/history/stats/
```

**Example Response**:

```json
{
  "total_queries": 250,
  "avg_confidence": 0.78,
  "low_confidence_count": 45,
  "low_confidence_ratio": 0.18,
  "recent_queries": 15
}
```

### Document Type Breakdown

Get breakdown of queries by document type.

```http
GET /api/history/doc_type_breakdown/
```

**Example Response**:

```json
{
  "protocol": 85,
  "paper": 65,
  "thesis": 42,
  "troubleshooting": 58
}
```

## Cache Management

### Cache Statistics

Retrieve cache statistics.

```http
GET /api/cache/
```

**Example Response**:

```json
{
  "total_entries": 120,
  "total_hits": 350,
  "top_entries": [...],
  "least_recently_used": [...]
}
```

### Clear Cache

Clear the entire cache or specific entries.

```http
DELETE /api/cache/
```

To delete a specific cache entry:

```http
DELETE /api/cache/?id=42
```

## Figure Management

### List Figures

Retrieve figures extracted from documents.

```http
GET /api/figures/
```

**Parameters**:

| Parameter   | Type   | Description               |
|-------------|--------|---------------------------|
| document    | int    | Filter by document ID     |
| figure_type | string | Filter by figure type     |
| page_number | int    | Filter by page number     |
| search      | string | Search by caption content |

**Example Response**:

```json
{
  "count": 85,
  "next": "http://example.com/api/figures/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "figure_id": "fig123abc",
      "document": 42,
      "figure_type": "image",
      "page_number": 5,
      "caption": "Figure 1: RNA extraction workflow",
      "image_url": "http://example.com/media/figures/fig123abc.png",
      "created_at": "2025-05-15T10:30:00Z"
    },
    ...
  ]
}
```

### Get Figure by ID

Retrieve a specific figure by ID.

```http
GET /api/figures/{id}/
```

### Figures by Document

Get figures grouped by document.

```http
GET /api/figures/by_document/
```

### Search Figures by Content

Search figures by their caption content using vector search.

```http
GET /api/figures/search_by_content/?query=RNA%20workflow
```

## Evaluation Endpoints

### Trigger Evaluation

Trigger a new evaluation run against a test set.

```http
POST /api/evaluations/trigger/
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| eval_set_id | int | Yes | ID of the evaluation set to run |
| name | string | No | Optional name for this evaluation run |
| description | string | No | Optional description |

### Evaluation Report

Get a report for a specific evaluation run.

```http
GET /api/evaluations/report/{run_id}/
```

## Error Responses

The API uses standard HTTP status codes to indicate the success or failure of requests:

- `200 OK`: The request succeeded
- `400 Bad Request`: The request was invalid or cannot be served
- `401 Unauthorized`: Authentication is required
- `404 Not Found`: The requested resource could not be found
- `500 Internal Server Error`: An error occurred on the server

Error responses include a JSON object with an error message:

```json
{
  "error": "An error occurred while processing your query."
}
```

## Rate Limiting

API requests are subject to rate limiting to ensure fair usage. Current limits are:

- 60 requests per minute per IP address
- 1000 requests per day per authenticated user

When rate limits are exceeded, the API responds with HTTP status code `429 Too Many Requests`.