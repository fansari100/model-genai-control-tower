# ─────────────────────────────────────────────────────────────
# Control Tower – Makefile
# ─────────────────────────────────────────────────────────────
.PHONY: help dev up down build migrate seed test lint eval redteam garak-scan aibom cert-pack

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Infrastructure ───────────────────────────────────────────
up: ## Start all services (Postgres, MinIO, Redpanda, Temporal, OPA, Keycloak, OTEL, Phoenix, Grafana)
	docker compose -f infra/docker-compose.yml up -d

down: ## Stop all services
	docker compose -f infra/docker-compose.yml down

build: ## Build all Docker images
	docker compose -f infra/docker-compose.yml build

logs: ## Tail all service logs
	docker compose -f infra/docker-compose.yml logs -f

# ── Backend ──────────────────────────────────────────────────
backend-dev: ## Run backend in dev mode
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-test: ## Run backend tests
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing

backend-lint: ## Lint backend
	cd backend && ruff check app/ && ruff format --check app/ && mypy app/

migrate: ## Run Alembic migrations
	cd backend && alembic upgrade head

migrate-gen: ## Auto-generate a new migration
	cd backend && alembic revision --autogenerate -m "$(msg)"

seed: ## Seed database with sample data
	cd backend && python -m scripts.seed_data

# ── Frontend ─────────────────────────────────────────────────
frontend-dev: ## Run frontend in dev mode
	cd frontend && npm run dev

frontend-build: ## Build frontend
	cd frontend && npm run build

frontend-lint: ## Lint frontend
	cd frontend && npm run lint

# ── Evaluation & Red Teaming ────────────────────────────────
eval: ## Run promptfoo evaluation suite
	cd eval/promptfoo && npx promptfoo@latest eval

eval-view: ## Open promptfoo eval viewer
	cd eval/promptfoo && npx promptfoo@latest view

redteam: ## Run promptfoo red team suite
	cd eval/promptfoo && npx promptfoo@latest redteam run

pyrit: ## Run PyRIT security scenarios
	cd eval/pyrit && python -m pytest scenarios/ -v

garak-scan: ## Run garak LLM vulnerability scan
	garak --model_type openai --model_name gpt-4o --probes all --report_prefix ct_scan

# ── AIBOM & Evidence ────────────────────────────────────────
aibom: ## Generate AI Bill of Materials
	cd backend && python -m scripts.generate_aibom

cert-pack: ## Generate certification evidence pack
	cd backend && python -m scripts.generate_cert_pack

# ── Full Dev Environment ────────────────────────────────────
dev: up ## Start everything for development
	@echo "⏳ Waiting for services..."
	@sleep 5
	@echo "🔄 Running migrations..."
	$(MAKE) migrate
	@echo "🌱 Seeding data..."
	$(MAKE) seed
	@echo "✅ Control Tower ready!"
	@echo "   Backend:  http://localhost:8000"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Phoenix:  http://localhost:6006"
	@echo "   Grafana:  http://localhost:3002"
	@echo "   Keycloak: http://localhost:8080"

clean: down ## Clean everything
	docker volume prune -f
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
