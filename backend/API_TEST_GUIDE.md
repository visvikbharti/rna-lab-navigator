# RNA Lab Navigator API Testing Guide

## Overview
This guide explains the comprehensive API testing suite for the RNA Lab Navigator backend. The tests focus on scientific accuracy, preventing hallucinations, and ensuring robust error handling.

## Test Scripts

### 1. `test_api_comprehensive.py`
Comprehensive testing of all API endpoints with various scientific queries.

**Tests:**
- RAG Query Endpoint (`/api/query/`)
  - Basic scientific queries (RNA extraction, CRISPR, Western blot)
  - Off-topic queries (should reject)
  - Empty/invalid queries
  - Hallucination prevention
  - Citation verification
  - Confidence scoring

- Hypothesis Exploration (`/api/hypothesis/explore/`)
  - Valid scientific hypotheses
  - Invalid/nonsensical hypotheses
  - Empty inputs
  - Scientific validity checks

- Protocol Generation (`/api/hypothesis/generate-protocol/`)
  - Valid protocol requests
  - Invalid experiment types
  - Empty inputs
  - Output format validation

### 2. `test_api_edge_cases.py`
Edge case and security testing.

**Tests:**
- Malformed Requests
  - Invalid JSON
  - Wrong content types
  - Missing required fields
  - Invalid field types

- Injection Attempts
  - SQL injection
  - Script injection (XSS)
  - Command injection
  - Path traversal

- Boundary Conditions
  - Very long inputs
  - Unicode/special characters
  - Empty vs null values
  - Complex nested data

- Performance
  - Concurrent requests
  - Rate limiting

### 3. `test_hallucination_prevention.py`
Specific tests for preventing AI hallucinations.

**Tests:**
- Hallucination Prevention
  - Fictional scientists/papers
  - Impossible biology
  - False premises
  - Future speculation
  - Mixed valid/invalid content

- Citation Verification
  - Presence of sources
  - Citation format
  - Minimum source requirements

- Confidence Calibration
  - High confidence for basic queries
  - Low confidence for uncertain queries
  - Very low confidence for nonsensical queries

## Running the Tests

### Prerequisites
1. Start the backend server:
   ```bash
   cd backend
   python manage.py runserver
   ```

2. Ensure Celery workers are running:
   ```bash
   celery -A rna_backend worker -l info
   celery -A rna_backend beat -l info
   ```

### Quick Test
Run a quick smoke test to verify server is running:
```bash
python quick_api_test.py
```

### Full Test Suite
Run all tests in sequence:
```bash
./run_all_api_tests.sh
```

Or run individual test scripts:
```bash
python test_api_comprehensive.py
python test_api_edge_cases.py
python test_hallucination_prevention.py
```

## Test Results

Results are saved as JSON files:
- `test_results.json` - Comprehensive test results
- `edge_case_results.json` - Edge case test results
- `hallucination_test_results.json` - Hallucination prevention results

## Key Metrics

The tests verify:
1. **Answer Quality**: Scientifically accurate responses with proper citations
2. **Hallucination Prevention**: Rejects nonsensical/fictional queries
3. **Error Handling**: Graceful handling of malformed requests
4. **Security**: Resistance to injection attacks
5. **Performance**: Handles concurrent requests appropriately

## Success Criteria

Per the project requirements:
- Answer quality (Good + Okay) ≥ 85% on test bank
- Median end-to-end latency ≤ 5s
- Confidence score < 0.45 triggers rejection
- All responses must include citations when answering from sources

## Troubleshooting

If tests fail:
1. Check server is running on http://localhost:8000
2. Verify database migrations are applied
3. Ensure vector database (Weaviate) is running
4. Check OpenAI API key is configured
5. Review server logs for detailed errors

## Adding New Tests

To add new test cases:
1. Add to appropriate test array (e.g., `RAG_QUERY_TESTS`)
2. Include expected behavior (keywords, error conditions)
3. Document the test purpose
4. Run the test suite to verify

## Notes

- Tests use `AllowAny` permission for simplified testing
- Production should use `IsAuthenticated` for sensitive endpoints
- Adjust timeout values based on your system performance
- Some tests may require actual document ingestion to pass fully