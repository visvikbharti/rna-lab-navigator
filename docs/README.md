# RNA Lab Navigator Documentation

Welcome to the comprehensive documentation for the RNA Lab Navigator project. This repository contains all the information needed to use, deploy, customize, and extend the system.

## Table of Contents

### User Documentation
- [User Guide](user_guide/index.md) - Complete guide for end users
  - [Getting Started](user_guide/getting_started.md) - Quick introduction to using the system
  - [Advanced Features](user_guide/advanced_features.md) - Advanced usage scenarios
  - [Administrator Guide](user_guide/administrator_guide.md) - System administration

### API Documentation
- [API Reference](api_reference/index.md) - Complete API documentation
  - [Search API](api_reference/search_api.md) - Detailed search API documentation

### Developer Documentation
- [Developer Guide](developer_guide/index.md) - Complete developer documentation
  - [Architecture Overview](developer_guide/architecture.md) - System architecture and design
  - [Contributing Guidelines](developer_guide/contributing.md) - How to contribute to the project

### Deployment & Configuration
- [Deployment Guide](deployment_guide.md) - How to deploy the system
- [Configuration Reference](configuration_reference.md) - Detailed configuration options

### Integration Guides
- [Integration Examples](integration_examples.md) - Examples of integrating with other systems

## Project Overview

RNA Lab Navigator is a private, retrieval-augmented assistant for Dr. Debojyoti Chakraborty's 21-member RNA-biology lab at CSIR-IGIB. The system can answer protocol, thesis, and paper questions with citations in under 5 seconds, helping preserve institutional memory and accelerate experiments.

### Key Features

- **Fast Answers**: Get responses to lab-specific questions in under 5 seconds
- **Source Citations**: Every answer includes references to the source documents
- **Document Preview**: View the relevant sections of referenced documents directly in the interface
- **Comprehensive Coverage**: Search across protocols, theses, papers, and troubleshooting guides
- **Feedback Mechanism**: Rate answers to continuously improve system accuracy
- **Security**: Role-based access control and robust security measures protect sensitive data

### Technology Stack

- **Frontend**: React 18 + Vite + Tailwind CSS
- **Backend**: Django 4 + DRF + Celery
- **Vector Database**: Weaviate (HNSW + BM25 hybrid search)
- **Language Models**: OpenAI GPT-4o for answers, Ada-002 for embeddings
- **Infrastructure**: Docker (PostgreSQL, Redis, Weaviate), deployed on Railway + Vercel

## Quick Start

For a quick start with the system, refer to:

1. [Getting Started Guide](user_guide/getting_started.md) for end users
2. [Deployment Guide](deployment_guide.md) for system administrators
3. [Developer Guide](developer_guide/index.md) for developers

## Contributing

We welcome contributions to the RNA Lab Navigator project. Please read our [Contributing Guidelines](developer_guide/contributing.md) for details on how to submit contributions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For technical assistance, please contact the lab administrator or refer to the contacts listed in the system's footer.