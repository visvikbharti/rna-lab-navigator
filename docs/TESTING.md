# Testing Documentation

This document outlines the testing strategy and procedures for the RNA Lab Navigator application.

## 1. Testing Strategy

Our testing approach follows a comprehensive multi-level strategy:

1. **Unit Tests**: Test individual components and functions in isolation
2. **Integration Tests**: Test interactions between components
3. **End-to-End Tests**: Test complete user workflows
4. **Performance Tests**: Test system behavior under load
5. **Security Tests**: Test resilience against security threats

## 2. Test Coverage

| Component | Target Coverage | Current Coverage |
|-----------|----------------|------------------|
| Backend Core | 90% | 85% |
| Frontend Components | 80% | 75% |
| API Controllers | 90% | 85% |
| Model Logic | 85% | 80% |
| Security Features | 95% | 90% |

## 3. Test Environment Setup

### Backend Tests

```bash
# Install test dependencies
cd backend
pip install -r requirements.txt
pip install pytest pytest-django pytest-cov pytest-xdist

# Run the tests
pytest
```

### Frontend Tests

```bash
# Install test dependencies
cd frontend
npm install

# Run the tests
npm test
```

### Environment Variables

Create a `.env.test` file for testing:

```ini
DEBUG=True
SECRET_KEY=test-key-not-for-production
POSTGRES_DB=test_db
WEAVIATE_URL=http://localhost:8080
OPENAI_API_KEY=sk-test-key-for-testing
```

## 4. Test Types and Examples

### Unit Tests

Unit tests focus on testing individual functions and classes in isolation. Examples include:

- Testing text chunking algorithms
- Testing embedding creation functions
- Testing document processing utilities
- Testing model methods

**Example: Testing Chunking Logic**

```python
def test_chunk_text():
    """Test text chunking with overlap."""
    text = "This is a test text. " * 100
    chunks = chunk_text(text)
    assert len(chunks) > 1
    # Ensure chunks have proper size
    for chunk in chunks:
        assert len(chunk.split()) <= 500
```

### Integration Tests

Integration tests focus on testing interactions between components. Examples include:

- Testing the RAG pipeline from query to answer
- Testing the authentication flow
- Testing database and vector store interactions

**Example: Testing RAG Pipeline**

```python
@pytest.mark.django_db
def test_full_rag_pipeline(authenticated_client, mock_openai, mock_weaviate):
    """Test the full RAG pipeline from query to answer."""
    # Make a query request
    response = authenticated_client.post('/api/query/', {
        "question": "What is RNA?",
        "doc_type": "all"
    })
    
    # Verify response
    assert response.status_code == 200
    assert 'answer' in response.data
    assert 'sources' in response.data
```

### End-to-End Tests

End-to-end tests verify complete user workflows. Examples include:

- User authentication and authorization
- Submitting a query and receiving an answer
- Uploading a document and querying it

**Example: Complete Query Flow**

```python
def test_query_answer_flow(page):
    """Test the complete query and answer flow."""
    # Log in
    page.goto("/login")
    page.fill("input[name=username]", "test_user")
    page.fill("input[name=password]", "test_password")
    page.click("button[type=submit]")
    
    # Submit a query
    page.goto("/")
    page.fill("textarea[placeholder*=question]", "What is RNA?")
    page.click("button:has-text('Submit')")
    
    # Verify answer appears
    assert page.wait_for_selector(".answer-card")
    assert page.text_content(".answer-card") != ""
```

### Performance Tests

Performance tests evaluate the system under various load conditions. Examples include:

- Response time under normal load
- Throughput under concurrent users
- Memory usage during extended operation

**Example: Response Time Test**

```python
@pytest.mark.slow
def test_query_response_time(authenticated_client):
    """Test query response time."""
    start_time = time.time()
    response = authenticated_client.post('/api/query/', {
        "question": "What is RNA?",
        "doc_type": "all"
    })
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 5.0  # Response within 5 seconds
```

### Security Tests

Security tests verify that the system is resistant to common security threats. Examples include:

- Authentication and authorization checks
- Input validation and sanitization
- Protection against common web vulnerabilities

**Example: Testing WAF Protection**

