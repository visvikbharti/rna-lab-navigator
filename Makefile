.PHONY: help dev setup-infra setup-backend setup-frontend run-backend run-frontend run-celery-worker run-celery-beat clean lint test prod-build prod-up prod-logs prod-down deploy

PYTHON := python
PIP := pip
MANAGE_PY := backend/manage.py
DOCKER_COMPOSE := docker-compose
NPM := npm

help:
	@echo "RNA Lab Navigator commands:"
	@echo ""
	@echo "Development commands:"
	@echo "make dev                - Set up and run the complete development environment"
	@echo "make setup-infra        - Start Docker containers (Postgres, Redis, Weaviate)"
	@echo "make setup-backend      - Set up Python virtual environment and install dependencies"
	@echo "make setup-frontend     - Install frontend dependencies"
	@echo "make run-backend        - Run Django development server"
	@echo "make run-frontend       - Run frontend development server"
	@echo "make run-celery-worker  - Run Celery worker"
	@echo "make run-celery-beat    - Run Celery beat scheduler"
	@echo "make lint               - Run linting checks on the codebase"
	@echo "make test               - Run all tests"
	@echo "make clean              - Remove temporary files and caches"
	@echo ""
	@echo "Production commands:"
	@echo "make prod-build         - Build production Docker images"
	@echo "make prod-up            - Start production Docker services"
	@echo "make prod-logs          - View production Docker logs"
	@echo "make prod-down          - Stop production Docker services"
	@echo "make deploy             - Run tests, lint checks, build and deploy"

dev: setup-infra setup-backend setup-frontend run-backend run-celery-worker run-celery-beat run-frontend

setup-infra:
	@echo "Starting Docker containers..."
	$(DOCKER_COMPOSE) up -d

setup-backend:
	@echo "Setting up Python virtual environment and dependencies..."
	cd backend && \
	if [ ! -d "venv" ]; then $(PYTHON) -m venv venv; fi && \
	. venv/bin/activate && \
	$(PIP) install -r requirements.txt && \
	if [ ! -f ".env" ]; then cp .env.example .env; fi && \
	$(PYTHON) $(MANAGE_PY) migrate

setup-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && $(NPM) install

run-backend:
	@echo "Starting Django development server..."
	cd backend && . venv/bin/activate && $(PYTHON) $(MANAGE_PY) runserver

run-frontend:
	@echo "Starting frontend development server..."
	cd frontend && $(NPM) run dev

run-celery-worker:
	@echo "Starting Celery worker..."
	cd backend && . venv/bin/activate && celery -A rna_backend worker -l info

run-celery-beat:
	@echo "Starting Celery beat scheduler..."
	cd backend && . venv/bin/activate && celery -A rna_backend beat -l info

lint:
	@echo "Running linters..."
	cd backend && . venv/bin/activate && black . && isort .
	cd frontend && $(NPM) run lint && $(NPM) run format

test:
	@echo "Running tests..."
	cd backend && . venv/bin/activate && $(PYTHON) $(MANAGE_PY) test
	cd frontend && $(NPM) test

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Production commands
prod-build:
	@echo "Building production images..."
	cd frontend && $(NPM) run build
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml build

prod-up:
	@echo "Starting production services..."
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d

prod-logs:
	@echo "Viewing production logs..."
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml logs -f

prod-down:
	@echo "Stopping production services..."
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml down

deploy: test lint prod-build prod-up
	@echo "Deployment complete. View logs with 'make prod-logs'"