# Architecture Overview

This document provides a detailed overview of the RNA Lab Navigator's architecture, explaining how the various components interact and why specific design decisions were made.

## System Architecture

RNA Lab Navigator follows a modern microservices-inspired architecture while maintaining reasonable simplicity for maintainability. The system comprises several key components:

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Client Layer                               │
│                                                                     │
│  ┌─────────────┐   ┌───────────────┐   ┌────────────────────────┐   │
│  │ Web Browser │   │ Mobile Browser │   │ Potential Future API  │   │
│  │             │   │               │   │ Clients               │   │
│  └─────────────┘   └───────────────┘   └────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Presentation Layer                             │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                React + Vite + Tailwind CSS                  │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │    │
│  │  │ Chat        │  │ Document    │  │ Admin               │  │    │
│  │  │ Interface   │  │ Viewer      │  │ Dashboard           │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           API Layer                                  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                Django REST Framework                         │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │    │
│  │  │ Query API   │  │ Search API  │  │ Admin API   │          │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │    │
│  │  │ Feedback    │  │ Document    │  │ Security    │          │    │
│  │  │ API         │  │ API         │  │ API         │          │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │    │
│  └─────────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Service Layer                                 │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ RAG         │  │ Search      │  │ Document    │  │ Security    │ │
│  │ Pipeline    │  │ Service     │  │ Service     │  │ Service     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Ingestion   │  │ Analytics   │  │ LLM         │  │ Backup      │ │
│  │ Service     │  │ Service     │  │ Service     │  │ Service     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                              │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ PostgreSQL  │  │ Redis       │  │ Weaviate    │  │ Celery      │ │
│  │ Database    │  │ Cache       │  │ Vector DB   │  │ Tasks       │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                                     │
│  ┌─────────────────────┐  ┌─────────────────────────────────────┐   │
│  │ S3/Local Storage    │  │ External APIs (OpenAI, Ollama)      │   │
│  │                     │  │                                     │   │
│  └─────────────────────┘  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Presentation Layer (Frontend)

**Technology Stack**: React 18, Vite, Tailwind CSS

**Key Components**:
- **ChatBox**: Main interface for user queries and answers
- **AnswerCard**: Displays formatted answers with citations
- **FilterChips**: Enables document type filtering
- **ProtocolUploader**: Interface for adding new protocols
- **SearchQualityDashboard**: Monitors search performance
- **SecurityDashboard**: Monitors security metrics
- **AdminPanel**: Administration interface

**Design Decisions**:
- **React**: Chosen for component reusability and state management
- **Vite**: Selected for fast development experience
- **Tailwind CSS**: Used for rapid UI development with consistent styling
- **Component Structure**: Modular components that can be reused and independently tested

### 2. API Layer

**Technology Stack**: Django 4, Django REST Framework

