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
	@echo "Docker:"
	@echo "  make docker-build   Build libpostal-enabled image"
	@echo "  make docker-shell   Shell into the image"
	@echo "  make docker-test    Run a sample parse inside the image"
	@echo "  make docker-run-api Run the optional API server"
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

# Docker targets (libpostal-enabled image)
DOCKER_IMAGE ?= ghcr.io/abstract-data/ryandata-addr-utils-libpostal
DOCKER_TAG ?= latest
DOCKER_REF ?= main

docker-build:
	docker build --build-arg RYANDATA_ADDR_UTILS_REF=$(DOCKER_REF) -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-shell:
	docker run --rm -it $(DOCKER_IMAGE):$(DOCKER_TAG) bash

docker-test:
	docker run --rm $(DOCKER_IMAGE):$(DOCKER_TAG) \
		python -c "from ryandata_address_utils import parse; print(parse('123 Main St, Austin TX 78749').to_dict())"

docker-run-api:
	docker run --rm -it -p 8000:8000 $(DOCKER_IMAGE):$(DOCKER_TAG) \
		python -m ryandata_address_utils.api

# Clean up
clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
