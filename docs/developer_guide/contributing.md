# Contributing Guide

Thank you for your interest in contributing to the RNA Lab Navigator project! This guide will help you understand how to contribute effectively to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Documentation Guidelines](#documentation-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [Issue Reporting](#issue-reporting)
9. [Security Vulnerability Reporting](#security-vulnerability-reporting)
10. [Project Governance](#project-governance)

## Code of Conduct

The RNA Lab Navigator project is committed to fostering an inclusive and welcoming environment. All contributors are expected to adhere to our Code of Conduct:

- Be respectful and considerate in all communications
- Value diverse perspectives and experiences
- Focus on the technical merits of contributions
- Provide constructive feedback
- Prioritize the lab's research needs

## Getting Started

Before contributing, please:

1. **Set up your development environment** following the instructions in the [Developer Guide](index.md#development-environment-setup)
2. **Familiarize yourself with the codebase** and architecture
3. **Check existing issues** to find tasks that need attention
4. **Join the development chat** to discuss your ideas with the team

### First-Time Contributors

If you're new to the project, consider starting with issues labeled `good-first-issue`. These are specifically selected to be accessible to newcomers.

## Development Workflow

We follow a standard GitHub flow:

1. **Fork the repository** to your GitHub account
2. **Clone your fork** to your local machine
3. **Create a feature branch** from `master` with a descriptive name
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** with appropriate tests and documentation
5. **Commit your changes** with clear commit messages
6. **Push your branch** to your fork
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a pull request** to the main repository

### Branching Strategy

- `master`: Main development branch, should always be deployable
- `feature/*`: Feature branches for new features or enhancements
- `bugfix/*`: Bug fix branches
- `release/*`: Release preparation branches
- `hotfix/*`: Urgent fixes for production issues

## Coding Standards

Adhering to consistent coding standards helps maintain code quality and readability.

### Backend (Python)

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use [Black](https://black.readthedocs.io/) formatter
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Add type hints to function signatures
- Document functions and classes with docstrings (Google style)
- Maximum line length: 88 characters (Black default)
- Use snake_case for variables and function names
- Use CamelCase for class names

Run automated formatting:
```bash
cd backend
black .
isort .
```

### Frontend (JavaScript/React)

- Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use [Prettier](https://prettier.io/) for formatting
- Use [ESLint](https://eslint.org/) for linting
- Use functional components with hooks
- Use camelCase for variables and function names
- Use PascalCase for component names
- Organize imports logically
- Document complex logic with comments

Run automated formatting:
```bash
cd frontend
npm run format
npm run lint
```

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

Example:
```
feat(query): add cross-encoder reranking to improve search results

Implements cross-encoder reranking using sentence-transformers to improve
search precision. Results are reranked after initial vector retrieval.

Closes #123
```

## Testing Guidelines

All contributions should include appropriate tests.

### Test Requirements

- **New features**: Must include unit and integration tests
- **Bug fixes**: Must include regression tests
- **Performance improvements**: Must include benchmark tests
- **All tests**: Must pass before a PR will be accepted

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Test Coverage

We aim for high test coverage. Use coverage tools to ensure your code is well-tested:

```bash
# Backend coverage
cd backend
pytest --cov=api tests/

# Frontend coverage
cd frontend
npm test -- --coverage
```

## Documentation Guidelines

Good documentation is critical for project maintainability:

### Code Documentation

- Document all public functions, classes, and modules
- Explain complex algorithms with comments
- Include examples for non-trivial functions
- Update existing documentation when changing functionality

### User Documentation

When adding or changing user-facing features:
1. Update relevant user guides in `docs/user_guide/`
2. Add screenshots for UI changes
3. Update examples to reflect new functionality

### API Documentation

When modifying API endpoints:
1. Update OpenAPI/Swagger documentation
2. Update `docs/api_reference/`
3. Include example requests and responses

### Developer Documentation

When changing architectural components:
1. Update `docs/developer_guide/`
2. Update diagrams as needed
3. Document design decisions and trade-offs

## Pull Request Process

1. **Create a draft PR** early to get feedback
2. **Fill out the PR template** completely
3. **Ensure all tests pass** on your local machine
4. **Request reviews** from appropriate team members
5. **Address all review comments**
6. **Mark PR as ready for review** when complete
7. **Wait for approval** before merging

### PR Checklist

Before submitting your PR, ensure:
- [ ] Code follows the style guidelines
- [ ] Tests have been added or updated
- [ ] Documentation has been updated
- [ ] Changes generate no new warnings
- [ ] All tests pass locally and in CI
- [ ] PR description clearly describes the changes

## Issue Reporting

When reporting issues:

1. **Check existing issues** to avoid duplicates
2. **Use the issue template** to provide all necessary information
3. **Include steps to reproduce** the issue
4. **Provide relevant logs** and screenshots
5. **Specify your environment** (OS, browser, versions)
6. **Add appropriate labels** to categorize the issue

## Security Vulnerability Reporting

For security vulnerabilities:

1. **Do NOT report security vulnerabilities through public GitHub issues**
2. **Email security@your-lab-domain.com** with details
3. **Provide steps to reproduce** the vulnerability
4. **Allow time for assessment** before public disclosure
5. **Include your PGP key** for secure communication if possible

## Project Governance

### Decision Making

Technical decisions are made by consensus among core contributors, with the lab administrator having final say when consensus cannot be reached.

### Core Contributors

Core contributors are responsible for:
- Reviewing pull requests
- Triaging issues
- Mentoring new contributors
- Maintaining code quality
- Planning roadmap

To become a core contributor:
1. Make sustained, quality contributions to the project
2. Demonstrate understanding of the codebase and architecture
3. Show good judgment in code reviews
4. Be recommended by existing core contributors

### Release Process

1. **Version bump** following [Semantic Versioning](https://semver.org/)
2. **Update CHANGELOG.md** with all significant changes
3. **Create a release branch** from master
4. **Run final automated tests** to verify release
5. **Create a GitHub release** with detailed notes
6. **Deploy to production** following the deployment guide

### Project Communication

- **GitHub Issues**: Primary location for task tracking
- **Pull Requests**: Focused technical discussions
- **Lab Slack**: Day-to-day communication
- **Monthly Meetings**: Roadmap planning and review

## Thank You!

Your contributions help make the RNA Lab Navigator better for the entire lab. We appreciate your time and effort in contributing to this project!