**Key Endpoints**:
- **/api/query/**: Main RAG endpoint for answering questions
- **/api/search/**: Advanced search functionality
- **/api/feedback/**: User feedback collection
- **/api/documents/**: Document management
- **/api/security/**: Security monitoring and management
- **/api/analytics/**: Performance and usage metrics

**Design Decisions**:
- **Django REST Framework**: Chosen for its robust validation, serialization, and authentication
- **API Versioning**: Implemented to support backward compatibility
- **Authentication**: JWT-based for stateless authentication
- **Rate Limiting**: Implemented to prevent abuse

### 3. Service Layer

#### RAG Pipeline

**Key Components**:
- **Query Processing**: Parses and enhances user queries
- **Vector Search**: Finds relevant documents via embeddings
- **Cross-Encoder Reranking**: Improves search precision
- **Prompt Construction**: Formats context for the LLM
- **Answer Generation**: Interfaces with LLM APIs
- **Citation Processing**: Ensures proper source attribution

**Design Decisions**:
- **Hybrid Search**: Combines vector search with keyword matching for better recall
- **Reranking**: Improves precision after initial retrieval
- **Confidence Scoring**: Implemented to filter low-quality answers
- **Golden Rules**: Strictly enforces citation and confidence requirements

#### Document Ingestion

**Key Components**:
- **Document Parsing**: Extracts text and metadata from various formats
- **Chunking**: Splits documents into optimal-sized chunks
- **Embedding Generation**: Creates vector representations
- **Storage Management**: Handles both vector and relational data

**Design Decisions**:
- **Chunk Size**: 400±50 words with 100-word overlap based on experiments
- **Special Handling**: Thesis documents chunked by chapter
- **Metadata Extraction**: Automated with manual correction capability
- **Image Processing**: Special handling for figures and diagrams

#### LLM Service

**Key Components**:
- **Model Selection**: Chooses appropriate model based on query
- **Network Isolation**: Supports various isolation levels
- **Response Processing**: Formats and validates LLM outputs
- **Cost Management**: Optimizes API usage

**Design Decisions**:
- **Tiered Models**: Uses different models based on query complexity
- **Offline Mode**: Supports local models for air-gapped environments
- **Golden Rules**: Enforces specific prompting patterns
- **Streaming**: Supports streaming responses for better UX

### 4. Infrastructure Layer

**Key Components**:
- **PostgreSQL**: Relational database for structured data
- **Weaviate**: Vector database for semantic search
- **Redis**: Caching and message broker
- **Celery**: Asynchronous task processing
- **Storage**: Document and media storage (local or S3)
- **External APIs**: Integration with OpenAI and other services

**Design Decisions**:
- **Containerization**: Docker for consistent environments
- **Separation of Concerns**: Each service in its own container
- **Scalability**: Services can be scaled independently
- **Persistence**: Proper volume mapping for data durability

## Data Flow

### Query Flow

1. User submits a query through the frontend
2. Request is validated and processed by the Query API
3. RAG Pipeline retrieves relevant documents from Weaviate
4. Cross-encoder reranks the results for relevance
5. Top results are formatted into a prompt
6. LLM Service generates an answer with citations
7. Response is formatted and returned to the frontend
8. Frontend displays the answer with citation links
9. Query and answer are logged for analytics

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│            │    │            │    │            │    │            │
│  Frontend  │───▶│  Query API │───▶│ Vector     │───▶│ Cross-     │
│            │    │            │    │ Search     │    │ Encoder    │
└────────────┘    └────────────┘    └────────────┘    └────────────┘
      ▲                                                      │
      │                                                      ▼
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│            │    │            │    │            │    │            │
│  Response  │◀───│ Citation   │◀───│ LLM        │◀───│ Prompt     │
│  Handling  │    │ Processing │    │ Generation │    │ Building   │
└────────────┘    └────────────┘    └────────────┘    └────────────┘
```

### Ingestion Flow

1. Document is uploaded through UI or API
2. Document is parsed and text is extracted
3. Text is chunked into manageable pieces
4. Embeddings are generated for each chunk
5. Chunks and metadata are stored in Weaviate
6. Document metadata is stored in PostgreSQL
7. Ingestion status is updated and logged

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│            │    │            │    │            │    │            │
│  Document  │───▶│  Parser    │───▶│ Text       │───▶│ Chunking   │
│  Upload    │    │            │    │ Extraction │    │ Service    │
└────────────┘    └────────────┘    └────────────┘    └────────────┘
                                                             │
                                                             ▼
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│            │    │            │    │            │    │            │
│ PostgreSQL │◀───│ Metadata   │◀───│ Vector     │◀───│ Embedding  │
│ Storage    │    │ Extraction │    │ Storage    │    │ Generation │
└────────────┘    └────────────┘    └────────────┘    └────────────┘
```

## Security Architecture

The RNA Lab Navigator implements multiple security layers:

### Authentication and Authorization

- **JWT Authentication**: Secure, token-based authentication
- **Role-Based Access Control**: Different permissions for users, admins, etc.
- **Session Management**: Secure session handling with proper expiration

### Network Security

- **TLS Encryption**: All communications encrypted in transit
- **mTLS**: Mutual TLS for service-to-service communication
- **Network Isolation**: Configurable isolation for LLM services
- **Web Application Firewall**: Protection against common web attacks

### Data Security

- **Encryption at Rest**: Database and file encryption
- **Data Validation**: Strict input validation to prevent injection
- **Audit Logging**: Comprehensive logging of security events
- **Backup System**: Regular backups with encryption

### Operational Security

- **Security Monitoring**: Real-time monitoring of security events
- **Incident Response**: Automated alerting and response
- **Penetration Testing**: Regular security testing
- **Vulnerability Management**: Process for addressing security issues

## Performance Considerations

The RNA Lab Navigator is designed for performance with these strategies:

### Caching Strategy

- **Query Cache**: Caches frequent queries for fast responses
- **Embedding Cache**: Avoids regenerating embeddings
- **HTTP Caching**: Proper cache headers for static content
- **Redis Caching**: In-memory caching for performance-critical data

### Database Optimization

- **Indexing**: Proper indexes for common query patterns
- **Connection Pooling**: Efficiently manages database connections
- **Query Optimization**: Optimized database queries

### Vector Search Tuning

- **HNSW Parameters**: Tuned for the specific document types
- **Hybrid Search**: Balance between vector and keyword search
- **Dimension Reduction**: Techniques to optimize vector storage

### Asynchronous Processing

- **Celery Tasks**: Handles time-consuming operations asynchronously
- **Task Prioritization**: Ensures critical tasks are processed first
- **Background Processing**: Heavy processing happens in background

## Monitoring and Observability

The system provides comprehensive monitoring:

### Metrics Collection

- **Performance Metrics**: Response times, processing times, etc.
- **Resource Usage**: CPU, memory, disk, and network utilization
- **API Usage**: Endpoint call counts and patterns
- **LLM Metrics**: Token usage, cost, and performance

### Logging Strategy

- **Centralized Logging**: All logs collected centrally
- **Structured Logging**: Consistent JSON format for easy parsing
- **Log Levels**: Appropriate log levels for different environments
- **Correlation IDs**: Tracking requests across services

### Alerting System

- **Threshold Alerts**: Notifications when metrics exceed thresholds
- **Anomaly Detection**: Identification of unusual patterns
- **Error Rate Monitoring**: Alerts on elevated error rates
- **Security Alerts**: Immediate notification of security events

## Extensibility

The RNA Lab Navigator is designed for extensibility:

### Plugin System

The system supports plugins for custom functionality:
- **Document Processors**: Custom handlers for specific document types
- **Search Enhancers**: Custom search algorithms
- **LLM Integrations**: Support for additional LLM providers
- **UI Components**: Custom interface elements

### API Extension

New functionality can be added through the API with:
- **Consistent Patterns**: Following established API conventions
- **Versioning**: API versioning for compatibility
- **Documentation**: Auto-generated API docs
- **Testing**: Comprehensive test coverage

### Integration Points

The system provides these integration points:
- **Webhooks**: For event-driven integration
- **Export APIs**: For data exchange
- **Import APIs**: For bulk data ingestion
- **SSO Integration**: For authentication with existing systems

## Dependencies

Key external dependencies include:

- **OpenAI API**: For embeddings and language generation
- **Weaviate**: For vector search capabilities
- **PostgreSQL**: For relational data storage
- **Redis**: For caching and message brokering
- **Celery**: For asynchronous task processing
- **Sentence-Transformers**: For local embedding and reranking
- **Docker**: For containerization
- **Nginx**: For serving the application

## Design Principles

The RNA Lab Navigator follows these core design principles:

1. **Separation of Concerns**: Each component has a single responsibility
2. **Modularity**: Components can be replaced or upgraded independently
3. **Configurability**: System behavior can be adjusted without code changes
4. **Security by Design**: Security considerations in all aspects
5. **Performance Focus**: Designed for fast response times
6. **User Experience**: Prioritizes ease of use and clarity
7. **Maintainability**: Code and architecture designed for long-term maintenance