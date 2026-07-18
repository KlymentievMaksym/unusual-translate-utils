# ==========================================
# Configuration variables
# ==========================================
.DEFAULT_GOAL := help

# Pattern: Controlled State Injection.
ifneq (,$(wildcard .env))
    include .env
    # Extract valid POSIX variable names ignoring comments and whitespaces.
    export $(shell awk -F= '/^[a-zA-Z_][a-zA-Z0-9_]*/ {print $$1}' .env)
endif

SRC_DIR := src/
COV_MODULE := src/translate_utils
ARGS ?= 
TARGET_DIRS := $(SRC_DIR) tests/

# Fallback strategy with Defensive Programming
SYSTEM_PYTHON := $(shell command -v python3 2> /dev/null || command -v python)
ifeq ($(SYSTEM_PYTHON),)
    $(error "ERROR: Python is not installed or not in PATH. Please install Python to proceed.")
endif

# Pattern: Toolchain Detection Strategy
HAS_UV := $(shell command -v uv 2> /dev/null)

# ==========================================
# Context-Aware Strategy for Environments
# ==========================================
ifdef CI
    RUFF_FORMAT := --output-format=github
    BIN := 
    PYTHON := python
    ENV_REQ := 
    INSTALL_CMD := python -m pip install
else
    RUFF_FORMAT :=
    VENV := .venv
    VENV_MARKER := $(VENV)/.installed
    
    # --- CROSS-PLATFORM FIX ---
    # Windows creates 'Scripts/', Unix creates 'bin/'
    ifeq ($(OS),Windows_NT)
        BIN := $(VENV)/Scripts/
    else
        BIN := $(VENV)/bin/
    endif
    # --------------------------
    
    PYTHON := $(BIN)python
    ENV_REQ := $(VENV_MARKER)

    ifdef HAS_UV
        VENV_CMD := uv venv $(VENV) --python $(SYSTEM_PYTHON)
        INSTALL_CMD := uv pip install --python $(PYTHON)
    else
        VENV_CMD := $(SYSTEM_PYTHON) -m venv $(VENV) && $(PYTHON) -m pip install --upgrade pip
        INSTALL_CMD := $(PYTHON) -m pip install
    endif
endif

# ==========================================
# Self-Documenting Help Menu
# ==========================================
.PHONY: help
help: ## Show this help message
	@echo "Usage: make [target] [ARGS=\"...\"]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ==========================================
# Project Lifecycle & Virtual Environment
# ==========================================
ifndef CI

$(VENV):
	@echo "Creating virtual environment..."
	@$(VENV_CMD)

$(VENV_MARKER): pyproject.toml | $(VENV)
	@echo "Dependencies changed or missing. Installing..."
	@$(INSTALL_CMD) -e ".[dev]"
	@touch $(VENV_MARKER)

endif

.PHONY: setup
setup: $(ENV_REQ) ## Bootstrap the project (create venv and install dependencies)
ifndef CI
	@echo "=========================================="
	@echo "Setup complete! Environment is up-to-date."
ifdef HAS_UV
	@echo "Pro-tip: 'uv' was used for blazing-fast environment lifecycle."
endif
	@echo "To activate it in your shell, run:"
	@echo "source $(VENV)/bin/activate"
	@echo "=========================================="
else
	@echo "CI environment is already managed by the pipeline."
endif

# ==========================================
# Validation Commands (Read-only, used by CI and local check-all)
# ==========================================
.PHONY: lint
lint: $(ENV_REQ) ## Run Ruff linter (Read-only)
	$(BIN)ruff check $(RUFF_FORMAT) $(TARGET_DIRS) $(ARGS)

.PHONY: check-format
check-format: $(ENV_REQ) ## Check code formatting using Ruff (Read-only)
	$(BIN)ruff format --check $(TARGET_DIRS) $(ARGS)

.PHONY: typecheck
typecheck: $(ENV_REQ) ## Run Mypy static type checker
	$(BIN)mypy --install-types --non-interactive $(TARGET_DIRS) $(ARGS)

# FIX: SSOT Principle. pytest now relies completely on pyproject.toml for paths.
.PHONY: test
test: $(ENV_REQ) ## Run standard pytest suite (Supports ARGS)
	$(BIN)pytest $(ARGS)

.PHONY: test-cov
test-cov: $(ENV_REQ) ## Run tests with coverage report (Supports ARGS)
	$(BIN)pytest --cov=$(COV_MODULE) --cov-report=term-missing --cov-report=xml $(ARGS)

# ==========================================
# Facade Meta-Targets
# ==========================================
.PHONY: check-all
check-all: ## Run the entire CI validation pipeline locally
	@$(MAKE) check-format
	@$(MAKE) lint
	@$(MAKE) typecheck
	@$(MAKE) test
	@echo "All checks passed! You are ready to push."

# ==========================================
# Mutator Commands (Used locally by developers)
# ==========================================
.PHONY: format
format: $(ENV_REQ) ## Auto-fix linting issues and format code
	$(BIN)ruff check --fix $(TARGET_DIRS) $(ARGS)
	$(BIN)ruff format $(TARGET_DIRS) $(ARGS)

# ==========================================
# Cleanup
# ==========================================
.PHONY: clean
clean: ## Remove cache, build, and test artifacts
	-rm -rf .ruff_cache/ .mypy_cache/ .pytest_cache/ coverage.xml .coverage htmlcov/
	-find $(TARGET_DIRS) -type d -name "__pycache__" -exec rm -rf {} +
	-find . -maxdepth 1 -type d -name "__pycache__" -exec rm -rf {} +
	-find . -maxdepth 1 -type d -name "*.egg-info" -exec rm -rf {} +

.PHONY: distclean
distclean: clean ## Remove all artifacts and the virtual environment
ifndef CI
	-rm -rf $(VENV)
	@echo "Environment destroyed. If you are currently in an active venv shell, type 'deactivate'."
endif