```python
def test_waf_protection(authenticated_client, settings):
    """Test WAF protection against malicious requests."""
    settings.WAF_ENABLED = True
    
    # Test SQL injection attempt
    response = authenticated_client.post('/api/query/', {
        "question": "'; DROP TABLE users; --",
        "doc_type": "all"
    })
    
    assert response.status_code == 400  # Bad request, blocked by WAF
```

## 5. Test Automation

### CI Pipeline Testing

Testing is automated in our CI/CD pipeline using GitHub Actions:

1. **Pull Request Checks**:
   - Run unit and integration tests
   - Check code coverage
   - Run security scan
   - Run linting

2. **Nightly Builds**:
   - Run full test suite including performance tests
   - Generate coverage reports
   - Run security analysis

### Testing Schedule

| Test Type | When Run | Duration |
|-----------|----------|----------|
| Unit Tests | Every PR, every push | 1-2 min |
| Integration Tests | Every PR, every push | 2-5 min |
| End-to-End Tests | Daily | 10-15 min |
| Performance Tests | Weekly | 20-30 min |
| Security Tests | Weekly | 15-20 min |

## 6. Test Reports and Monitoring

### Coverage Reports

Coverage reports are generated after each test run:

```bash
# Backend coverage
pytest --cov=. --cov-report=html

# Frontend coverage
npm test -- --coverage
```

Reports are stored in:
- Backend: `backend/htmlcov/`
- Frontend: `frontend/coverage/`

### Test Result Monitoring

Test results are monitored using:
1. GitHub Actions dashboard
2. Codecov for coverage trends
3. Weekly test status reports

## 7. Testing Tools

| Purpose | Tool | Description |
|---------|------|-------------|
| Backend Unit Testing | pytest | Python testing framework |
| Backend Coverage | pytest-cov | Coverage reporting |
| Frontend Testing | Jest, React Testing Library | JavaScript testing framework |
| End-to-End Testing | Playwright | Browser automation |
| Performance Testing | pytest-benchmark | Benchmark tests |
| Security Testing | bandit, OWASP ZAP | Security analysis |
| Mocking | unittest.mock, pytest-mock | Mock dependencies |
| Load Testing | Locust | Simulate multiple users |

## 8. Writing Tests

### Best Practices

1. **Test naming**: Use descriptive names following `test_<function>_<scenario>`
2. **Arrange-Act-Assert**: Structure tests with clear setup, action, and verification
3. **Isolation**: Tests should be independent and not rely on other tests
4. **Fixtures**: Use pytest fixtures for common setup
5. **Coverage**: Aim for high coverage but prioritize critical paths

### Test Structure

```python
# Example of a well-structured test
@pytest.mark.django_db
def test_user_authentication_success(client):
    """Test user can authenticate with valid credentials."""
    # Arrange
    User.objects.create_user(username='testuser', password='testpass')
    
    # Act
    response = client.post('/api/auth/login/', {
        'username': 'testuser',
        'password': 'testpass'
    })
    
    # Assert
    assert response.status_code == 200
    assert 'token' in response.data
```

## 9. Troubleshooting Tests

### Common Issues

1. **Database issues**: Tests leaving residual data
   - Solution: Use `@pytest.mark.django_db` and transaction fixtures

2. **Async issues**: Race conditions in async tests
   - Solution: Use proper wait and synchronization

3. **Environment issues**: Tests failing in CI but not locally
   - Solution: Standardize test environment variables

4. **Flaky tests**: Tests occasionally failing
   - Solution: Identify race conditions, improve determinism

### Debug Techniques

```bash
# Run tests with increased verbosity
pytest -vvs path/to/test_file.py

# Run tests with print output
pytest -s path/to/test_file.py

# Run a specific test
pytest path/to/test_file.py::test_specific_function
```

## 10. Test-Driven Development

For new features, we follow a TDD approach:

1. Write a failing test that defines the expected behavior
2. Implement the minimum code to make the test pass
3. Refactor the code while keeping tests passing
4. Repeat for additional functionality

This process ensures that all new code is testable and meets requirements.

---

For questions about testing, contact the development team at dev@example.com.