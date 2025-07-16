# Makefile for Data Anonymizer project - Comprehensive Testing & Development

# Variables
PYTHON := python
PIP := pip
FLAKE8 := flake8
BLACK := black
MYPY := mypy
BANDIT := bandit

# Directories
SRC_DIR := src
FRONTEND_DIR := frontend
BACKEND_DIR := backend
DOCS_DIR := docs

.PHONY: help install install-dev dev backend frontend samples lint format type-check security-check pre-commit build run-backend run-frontend run-dev docker-build docker-run docker-stop docs docs-serve profile setup-env clean

help:
	@echo "Available commands:"
	@echo "  install          - Install dependencies"
	@echo "  install-dev      - Install development dependencies"
	@echo "  dev              - Run both backend and frontend in development mode"
	@echo "  backend          - Run only the backend server"
	@echo "  frontend         - Run only the frontend server"
	@echo "  samples          - Generate sample data files"
	@echo "  lint             - Run linting checks"
	@echo "  format           - Format code with black and isort"
	@echo "  type-check       - Run type checking with mypy"
	@echo "  security-check   - Run security checks with bandit"
	@echo "  pre-commit       - Run all pre-commit checks"
	@echo "  build            - Build the application"
	@echo "  run-backend      - Run the backend server"
	@echo "  run-frontend     - Run the frontend server"
	@echo "  run-dev          - Run development servers"
	@echo "  docker-build     - Build Docker image"
	@echo "  docker-run       - Run with Docker Compose"
	@echo "  docker-stop      - Stop Docker containers"
	@echo "  docs             - Generate documentation"
	@echo "  docs-serve       - Serve documentation"
	@echo "  profile          - Run performance profiling"
	@echo "  setup-env        - Set up development environment"
	@echo "  clean            - Clean up generated files"

# Installation targets
install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

dev:
	python scripts/dev.py dev

backend:
	python scripts/dev.py backend

frontend:
	python scripts/dev.py frontend

samples:
	python scripts/dev.py samples

# Code quality targets
format:
	$(BLACK) $(SRC_DIR) scripts/
	isort $(SRC_DIR) scripts/

lint:
	$(FLAKE8) $(SRC_DIR) --max-line-length=88 --extend-ignore=E203,W503
	$(MYPY) $(SRC_DIR) --ignore-missing-imports

type-check:
	$(MYPY) $(SRC_DIR) --ignore-missing-imports

security-check:
	$(BANDIT) -r $(SRC_DIR) $(BACKEND_DIR) -f json -o security-report.json
	$(BANDIT) -r $(SRC_DIR) $(BACKEND_DIR)

# Pre-commit checks
pre-commit: format lint type-check security-check

# Build targets
build:
	$(PYTHON) setup.py sdist bdist_wheel

run-backend:
	cd $(BACKEND_DIR) && $(PYTHON) -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	cd $(FRONTEND_DIR) && streamlit run app.py --server.port 8501

run-dev:
	# Run backend and frontend concurrently
	cd $(BACKEND_DIR) && $(PYTHON) -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
	cd $(FRONTEND_DIR) && streamlit run app.py --server.port 8501 &
	wait

# Docker targets
docker-build:
	docker build -t data-anonymizer .

docker-run:
	docker-compose up --build

docker-stop:
	docker-compose down

# Documentation targets
docs:
	cd $(DOCS_DIR) && $(PYTHON) -m sphinx -b html . _build/html

docs-serve:
	cd $(DOCS_DIR)/_build/html && $(PYTHON) -m http.server 8080

# Performance targets
profile:
	$(PYTHON) -m cProfile -o profile.stats $(SRC_DIR)/data_anonymizer/core/anonymizer.py
	$(PYTHON) -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"

# Development environment setup
setup-env:
	$(PYTHON) -m venv .venv
	.venv\Scripts\pip install --upgrade pip
	.venv\Scripts\pip install -r requirements.txt
	.venv\Scripts\pip install -e .

# Enhanced clean target
clean:
	if exist __pycache__ rmdir /s /q __pycache__
	if exist build rmdir /s /q build
	if exist dist rmdir /s /q dist
	if exist *.egg-info rmdir /s /q *.egg-info
	if exist .mypy_cache rmdir /s /q .mypy_cache
	if exist security-report.json del security-report.json
	if exist profile.stats del profile.stats
	for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
	for /r . %%f in (*.pyc) do @if exist "%%f" del "%%f"
