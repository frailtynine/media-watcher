.PHONY: help install install-frontend dev dev-backend dev-frontend stop migrate test clean

# Colors for help output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RESET := \033[0m

# Default target
help: ## Show this help message
	@echo "$(GREEN)AI News Bot - Local Development Commands$(RESET)"
	@echo "=============================================="
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "$(BLUE)%-20s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# Installation Commands
install: ## Install backend dependencies using poetry
	@echo "$(GREEN)Installing backend dependencies...$(RESET)"
	poetry install

install-frontend: ## Install frontend dependencies
	@echo "$(GREEN)Installing frontend dependencies...$(RESET)"
	cd ai_news_frontend && npm install

install-all: install install-frontend ## Install all dependencies (backend + frontend)

# Development Commandsstop
dev: ## Start both backend and frontend in development mode
	@echo "$(GREEN)Starting full development environment...$(RESET)"
	@echo "$(YELLOW)Backend will be available at: http://localhost:8050$(RESET)"
	@echo "$(YELLOW)Frontend will be available at: http://localhost:3000$(RESET)"
	@echo "$(YELLOW)API docs will be available at: http://localhost:8050/api/docs$(RESET)"
	@make -j2 dev-backend dev-frontend

dev-backend: ## Start only the backend server
	@echo "$(GREEN)Starting backend server...$(RESET)"
	poetry run python -m ai_news_bot

dev-frontend: ## Start only the frontend development server
	@echo "$(GREEN)Starting frontend development server...$(RESET)"
	cd ai_news_frontend && npm run dev

# Database Commands
migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(RESET)"
	poetry run alembic upgrade head

migrate-generate: ## Generate new migration
	@echo "$(GREEN)Generating new migration...$(RESET)"
	poetry run alembic revision --autogenerate

# Testing Commands
test: ## Run tests
	@echo "$(GREEN)Running tests...$(RESET)"
	poetry run pytest -vv .

test-coverage: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	poetry run pytest -vv . --cov=ai_news_bot --cov-report=html

# Code Quality Commands
lint: ## Run linting
	@echo "$(GREEN)Running linting...$(RESET)"
	poetry run ruff check .
	poetry run mypy ai_news_bot

format: ## Format code
	@echo "$(GREEN)Formatting code...$(RESET)"
	poetry run black ai_news_bot tests
	poetry run ruff check --fix .

# Setup Commands
setup: install-all migrate ## Complete setup for new development environment
	@echo "$(GREEN)Development environment setup complete!$(RESET)"
	@echo "$(BLUE)Next steps:$(RESET)"
	@echo "  1. Create a .env file with your configuration (see README.md)"
	@echo "  2. Run 'make dev' to start both backend and frontend"
	@echo "  3. Visit http://localhost:3000 for the frontend"
	@echo "  4. Visit http://localhost:8050/api/docs for API documentation"

# Utility Commands
clean: ## Clean up generated files
	@echo "$(YELLOW)Cleaning up...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage 2>/dev/null || true

stop: ## Stop any running processes (useful if started with make dev)
	@echo "$(YELLOW)Stopping processes...$(RESET)"
	@pkill -f "python -m ai_news_bot" 2>/dev/null || true
	@pkill -f "vite" 2>/dev/null || true
	@echo "$(GREEN)Processes stopped$(RESET)"

# Quick start
start: dev ## Alias for dev command
quick-start: setup dev ## Complete setup and start development servers