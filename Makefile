.PHONY: help install test lint typecheck format clean

# Default target
help:
	@echo "jre-addr-parse - US Address Parser"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install the package locally"
	@echo "  make install-dev  Install with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test         Run tests"
	@echo "  make lint         Run ruff linter"
	@echo "  make typecheck    Run mypy type checker"
	@echo "  make format       Format code with ruff"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        Remove build artifacts"

# Install the package
install:
	pip install .

# Install with dev dependencies
install-dev:
	uv sync

# Run tests
test:
	uv run pytest

# Run linter
lint:
	uv run ruff check src/

# Run type checker
typecheck:
	uv run mypy src/

# Format code
format:
	uv run ruff format src/

# Clean up
clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
