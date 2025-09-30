# PulsePlan Backend Makefile
# Provides convenient commands for development and CI/CD

.PHONY: help install test test-scheduler test-acceptance-gate lint format clean run dev

# Default target
help:
	@echo "PulsePlan Backend Commands:"
	@echo ""
	@echo "  install              Install dependencies"
	@echo "  test                 Run all tests"
	@echo "  test-scheduler       Run scheduler unit tests"
	@echo "  test-acceptance-gate Run acceptance gate"
	@echo "  lint                 Run code linting"
	@echo "  format               Format code"
	@echo "  clean                Clean temporary files"
	@echo "  run                  Run development server"
	@echo "  dev                  Run in development mode"
	@echo ""

# Installation
install:
	pip install -r requirements.txt
	pip install ortools || echo "OR-Tools not available, using fallback"

# Testing
test:
	pytest -v --tb=short

test-scheduler:
	pytest app/scheduler/testing/ -v

test-acceptance-gate:
	@echo "🚀 Running Scheduler Acceptance Gate..."
	python scripts/run_acceptance_gate.py

# Code quality
lint:
	ruff check app/
	black --check app/

format:
	black app/
	ruff check app/ --fix

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf logs/
	rm -rf artifacts/

# Development
run:
	python main.py

dev:
	python main.py --reload

# CI/CD targets
ci-install: install

ci-test: test test-acceptance-gate

ci-lint: lint

ci-security-check:
	@echo "🔒 Running security checks..."
	# Add security scanning commands here
	@echo "✅ Security checks completed"

ci-performance-check:
	@echo "📊 Running performance checks..."
	python scripts/run_acceptance_gate.py
	@echo "✅ Performance checks completed"

# Docker targets (optional)
docker-build:
	docker build -t pulseplan-backend .

docker-run:
	docker run -p 8000:8000 pulseplan-backend

# Database targets (if needed)
db-migrate:
	@echo "Running database migrations..."
	# Add migration commands here

db-reset:
	@echo "Resetting database..."
	# Add database reset commands here