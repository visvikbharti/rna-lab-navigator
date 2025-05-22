# Changelog

All notable changes to RNA Lab Navigator will be documented in this file.

## [Unreleased]

### Added
- Advanced architecture enhancement plan document
- Detailed implementation roadmap for post-MVP features
- Enhanced documentation in developer design dossier
- Hybrid search capability with vector+BM25 using Weaviate
- Streaming response support with Server-Sent Events (SSE)
- Embedding caching system using Redis
- User feedback system with thumbs up/down and detailed feedback
- Query response caching for frequently asked questions
- Tiered model selection based on query complexity
- Analytics endpoints for monitoring system performance
- Automated evaluation system with reference questions
- Weekly evaluation runs with regression detection
- Email alerts for performance degradation
- Test evaluation set with sample RNA biology questions

### Changed
- Updated documentation to include advanced architecture recommendations
- Refactored search functionality to support hybrid retrieval
- Enhanced frontend to support real-time streaming of responses
- Improved embedding generation with SHA-256 based caching
- Extended frontend components with feedback UI
- Added model information display in the UI

## [0.1.0] - 2025-05-18

### Added
- Initial project setup
- Django backend with DRF API
- React frontend with Tailwind CSS
- Vector search integration with Weaviate
- Cross-encoder reranking
- OpenAI GPT-4o integration
- PDF ingestion for theses with chapter splitting
- Celery task for bioRxiv preprint fetching
- Docker-compose configuration for local development
- Documentation (README, entry guide, design dossier)

### Technical Details
- Chunking strategy: 400±50 words with 100-word overlap
- Cross-encoder model: `ms-marco-MiniLM-L-6-v2`
- Embedding model: OpenAI `text-embedding-ada-002`
- Confidence threshold: 0.45