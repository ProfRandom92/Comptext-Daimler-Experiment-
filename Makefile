.PHONY: help install test lint format clean dev prod docker debug benchmark security-check audit

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)CompText Daimler Buses - Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	pip install -r requirements.txt
	pip install -e .
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-dev: ## Install dev dependencies (testing, linting)
	@echo "$(BLUE)Installing dev dependencies...$(NC)"
	pip install -r requirements.txt
	pip install pytest pytest-cov mypy ruff black httpx
	@echo "$(GREEN)✓ Dev dependencies installed$(NC)"

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v --tb=short
	@echo "$(GREEN)✓ Tests passed$(NC)"

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated: htmlcov/index.html$(NC)"

test-fast: ## Run tests without coverage (faster)
	@echo "$(BLUE)Running fast tests...$(NC)"
	pytest tests/ -q --tb=line

test-unit: ## Run only unit tests (no integration)
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest tests/ -v -k "not integration" --tb=short

lint: ## Run Ruff linter
	@echo "$(BLUE)Linting with Ruff...$(NC)"
	ruff check . --extend-exclude=venv
	@echo "$(GREEN)✓ Linting passed$(NC)"

lint-fix: ## Auto-fix linting issues with Ruff
	@echo "$(BLUE)Auto-fixing linting issues...$(NC)"
	ruff check . --fix --extend-exclude=venv
	@echo "$(GREEN)✓ Linting issues fixed$(NC)"

format: ## Format code with Black
	@echo "$(BLUE)Formatting code...$(NC)"
	black . --exclude=venv
	@echo "$(GREEN)✓ Code formatted$(NC)"

mypy: ## Type-check with mypy
	@echo "$(BLUE)Type-checking with mypy...$(NC)"
	mypy src/ --strict --ignore-missing-imports
	@echo "$(GREEN)✓ Type-check passed$(NC)"

clean: ## Remove build artifacts and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info htmlcov .coverage .mypy_cache .pytest_cache
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

dev: ## Run in development mode (Mock LLM, debug logging)
	@echo "$(BLUE)Starting development server...$(NC)"
	LLM_BACKEND=mock LOG_LEVEL=DEBUG streamlit run dashboard.py

dev-api: ## Run FastAPI dev server (auto-reload)
	@echo "$(BLUE)Starting API development server...$(NC)"
	LLM_BACKEND=mock LOG_LEVEL=DEBUG uvicorn api:app --reload --port 8000

dev-ollama: ## Run with Ollama Gemma 2B (requires: ollama pull gemma2:2b)
	@echo "$(BLUE)Starting with Ollama Gemma 2B...$(NC)"
	ollama pull gemma2:2b > /dev/null 2>&1 || echo "$(YELLOW)Warning: Ollama not installed or gemma2:2b not pulled$(NC)"
	LLM_BACKEND=ollama_gemma OLLAMA_URL=http://localhost:11434 streamlit run dashboard.py

dev-claude: ## Run with Claude Haiku (requires: ANTHROPIC_API_KEY)
	@echo "$(BLUE)Starting with Claude Haiku...$(NC)"
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "$(RED)Error: ANTHROPIC_API_KEY not set$(NC)"; \
		exit 1; \
	fi
	LLM_BACKEND=anthropic streamlit run dashboard.py

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t comptext-daimler:latest .
	@echo "$(GREEN)✓ Image built$(NC)"

docker-up: ## Start services with Docker Compose (dashboard + api + ollama)
	@echo "$(BLUE)Starting Docker Compose stack...$(NC)"
	docker-compose up
	@echo "$(GREEN)✓ Services running at http://localhost:8501 (Dashboard) & http://localhost:8000 (API)$(NC)"

docker-down: ## Stop Docker Compose services
	@echo "$(BLUE)Stopping Docker Compose services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

docker-logs: ## Show Docker Compose logs
	@echo "$(BLUE)Showing logs...$(NC)"
	docker-compose logs -f

debug: ## Run with full debug logging
	@echo "$(BLUE)Starting with DEBUG logging...$(NC)"
	LOG_FORMAT=json LOG_LEVEL=DEBUG CACHE_DEBUG=true KVTC_DEBUG=true streamlit run dashboard.py

benchmark: ## Run performance benchmark
	@echo "$(BLUE)Running benchmark...$(NC)"
	python -c "from src.core.kvtc import IndustrialKVTCStrategy; \
	strategy = IndustrialKVTCStrategy(); \
	import time; \
	test_doc = 'P0300 Zündaussetzer' * 100; \
	t0 = time.perf_counter(); \
	result = strategy.compress(test_doc); \
	elapsed = (time.perf_counter() - t0) * 1000; \
	print(f'Benchmark: {elapsed:.2f}ms | Compression: {result.compression_ratio:.1%}')"

security-check: ## Run security checks (bandit, safety)
	@echo "$(BLUE)Running security checks...$(NC)"
	pip install bandit safety -q
	bandit -r src/ -ll || true
	safety check || true
	@echo "$(YELLOW)Review output above for security issues$(NC)"

audit: ## Full audit: lint + type-check + test
	@echo "$(BLUE)Running full audit...$(NC)"
	@echo "$(BLUE)→ Linting...$(NC)"
	@ruff check . --extend-exclude=venv || exit 1
	@echo "$(GREEN)  ✓ Linting passed$(NC)"
	@echo "$(BLUE)→ Type-checking...$(NC)"
	@mypy src/ --ignore-missing-imports || exit 1
	@echo "$(GREEN)  ✓ Type-check passed$(NC)"
	@echo "$(BLUE)→ Testing...$(NC)"
	@pytest tests/ -q || exit 1
	@echo "$(GREEN)  ✓ Tests passed$(NC)"
	@echo "$(GREEN)✓ Full audit passed!$(NC)"

run-batch-test: ## Test batch analysis endpoint
	@echo "$(BLUE)Starting API server...$(NC)"
	@python -m uvicorn api:app &
	@sleep 2
	@echo "$(BLUE)Running batch test...$(NC)"
	@curl -X POST http://localhost:8000/batch/analyze \
		-H "Content-Type: application/json" \
		-d '{"documents": [{"text": "P0300 Zündaussetzer", "quelle": "OBD"}, {"text": "Wartungsprotokoll km 80000", "quelle": "SAP"}, {"text": "Sperrung Bremsanlage", "quelle": "QA"}]}' | python -m json.tool
	@echo ""
	@echo "$(GREEN)✓ Batch test complete$(NC)"
	@pkill -f "uvicorn api:app" || true

logs-json: ## Show logs in JSON format (structured)
	@echo "$(BLUE)Setting LOG_FORMAT=json...$(NC)"
	LOG_FORMAT=json streamlit run dashboard.py

cache-stats: ## Show cache statistics
	@echo "$(BLUE)Showing cache stats...$(NC)"
	python -c "from src.core.result_cache import AnalysisResultCache; \
	cache = AnalysisResultCache(max_size=256); \
	print('Cache Stats:'); \
	print(f'  Max Size: {cache.max_size}'); \
	print(f'  Current Size: {len(cache.cache)}'); \
	print(f'  Hits: {cache.hits}'); \
	print(f'  Misses: {cache.misses}'); \
	print(f'  Hit Rate: {cache.hit_rate:.1%}')"

obd-list: ## List all OBD codes in database
	@echo "$(BLUE)OBD Error Code Database (70+ Codes)...$(NC)"
	python -c "from src.core.obd_database import OBD_DATABASE; \
	print(f'Total Codes: {len(OBD_DATABASE)}'); \
	print(''); \
	from src.models.schemas import ProcessPriority; \
	for prio in [ProcessPriority.P1_KRITISCH, ProcessPriority.P2_DRINGEND, ProcessPriority.P3_ROUTINE]: \
		codes = [code for code, info in OBD_DATABASE.items() if info.schweregrad == prio]; \
		print(f'{prio.value}: {len(codes)} codes'); \
		for code in sorted(codes)[:5]: \
			print(f'  {code}')"

version: ## Show project version
	@echo "$(BLUE)CompText Daimler Buses$(NC)"
	@grep "version" pyproject.toml | head -1

.DEFAULT_GOAL := help
